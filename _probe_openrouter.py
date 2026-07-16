import asyncio, os, httpx, json

# Load .env the same way the app does (stdlib-only loader).
from pathlib import Path

ROOT = Path(__file__).resolve().parent
for raw in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
    line = raw.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, _, v = line.partition("=")
    os.environ[k.strip()] = v.strip().strip('"').strip("'")

url = "https://openrouter.ai/api/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {os.environ.get('OPENAI_API_KEY')}",
    "Content-Type": "application/json",
}
payload = {
    "model": "tencent/hy3:free",
    "messages": [{"role": "user", "content": "Say hi in 3 words"}],
    "temperature": 0.3,
    "max_tokens": 30,
}


async def go():
    async with httpx.AsyncClient(timeout=60) as c:
        r = await c.post(url, headers=headers, json=payload)
        print("HTTP", r.status_code)
        print(json.dumps(r.json(), indent=2)[:1000])


asyncio.run(go())
