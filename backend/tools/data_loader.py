from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pandas as pd


async def read_dataset(path: str | Path, *, nrows: int | None = None) -> pd.DataFrame:
    file_path = Path(path)

    def _read() -> pd.DataFrame:
        if file_path.suffix.lower() == ".parquet":
            return pd.read_parquet(file_path)
        return pd.read_csv(file_path, nrows=nrows)

    return await asyncio.to_thread(_read)


async def profile_dataset(path: str | Path) -> dict[str, Any]:
    df = await read_dataset(path)
    missing = df.isna().mean().sort_values(ascending=False)
    numeric = df.select_dtypes(include="number")
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "schema": {column: str(dtype) for column, dtype in df.dtypes.items()},
        "missing_ratio": {column: float(value) for column, value in missing.items()},
        "numeric_summary": numeric.describe().fillna(0).to_dict() if not numeric.empty else {},
    }


async def preview_dataset(path: str | Path, *, page: int = 1, page_size: int = 100) -> dict[str, Any]:
    offset = max(page - 1, 0) * page_size
    file_path = Path(path)
    if file_path.suffix.lower() == ".parquet":
        df = await read_dataset(file_path)
        page_df = df.iloc[offset : offset + page_size]
    else:
        df = await read_dataset(file_path, nrows=offset + page_size)
        page_df = df.iloc[offset : offset + page_size]
    return {"page": page, "page_size": page_size, "rows": page_df.to_dict(orient="records")}
