from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4


@dataclass
class DatasetRecord:
    dataset_id: str
    filename: str
    path: str
    rows: int
    columns: int
    schema: dict[str, str]


class DatasetMemory:
    def __init__(self) -> None:
        self._records: dict[str, DatasetRecord] = {}

    def register(self, *, filename: str, path: Path, rows: int, columns: int, schema: dict[str, str]) -> DatasetRecord:
        record = DatasetRecord(str(uuid4()), filename, str(path), rows, columns, schema)
        self._records[record.dataset_id] = record
        return record

    def get(self, dataset_id: str) -> DatasetRecord:
        return self._records[dataset_id]

    def list(self) -> list[dict[str, Any]]:
        return [asdict(record) for record in self._records.values()]


dataset_memory = DatasetMemory()
