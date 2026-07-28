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
    monkeypatch.setenv("SERVERLESS_MAX_UPLOAD_MB", "10")
    upload_module_reloaded = importlib.reload(upload_module)
    content = b"x" * (10 * 1024 * 1024 + 1)
    file = UploadFile(filename="RetailIQ_PowerBI.csv", file=io.BytesIO(content))

    async def invoke() -> None:
        await upload_module_reloaded.upload_dataset(file)

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(invoke())

    assert exc_info.value.status_code == 413
    detail = exc_info.value.detail
    assert "10 MB" in detail
    assert "smaller sample" in detail
    assert "self-host" in detail


def test_api_client_guard_raises_clear_message_for_large_uploads(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVERLESS_MAX_UPLOAD_MB", "10")
    api_client_reloaded = importlib.reload(api_client)
    content = b"x" * (10 * 1024 * 1024 + 1)

    with pytest.raises(ValueError) as exc_info:
        api_client_reloaded._guard_size("RetailIQ_PowerBI.csv", content)

    message = str(exc_info.value)
    assert "RetailIQ_PowerBI.csv" in message
    assert "10 MB" in message
    assert "self-host the backend" in message
