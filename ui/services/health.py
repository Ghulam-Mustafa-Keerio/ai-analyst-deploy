from __future__ import annotations

import httpx


async def health(api_base_url: str) -> dict:
    async with httpx.AsyncClient(base_url=api_base_url, timeout=10) as client:
        response = await client.get("/health")
        response.raise_for_status()
        return response.json()
