from __future__ import annotations

import asyncio
import json
import queue
import threading
from typing import Any

import websockets


class WebSocketEventClient:
    def __init__(self) -> None:
        self.events: queue.Queue[dict[str, Any]] = queue.Queue()
        self._thread: threading.Thread | None = None
        self._running_job: str | None = None

    def start(self, ws_base_url: str, job_id: str) -> None:
        if self._thread and self._thread.is_alive() and self._running_job == job_id:
            return
        self._running_job = job_id
        self._thread = threading.Thread(target=lambda: asyncio.run(self._listen(ws_base_url, job_id)), daemon=True)
        self._thread.start()

    async def _listen(self, ws_base_url: str, job_id: str) -> None:
        url = f"{ws_base_url.rstrip('/')}/ws/status/{job_id}"
        async with websockets.connect(url, ping_interval=20) as websocket:
            async for message in websocket:
                self.events.put(json.loads(message))

    def drain(self) -> list[dict[str, Any]]:
        drained: list[dict[str, Any]] = []
        while True:
            try:
                drained.append(self.events.get_nowait())
            except queue.Empty:
                return drained


event_client = WebSocketEventClient()
