from __future__ import annotations

import asyncio
import io
import os
from enum import Enum
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pandas as pd

# ---------------------------------------------------------------------------
# Data source abstraction
# ---------------------------------------------------------------------------
# The original system only accepted an uploaded CSV/Parquet file. This module
# extends the runtime with several first-class data sources so the agent OS can
# ingest data from a SQL database, a remote URL, or a built-in sample dataset.
# Every source is normalised to a local Parquet file so the rest of the
# pipeline (profiling, training, evaluation) is unchanged.
# ---------------------------------------------------------------------------

CACHE_DIR = Path("/tmp/data/sources") if os.environ.get("VERCEL") else Path("data/uploads/sources")


class DataSourceType(str, Enum):
    upload = "upload"
    sql = "sql"
    url = "url"
    sample = "sample"
    json = "json"
    excel = "excel"
    sheets = "sheets"
    rest = "rest"
    mongo = "mongo"


# A small catalogue of synthetic sample datasets so the product is usable with
# zero external data. Each entry is a factory returning a DataFrame.
_SAMPLE_FACTORIES: dict[str, str] = {
    "titanic": "Binary classification: survival from passenger attributes.",
    "iris": "Multiclass classification: flower species from measurements.",
    "housing": "Regression: house price from size, rooms, location.",
    "credit": "Binary classification: loan default risk.",
    "sales": "Regression: daily revenue from marketing spend.",
}


def available_samples() -> list[dict[str, str]]:
    return [{"key": key, "description": desc} for key, desc in _SAMPLE_FACTORIES.items()]


def _sample_dataframe(key: str) -> pd.DataFrame:
    """Return a synthetic sample DataFrame for the given key."""
    import numpy as np

    rng = np.random.default_rng(42)
    if key == "iris":
        n = 150
        species = rng.choice(["setosa", "versicolor", "virginica"], n)
        return pd.DataFrame(
            {
                "sepal_length": rng.normal(5.8, 0.8, n),
                "sepal_width": rng.normal(3.0, 0.4, n),
                "petal_length": rng.normal(3.8, 1.2, n),
                "petal_width": rng.normal(1.2, 0.6, n),
                "species": species,
            }
        )
    if key == "housing":
        n = 400
        size = rng.integers(40, 300, n)
        rooms = rng.integers(1, 8, n)
        age = rng.integers(0, 60, n)
        location = rng.choice(["urban", "suburb", "rural"], n)
        price = size * 1200 + rooms * 8000 - age * 500 + (location == "urban") * 40000 + rng.normal(0, 8000, n)
        return pd.DataFrame(
            {"size_sqm": size, "rooms": rooms, "age_years": age, "location": location, "price": price.round(0)}
        )
    if key == "credit":
        n = 600
        income = rng.normal(55000, 20000, n)
        debt = rng.normal(20000, 9000, n)
        age = rng.integers(18, 75, n)
        default = ((income - debt) < 30000).astype(int) | (rng.random(n) < 0.15)
        return pd.DataFrame(
            {"income": income.round(0), "debt": debt.round(0), "age": age, "default": default.astype(int)}
        )
    if key == "sales":
        n = 365
        spend = rng.normal(5000, 1500, n)
        season = np.sin(np.arange(n) / 30.0)
        revenue = spend * 3.2 + season * 4000 + rng.normal(0, 2000, n)
        return pd.DataFrame({"day": np.arange(n), "marketing_spend": spend.round(0), "revenue": revenue.round(0)})
    # titanic (default)
    n = 500
    pclass = rng.choice([1, 2, 3], n, p=[0.24, 0.21, 0.55])
    sex = rng.choice(["male", "female"], n)
    age = rng.integers(1, 80, n)
    fare = rng.normal(30, 20, n) + pclass * 10
    survived = ((sex == "female") | (pclass == 1) | (rng.random(n) < 0.2)).astype(int)
    return pd.DataFrame(
        {"pclass": pclass, "sex": sex, "age": age, "fare": fare.round(2), "survived": survived}
    )


async def connect_sql(source_url: str, *, query: str | None = None, table: str | None = None) -> dict[str, Any]:
    """Validate a SQL connection and return available tables (or a preview)."""
    from sqlalchemy import create_engine, inspect, text

    def _connect() -> dict[str, Any]:
        engine = create_engine(source_url)
        with engine.connect() as conn:
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            if query:
                preview = pd.read_sql(text(query), conn).head(50)
            elif table:
                preview = pd.read_sql(text(f"SELECT * FROM {table} LIMIT 50"), conn)
            else:
                preview = pd.DataFrame()
        engine.dispose()
        return {
            "tables": tables,
            "preview_columns": list(preview.columns),
            "preview_rows": preview.to_dict(orient="records"),
        }

    return await asyncio.to_thread(_connect)


