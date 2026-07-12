from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.ws.event_stream import event_stream


router = APIRouter(tags=["websocket"])


@router.websocket("/ws/status/{job_id}")
async def status_websocket(websocket: WebSocket, job_id: str) -> None:
    client = await event_stream.connect(job_id, websocket)
    try:
        while True:
            event = await client.queue.get()
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    finally:
        await event_stream.disconnect(job_id, client)
