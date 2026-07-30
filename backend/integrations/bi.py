"""BI connector integrations.

Provides lightweight clients for:
* **Power BI** — REST API for datasets, tables, and push-data.
* **dbt** — invoke SQL transformations via ``dbt run`` (local) or
  ``dbt Cloud`` API (remote).

Both connectors degrade gracefully when credentials are absent.
"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from typing import Any

import httpx


# ======================================================================
# Power BI
# ======================================================================
@dataclass
class PowerBIConnector:
    """Minimal Power BI REST client using Azure AD service-principal auth."""

    tenant_id: str | None = None
    client_id: str | None = None
    client_secret: str | None = None
    workspace_id: str | None = None
    _token: str | None = None

    def __post_init__(self) -> None:
        self.tenant_id = self.tenant_id or os.environ.get("POWERBI_TENANT_ID")
        self.client_id = self.client_id or os.environ.get("POWERBI_CLIENT_ID")
        self.client_secret = self.client_secret or os.environ.get("POWERBI_CLIENT_SECRET")
        self.workspace_id = self.workspace_id or os.environ.get("POWERBI_WORKSPACE_ID")

    @property
    def configured(self) -> bool:
        return all([self.tenant_id, self.client_id, self.client_secret])

    async def _get_token(self) -> str:
        if self._token:
            return self._token
        if not self.configured:
            raise RuntimeError("Power BI connector not configured")
        url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "https://analysis.windows.net/powerbi/api/.default",
        }
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, data=data)
            resp.raise_for_status()
            self._token = resp.json()["access_token"]
        return self._token or ""

    async def list_datasets(self) -> list[dict[str, Any]]:
        token = await self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://api.powerbi.com/v1.0/myorg/datasets", headers=headers
            )
            resp.raise_for_status()
            return resp.json().get("value", [])

    async def push_rows(self, dataset_id: str, table_name: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        token = await self._get_token()
        headers = {"Authorization": f"Bearer {token}"}
        url = f"https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/tables/{table_name}/rows"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json={"rows": rows}, headers=headers)
            resp.raise_for_status()
            return resp.json() if resp.content else {"status": "ok"}


# ======================================================================
# dbt
# ======================================================================
@dataclass
class DbtConnector:
    """Run dbt transformations locally or via dbt Cloud."""

    project_dir: str | None = None
    cloud_token: str | None = None
    cloud_account_id: str | None = None
    cloud_job_id: str | None = None

    def __post_init__(self) -> None:
        self.project_dir = self.project_dir or os.environ.get("DBT_PROJECT_DIR")
        self.cloud_token = self.cloud_token or os.environ.get("DBT_CLOUD_TOKEN")
        self.cloud_account_id = self.cloud_account_id or os.environ.get("DBT_CLOUD_ACCOUNT_ID")
        self.cloud_job_id = self.cloud_job_id or os.environ.get("DBT_CLOUD_JOB_ID")

    @property
    def mode(self) -> str:
        if self.cloud_token and self.cloud_account_id:
            return "cloud"
        if self.project_dir:
            return "local"
        return "none"

    def run_local(self, *, select: str | None = None, full_refresh: bool = False) -> dict[str, Any]:
        if self.mode != "local":
            raise RuntimeError("dbt local mode not configured (set DBT_PROJECT_DIR)")
        cmd = ["dbt", "run"]
        if select:
            cmd.extend(["--select", select])
        if full_refresh:
            cmd.append("--full-refresh")
        result = subprocess.run(
            cmd, cwd=self.project_dir, capture_output=True, text=True, timeout=600
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout[-4000:],
            "stderr": result.stderr[-4000:],
        }

    async def trigger_cloud_run(self) -> dict[str, Any]:
        if self.mode != "cloud":
            raise RuntimeError("dbt Cloud not configured")
        url = f"https://cloud.getdbt.com/api/v2/accounts/{self.cloud_account_id}/jobs/{self.cloud_job_id}/run/"
        headers = {"Authorization": f"Token {self.cloud_token}", "Content-Type": "application/json"}
        payload = {"cause": "Triggered by AI-Analyst"}
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()


powerbi_connector = PowerBIConnector()
dbt_connector = DbtConnector()