async def resolve_dataset(
    *,
    source_type: DataSourceType,
    filename: str | None = None,
    content: bytes | None = None,
    source_url: str | None = None,
    query: str | None = None,
    table: str | None = None,
    sample_key: str | None = None,
    data_key: str | None = None,
) -> Path:
    """Normalise any supported source to a local Parquet file and return its path."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    if source_type == DataSourceType.upload:
        if content is None or filename is None:
            raise ValueError("Upload source requires filename and content.")
        suffix = Path(filename).suffix.lower()
        if suffix not in {".csv", ".parquet"}:
            raise ValueError("Only CSV and Parquet uploads are supported.")
        if suffix == ".parquet":
            path = CACHE_DIR / f"{os.urandom(8).hex()}.parquet"
            await asyncio.to_thread(path.write_bytes, content)
            return path
        df = await asyncio.to_thread(pd.read_csv, io.BytesIO(content))
        path = CACHE_DIR / f"{os.urandom(8).hex()}.parquet"
        await asyncio.to_thread(df.to_parquet, path)
        return path

    if source_type == DataSourceType.url:
        if not source_url:
            raise ValueError("URL source requires source_url.")
        # Accept both remote URLs and local file paths for consistency.
        if source_url.startswith(("http://", "https://")):
            parsed = urlparse(source_url)
            suffix = Path(parsed.path).suffix.lower() or ".csv"
            async with __import__("httpx").AsyncClient(timeout=60, follow_redirects=True) as client:
                resp = await client.get(source_url)
                resp.raise_for_status()
                raw = resp.content
            if suffix == ".parquet":
                path = CACHE_DIR / f"{os.urandom(8).hex()}.parquet"
                await asyncio.to_thread(path.write_bytes, raw)
                return path
            df = await asyncio.to_thread(pd.read_csv, io.BytesIO(raw))
        else:
            suffix = Path(source_url).suffix.lower() or ".csv"
            if suffix == ".parquet":
                path = CACHE_DIR / f"{os.urandom(8).hex()}.parquet"
                await asyncio.to_thread(path.write_bytes, Path(source_url).read_bytes())
                return path
            df = await asyncio.to_thread(pd.read_csv, source_url)
        path = CACHE_DIR / f"{os.urandom(8).hex()}.parquet"
        await asyncio.to_thread(df.to_parquet, path)
        return path

    if source_type == DataSourceType.sql:
        if not source_url:
            raise ValueError("SQL source requires source_url.")
        from sqlalchemy import create_engine, text

        def _extract() -> Path:
            engine = create_engine(source_url)
            sql = query or f"SELECT * FROM {table}" if table else None
            if not sql:
                raise ValueError("SQL source requires a table or query.")
            df = pd.read_sql(text(sql), engine)
            out = CACHE_DIR / f"{os.urandom(8).hex()}.parquet"
            df.to_parquet(out)
            engine.dispose()
            return out

        return await asyncio.to_thread(_extract)

    if source_type == DataSourceType.sample:
        if not sample_key:
            raise ValueError("Sample source requires sample_key.")
        df = await asyncio.to_thread(_sample_dataframe, sample_key)
        path = CACHE_DIR / f"{os.urandom(8).hex()}.parquet"
        await asyncio.to_thread(df.to_parquet, path)
        return path

    if source_type == DataSourceType.json:
        if not source_url:
            raise ValueError("JSON source requires source_url (a file path or http(s) URL).")
        df = await asyncio.to_thread(_read_json, source_url)
        path = CACHE_DIR / f"{os.urandom(8).hex()}.parquet"
        await asyncio.to_thread(df.to_parquet, path)
        return path

    if source_type == DataSourceType.excel:
        if not source_url:
            raise ValueError("Excel source requires source_url (a file path or http(s) URL).")
        sheet = table or 0
        df = await asyncio.to_thread(_read_excel, source_url, sheet)
        path = CACHE_DIR / f"{os.urandom(8).hex()}.parquet"
        await asyncio.to_thread(df.to_parquet, path)
        return path

    if source_type == DataSourceType.sheets:
        if not source_url:
            raise ValueError("Google Sheets source requires source_url (published CSV link or sheet URL).")
        df = await asyncio.to_thread(_read_sheets, source_url)
        path = CACHE_DIR / f"{os.urandom(8).hex()}.parquet"
        await asyncio.to_thread(df.to_parquet, path)
        return path

    if source_type == DataSourceType.rest:
        if not source_url:
            raise ValueError("REST source requires source_url (JSON endpoint returning an array/object).")
        df = await asyncio.to_thread(_read_rest, source_url, data_key or query or "data")
        path = CACHE_DIR / f"{os.urandom(8).hex()}.parquet"
        await asyncio.to_thread(df.to_parquet, path)
        return path

    if source_type == DataSourceType.mongo:
        if not source_url:
            raise ValueError("MongoDB source requires source_url (mongodb:// connection string).")
        df = await asyncio.to_thread(_read_mongo, source_url, table or query or "")
        path = CACHE_DIR / f"{os.urandom(8).hex()}.parquet"
        await asyncio.to_thread(df.to_parquet, path)
        return path

    raise ValueError(f"Unsupported source type: {source_type}")


# ---------------------------------------------------------------------------
# New source readers
# ---------------------------------------------------------------------------

def _read_json(source_url: str) -> pd.DataFrame:
    """Read a JSON file or URL into a DataFrame (records or split orient)."""
    if source_url.startswith(("http://", "https://")):
        import httpx

        raw = httpx.get(source_url, timeout=60, follow_redirects=True).json()
    else:
        raw = pd.read_json(source_url)
        return raw if isinstance(raw, pd.DataFrame) else pd.DataFrame(raw)
    if isinstance(raw, list):
        return pd.DataFrame(raw)
    if isinstance(raw, dict):
        # Common API shapes: {"data": [...]}, {"rows": [...]}, {"results": [...]}
        for key in ("data", "rows", "results", "items"):
            if key in raw and isinstance(raw[key], list):
                return pd.DataFrame(raw[key])
        return pd.DataFrame([raw])
    return pd.DataFrame(raw)


def _read_excel(source_url: str, sheet) -> pd.DataFrame:
    """Read an XLSX/XLS file or URL into a DataFrame.

    A sheet name given as a numeric string (e.g. ``"0"``) is coerced to an int
    so it is interpreted as a positional sheet index rather than a literal name.
    """
    if isinstance(sheet, str) and sheet.isdigit():
        sheet = int(sheet)
    if source_url.startswith(("http://", "https://")):
        import httpx

        content = httpx.get(source_url, timeout=60, follow_redirects=True).content
        return pd.read_excel(io.BytesIO(content), sheet_name=sheet)
    return pd.read_excel(source_url, sheet_name=sheet)


def _read_sheets(source_url: str) -> pd.DataFrame:
    """Read a Google Sheet via its published CSV link.

    Accepts either the "Publish to web" CSV link or a standard Sheets edit URL
    (converted to the export CSV endpoint automatically).
    """
    url = source_url
    if "docs.google.com/spreadsheets" in url and "/pub?output=csv" not in url and "/export" not in url:
        sheet_id = url.split("/d/")[1].split("/")[0]
        gid = "0"
        if "gid=" in url:
            gid = url.split("gid=")[1].split("&")[0]
        url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    import httpx

    content = httpx.get(url, timeout=60, follow_redirects=True).content
    return pd.read_csv(io.BytesIO(content))


def _read_rest(source_url: str, data_key: str) -> pd.DataFrame:
    """Fetch a REST JSON endpoint (or local file) and flatten into a DataFrame."""
    if source_url.startswith(("http://", "https://")):
        import httpx

        payload = httpx.get(source_url, timeout=60, follow_redirects=True).json()
    else:
        payload = pd.read_json(source_url)
    if isinstance(payload, dict) and data_key in payload:
        payload = payload[data_key]
    if isinstance(payload, list):
        return pd.json_normalize(payload)
    if isinstance(payload, dict):
        return pd.json_normalize([payload])
    return pd.DataFrame(payload)


def _read_mongo(source_url: str, collection: str) -> pd.DataFrame:
    """Read a MongoDB collection into a DataFrame.

    Requires ``pymongo``. The ``collection`` argument is the collection name;
    if omitted the first collection in the database is used.
    """
    try:
        from pymongo import MongoClient
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise ValueError(
            "MongoDB support requires `pymongo`. Install it with `pip install pymongo`."
        ) from exc
    if not collection:
        raise ValueError("MongoDB source requires a collection name (table field).")
    client = MongoClient(source_url, serverSelectionTimeoutMS=10000)
    db = client.get_default_database()
    cursor = db[collection].find()
    records = list(cursor)
    client.close()
    for rec in records:
        rec.pop("_id", None)
    return pd.json_normalize(records)
