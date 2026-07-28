from __future__ import annotations

import os
from functools import wraps
from typing import Any, Callable, Coroutine

import httpx
import streamlit as st


def get_max_upload_mb() -> int:
    try:
        return max(1, int(os.environ.get("SERVERLESS_MAX_UPLOAD_MB", "4")))
    except ValueError:
        return 4


MAX_UPLOAD_MB = get_max_upload_mb()
MAX_UPLOAD_BYTES = MAX_UPLOAD_MB * 1024 * 1024


def _guard_size(filename: str, content: bytes) -> None:
    limit_mb = get_max_upload_mb()
    limit_bytes = limit_mb * 1024 * 1024
    if len(content) > limit_bytes:
        raise ValueError(
            f"`{filename}` is {len(content) / 1024 / 1024:.1f} MB, "
            f"but the serverless backend accepts files up to {limit_mb} MB. "
            "Use a smaller sample or self-host the backend."
        )


def async_cache_data(ttl: int = 30) -> Callable:
    def decorator(func: Callable[..., Coroutine[Any, Any, Any]]) -> Callable:
        cached = st.cache_data(ttl=ttl)(lambda *args, **kwargs: _run_async(func(*args, **kwargs)))

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return cached(*args, **kwargs)

        return wrapper

    return decorator


def _run_async(coro: Coroutine[Any, Any, Any]) -> Any:
    """Run a coroutine from Streamlit's synchronous script context.

    Streamlit 1.59+ executes scripts inside a running asyncio event loop,
    so both ``asyncio.run`` and ``loop.run_until_complete`` raise errors.
    We run the coroutine in a fresh loop on a background thread so it works
    regardless of whether a loop is already running.
    """
    import asyncio
    import concurrent.futures

    def _run_in_new_loop() -> Any:
        return asyncio.run(coro)

    try:
        asyncio.get_running_loop()
        # A loop is running — we cannot use asyncio.run() or run_until_complete()
        # on this thread. Spawn a worker thread with its own event loop.
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(_run_in_new_loop)
            return future.result()
    except RuntimeError:
        # No running loop — safe to use asyncio.run directly.
        return asyncio.run(coro)


async def health(api_base_url: str) -> dict[str, Any]:
    async with httpx.AsyncClient(base_url=api_base_url, timeout=10) as client:
        response = await client.get("/health")
        response.raise_for_status()
        return response.json()


async def upload_dataset(api_base_url: str, filename: str, content: bytes) -> dict[str, Any]:
    _guard_size(filename, content)
    async with httpx.AsyncClient(base_url=api_base_url, timeout=120) as client:
        files = {"file": (filename, content)}
        response = await client.post("/upload", files=files)
        response.raise_for_status()
        return response.json()


async def start_agent(
    api_base_url: str,
    *,
    dataset_id: str,
    mode: str,
    target: str | None,
    features: list[str],
    model: str | None,
) -> dict[str, Any]:
    payload = {"dataset_id": dataset_id, "mode": mode, "target": target, "features": features, "model": model}
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30) as client:
        response = await client.post("/agent/start", json=payload)
        response.raise_for_status()
        return response.json()


async def run_agent(
    api_base_url: str,
    *,
    filename: str,
    content: bytes,
    mode: str,
    target: str | None,
    features: list[str],
    model: str | None,
) -> dict[str, Any]:
    """Upload a dataset and run the agent pipeline in a single request.

    Used against serverless backends (e.g. Vercel) where files and in-memory
    state do not persist across separate invocations.
    """
    _guard_size(filename, content)
    data = {"mode": mode, "target": target or "", "features": ",".join(features), "model": model or ""}
    files = {"file": (filename, content)}
    async with httpx.AsyncClient(base_url=api_base_url, timeout=120) as client:
        response = await client.post("/agent/run", data=data, files=files)
        response.raise_for_status()
        return response.json()


@async_cache_data(ttl=15)
async def list_experiments(api_base_url: str) -> dict[str, Any]:
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30) as client:
        response = await client.get("/agent/experiments/compare")
        response.raise_for_status()
        return response.json()


@async_cache_data(ttl=30)
async def preview_dataset(api_base_url: str, dataset_id: str, page: int, page_size: int) -> dict[str, Any]:
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30) as client:
        response = await client.get(f"/agent/datasets/{dataset_id}/preview", params={"page": page, "page_size": page_size})
        response.raise_for_status()
        return response.json()


@async_cache_data(ttl=60)
async def get_domain_details(api_base_url: str, domain_name: str) -> dict[str, Any]:
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30) as client:
        response = await client.get(f"/agent/domains/{domain_name}")
        response.raise_for_status()
        return response.json()


async def get_job_status(api_base_url: str, job_id: str) -> dict[str, Any]:
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30) as client:
        response = await client.get(f"/agent/jobs/{job_id}")
        response.raise_for_status()
        return response.json()


async def chat(api_base_url: str, *, job_id: str | None, message: str) -> dict[str, Any]:
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30) as client:
        response = await client.post("/chat", json={"job_id": job_id, "message": message})
        response.raise_for_status()
        return response.json()


@async_cache_data(ttl=30)
async def list_samples(api_base_url: str) -> dict[str, Any]:
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30) as client:
        response = await client.get("/data/samples")
        response.raise_for_status()
        return response.json()


async def connect_source(
    api_base_url: str,
    *,
    source_type: str,
    filename: str | None = None,
    source_url: str | None = None,
    query: str | None = None,
    table: str | None = None,
    sample_key: str | None = None,
    data_key: str | None = None,
) -> dict[str, Any]:
    payload = {
        "source_type": source_type,
        "filename": filename,
        "source_url": source_url,
        "query": query,
        "table": table,
        "sample_key": sample_key,
        "data_key": data_key,
    }
    async with httpx.AsyncClient(base_url=api_base_url, timeout=120) as client:
        response = await client.post("/data/connect", json=payload)
        response.raise_for_status()
        return response.json()


async def preview_sql(api_base_url: str, *, source_url: str, query: str | None = None, table: str | None = None) -> dict[str, Any]:
    payload = {"source_type": "sql", "source_url": source_url, "query": query, "table": table}
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30) as client:
        response = await client.post("/data/sql/preview", json=payload)
        response.raise_for_status()
        return response.json()


@async_cache_data(ttl=60)
async def embed_3d(api_base_url: str, dataset_id: str) -> dict[str, Any]:
    async with httpx.AsyncClient(base_url=api_base_url, timeout=60) as client:
        response = await client.get(f"/data/datasets/{dataset_id}/embed-3d")
        response.raise_for_status()
        return response.json()


async def download_model(api_base_url: str, job_id: str) -> dict[str, Any]:
    async with httpx.AsyncClient(base_url=api_base_url, timeout=30) as client:
        response = await client.get(f"/agent/jobs/{job_id}/model")
        response.raise_for_status()
        # Stream the artifact to the browser via Streamlit's native download.
        import io

        return {"filename": job_id + ".joblib", "content": io.BytesIO(response.content)}


def run(coro: Coroutine[Any, Any, Any]) -> Any:
    import asyncio

    # Some helpers are wrapped with @st.cache_data (e.g. list_samples,
    # preview_dataset, embed_3d). Those return their resolved value directly
    # rather than a coroutine, so pass them through untouched; only genuine
    # coroutines are awaited.
    if not asyncio.iscoroutine(coro):
        return coro
    return _run_async(coro)
