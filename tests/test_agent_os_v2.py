from __future__ import annotations

import asyncio
import io
import sys
from pathlib import Path

import httpx
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.main import app
from backend.ws.event_stream import make_event


async def _run_pipeline_smoke() -> dict:
    df = pd.DataFrame(
        {
            "age": [21, 35, 42, 29, 51, 33, 44, 26, 39, 48, 31, 57],
            "income": [40, 66, 81, 52, 94, 63, 85, 47, 71, 90, 59, 102],
            "segment": ["a", "b", "b", "a", "c", "b", "c", "a", "b", "c", "a", "c"],
            "converted": [0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1],
        }
    )
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        upload = await client.post("/upload", files={"file": ("smoke.csv", buffer.getvalue())})
        assert upload.status_code == 200
        dataset_id = upload.json()["dataset"]["dataset_id"]

        start = await client.post(
            "/agent/start",
            json={"dataset_id": dataset_id, "mode": "autonomous", "target": "converted"},
        )
        assert start.status_code == 200
        job_id = start.json()["job_id"]

        for _ in range(180):
            status = await client.get(f"/agent/jobs/{job_id}")
            body = status.json()
            if body["status"] in {"completed", "failed"}:
                return body
            await asyncio.sleep(0.5)

    raise AssertionError("Agent pipeline did not finish in time.")


def test_agent_pipeline_emits_structured_events() -> None:
    result = asyncio.run(_run_pipeline_smoke())

    assert result["status"] == "completed"
    assert any(event["type"] == "agent_step" for event in result["events"])
    assert any(event["agent"] == "ModelSelectionAgent" for event in result["events"])
    assert result["events"][-1]["type"] == "job_status"
    assert result["events"][-1]["status"] == "completed"


def test_event_schema_contains_required_fields() -> None:
    event = make_event(
        "agent_step",
        job_id="job-1",
        agent="ModelSelectionAgent",
        message="Selecting random_forest due to mixed feature types.",
        status="running",
    )

    assert set(event) == {"id", "type", "job_id", "agent", "message", "status", "payload", "timestamp"}
    assert event["type"] == "agent_step"
    assert event["agent"] == "ModelSelectionAgent"
