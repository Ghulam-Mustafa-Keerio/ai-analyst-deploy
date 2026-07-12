from __future__ import annotations

import asyncio
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from fastapi import WebSocket

Event = dict[str, Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_event(
    event_type: str,
    *,
    job_id: str,
    message: str,
    agent: str | None = None,
    status: str = "running",
    payload: dict[str, Any] | None = None,
) -> Event:
    return {
        "id": str(uuid4()),
        "type": event_type,
        "job_id": job_id,
        "agent": agent,
        "message": message,
        "status": status,
        "payload": payload or {},
        "timestamp": utc_now(),
    }


@dataclass
class Client:
    websocket: WebSocket
    queue: asyncio.Queue[Event]
    client_id: str = field(default_factory=lambda: str(uuid4()))


class EventStream:
    def __init__(self, replay_limit: int = 250) -> None:
        self._clients: dict[str, dict[str, Client]] = defaultdict(dict)
        self._history: dict[str, deque[Event]] = defaultdict(lambda: deque(maxlen=replay_limit))
        self._lock = asyncio.Lock()

    async def publish(self, event: Event) -> None:
        job_id = event["job_id"]
        async with self._lock:
            self._history[job_id].append(event)
            clients = list(self._clients[job_id].values())
        for client in clients:
            await client.queue.put(event)

    async def connect(self, job_id: str, websocket: WebSocket) -> Client:
        await websocket.accept()
        client = Client(websocket=websocket, queue=asyncio.Queue(maxsize=500))
        async with self._lock:
            self._clients[job_id][client.client_id] = client
            history = list(self._history[job_id])
        for event in history:
            await client.queue.put(event)
        return client

    async def disconnect(self, job_id: str, client: Client) -> None:
        async with self._lock:
            self._clients[job_id].pop(client.client_id, None)

    def history(self, job_id: str) -> list[Event]:
        return list(self._history[job_id])


event_stream = EventStream()
