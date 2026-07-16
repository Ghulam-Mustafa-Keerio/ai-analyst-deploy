"""Provider-agnostic LLM client with graceful degradation.

The platform is marketed as a *Hybrid* autonomous data-science agent: the
deterministic scikit-learn pipeline does the heavy lifting, while an optional
LLM layer adds natural-language reasoning (model debate, insights, advisor).

Design goals:
* No new hard dependencies — uses ``httpx`` (already required) for OpenAI-
  compatible endpoints and the Google Generative Language API for Gemini.
* Never crash the pipeline when no key/endpoint is configured. Callers receive
  ``None`` and fall back to deterministic behaviour.
* One config surface (env vars) so it works on self-hosted and serverless.

Supported providers (auto-detected from env):
* ``openai``   -> OPENAI_API_KEY (+ optional OPENAI_BASE_URL for Azure/OpenRouter)
* ``gemini``   -> GEMINI_API_KEY (Google AI Studio)
* ``openai``-compatible gateways (Ollama, vLLM, OpenRouter, Together, etc.)
"""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class LLMMessage:
    role: str
    content: str


def extract_json(text: str) -> Any | None:
    """Best-effort JSON extraction tolerant of reasoning-model noise.

    Reasoning models (e.g. tencent/hy3, DeepSeek-R1) often wrap JSON in markdown
    fences or prepend explanatory prose. We strip fences first, then fall back to
    locating the first balanced ``{...}`` or ``[...]`` block.
    """
    if not text:
        return None
    cleaned = text.strip()
    # Strip ```json ... ``` or ``` ... ``` fences.
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1]
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    # Find the first balanced brace/bracket block.
    for opener, closer in (("{", "}"), ("[", "]")):
        start = cleaned.find(opener)
        if start == -1:
            continue
        depth = 0
        for idx in range(start, len(cleaned)):
            if cleaned[idx] == opener:
                depth += 1
            elif cleaned[idx] == closer:
                depth -= 1
                if depth == 0:
                    candidate = cleaned[start : idx + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break
    return None


class LLMProvider:
    """Minimal chat-completions client that targets OpenAI-compatible APIs and Gemini."""

    def __init__(
        self,
        *,
        provider: str,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        if provider == "gemini":
            self.base_url = (base_url or "https://generativelanguage.googleapis.com/v1beta").rstrip("/")
        else:
            self.base_url = (base_url or "https://api.openai.com/v1").rstrip("/")

    # -- public API -------------------------------------------------------
    async def complete(
        self,
        prompt: str,
        *,
        system: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 600,
        retries: int = 3,
    ) -> str | None:
        """Return the assistant text, or ``None`` if the call cannot be made.

        Retries on transient failures (e.g. 429 rate-limits common on free-tier
        providers like OpenRouter ``tencent/hy3:free``) with a short backoff.
        After exhausting retries, returns ``None`` so callers fall back to
        deterministic behaviour — the pipeline never crashes for lack of an LLM.
        """
        messages = []
        if system:
            messages.append(LLMMessage(role="system", content=system))
        messages.append(LLMMessage(role="user", content=prompt))
        last_exc: Exception | None = None
        for attempt in range(retries):
            try:
                if self.provider == "gemini":
                    return await self._complete_gemini(messages, temperature, max_tokens)
                return await self._complete_openai(messages, temperature, max_tokens)
            except Exception as exc:  # noqa: BLE001 - graceful degradation
                last_exc = exc
                # Only retry on rate-limit / transient transport errors.
                if getattr(exc, "status_code", None) not in (429, 500, 502, 503, 504) and "429" not in str(exc):
                    break
                if attempt < retries - 1:
                    await asyncio.sleep(1.5 * (attempt + 1))
        # Graceful degradation: the deterministic pipeline continues.
        return None

    # -- transport --------------------------------------------------------
    async def _complete_openai(self, messages: list[LLMMessage], temperature: float, max_tokens: int) -> str | None:
        url = f"{self.base_url}/chat/completions"
        # OpenRouter expects these headers; harmless for other OpenAI-compatible gateways.
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/Ghulam-Mustafa-Keerio/AI-Analyst",
            "X-Title": "Autonomous Data Science Agent OS",
        }
        payload: dict[str, Any] = {
            "model": self.model or "gpt-4o-mini",
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
        message = data["choices"][0]["message"]
        # Reasoning models (e.g. tencent/hy3, DeepSeek-R1) may return the answer
        # in ``reasoning`` while ``content`` is null. Prefer content, fall back.
        content = message.get("content") or message.get("reasoning") or ""
        return content.strip() or None

    async def _complete_gemini(self, messages: list[LLMMessage], temperature: float, max_tokens: int) -> str | None:
        url = f"{self.base_url}/models/{self.model or 'gemini-1.5-flash'}:generateContent?key={self.api_key}"
        system_instruction = None
        turns = []
        for m in messages:
            if m.role == "system":
                system_instruction = {"parts": [{"text": m.content}]}
            else:
                turns.append({"role": "user" if m.role == "user" else "model", "parts": [{"text": m.content}]})
        payload: dict[str, Any] = {
            "contents": turns,
            "generationConfig": {"temperature": temperature, "maxOutputTokens": max_tokens},
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
        candidates = data.get("candidates") or []
        if not candidates:
            return None
        parts = candidates[0].get("content", {}).get("parts", [])
        return "".join(part.get("text", "") for part in parts).strip()


def _detect_provider() -> LLMProvider | None:
    openai_key = os.environ.get("OPENAI_API_KEY")
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if openai_key:
        return LLMProvider(
            provider="openai",
            api_key=openai_key,
            base_url=os.environ.get("OPENAI_BASE_URL"),
            model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        )
    if gemini_key:
        return LLMProvider(
            provider="gemini",
            api_key=gemini_key,
            model=os.environ.get("GEMINI_MODEL", "gemini-1.5-flash"),
        )
    return None


_PROVIDER: LLMProvider | None = None
_INITIALIZED = False


def get_llm() -> LLMProvider | None:
    """Return a configured provider, or ``None`` when no LLM is configured."""
    global _PROVIDER, _INITIALIZED
    if not _INITIALIZED:
        _PROVIDER = _detect_provider()
        _INITIALIZED = True
    return _PROVIDER


def llm_available() -> bool:
    return get_llm() is not None
