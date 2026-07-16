import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent


def _load_env_file(path: Path) -> None:
    """Minimal .env loader (stdlib only) so local secrets work without python-dotenv.

    The local .env file is authoritative: it overrides any placeholder env var
    already exported in the shell (e.g. GEMINI_API_KEY=your_...). On serverless
    deployments .env does not exist, so real platform env vars are used instead.
    """
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        os.environ[key] = value


_load_env_file(ROOT / ".env")

from backend.llm.provider import LLMProvider, get_llm, llm_available

__all__ = ["LLMProvider", "get_llm", "llm_available"]
