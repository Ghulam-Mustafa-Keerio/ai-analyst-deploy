from __future__ import annotations

import asyncio
import importlib
import io
import os

import pytest
from fastapi import HTTPException, UploadFile

from backend.api import upload as upload_module
from ui.services import api_client


def test_upload_rejects_datasets_above_serverless_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    # Force a 10 MB limit so the 10 MB + 1 byte file is rejected.
    monkeypatch.setattr(upload_module, "get_max_upload_bytes", lambda: 10 * 1024 * 1024)
    content = b"x" * (10 * 1024 * 1024 + 1)
    file = UploadFile(filename="RetailIQ_PowerBI.csv", file=io.BytesIO(content))

    async def invoke() -> None:
        await upload_module.upload_dataset(file)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(invoke())

    assert exc_info.value.status_code == 413
    detail = exc_info.value.detail
    assert "10" in detail and "MB" in detail
    assert "upload_limit.json" in detail or "SERVERLESS_MAX_UPLOAD_MB" in detail


def test_api_client_guard_raises_clear_message_for_large_uploads(monkeypatch: pytest.MonkeyPatch) -> None:
    # Force a 10 MB limit so the 10 MB + 1 byte file is rejected.
    monkeypatch.setattr(api_client, "get_max_upload_mb", lambda: 10)
    content = b"x" * (10 * 1024 * 1024 + 1)

    with pytest.raises(ValueError) as exc_info:
        api_client._guard_size("RetailIQ_PowerBI.csv", content)

    message = str(exc_info.value)
    assert "RetailIQ_PowerBI.csv" in message
    assert "10 MB" in message
    assert "upload_limit.json" in message
