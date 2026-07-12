# Deployment Guide

This project is split into two deployable surfaces:

- **Backend** → Vercel (FastAPI, serverless Python)
- **Frontend** → Streamlit Community Cloud

## Backend (Vercel) — DONE ✅

Live URL: **https://ai-analyst-five.vercel.app**

### What changed for serverless
Vercel serverless functions do **not** support WebSockets, long-running
background tasks, or persistent in-memory state. The backend was adapted:

- `backend/agents/runtime.py` gained `run_sync()` which executes the full
  agent pipeline **inline** and returns the completed job status + event
  history in a single request.
- `backend/api/agent.py` adds a combined `POST /agent/run` endpoint that
  uploads a dataset **and** runs the pipeline in one call (required because
  uploaded files and in-memory state do not persist across Vercel invocations).
  In serverless mode (`VERCEL` env set) `POST /agent/start` also runs inline.
- Uploads go to `/tmp/data/uploads` (the only writable path on Vercel).
- `vercel.json` uses the modern `functions` config with `maxDuration: 60` and
  an `excludeFiles` glob to keep the bundle under the 500 MB limit.
- `pyproject.toml` declares `tool.vercel.entrypoint = "backend.main:app"` and
  no longer lists `streamlit`/`websockets` (frontend-only deps).

### Redeploy
```powershell
vercel deploy --prod
```

### Notes / limitations
- The agent pipeline must finish within the 60s function timeout. Large
  datasets may exceed this; for those use a long-running host (Railway/Render).
- State is per-invocation. Each `/agent/run` is self-contained.
- The WebSocket live-stream route (`/ws/status/{job_id}`) is still present for
  local/dev use but is not reachable on Vercel; the frontend falls back to REST
  polling automatically when "Serverless backend" is enabled.

## Frontend (Streamlit Community Cloud)

The Streamlit app is **env-configurable**:

- `API_BASE_URL` — backend base URL (default `http://127.0.0.1:8000`)
- `WS_BASE_URL` — WebSocket base URL (default `ws://127.0.0.1:8000`)
- `SERVERLESS_BACKEND` — set to `true` to use the single-request `/agent/run`
  flow instead of the upload-then-start + WebSocket flow.

### Deploy steps
1. Push this repo to GitHub (the Vercel project already exists; create a new
   GitHub repo for the frontend, or reuse the same one).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **New app** → select this repo.
   - **Main file path:** `ui/app.py`
   - **Python requirements:** `requirements-streamlit.txt` (set in Advanced
     settings, or rename to `requirements.txt` at repo root).
4. In **Advanced settings → Secrets**, add:
   ```toml
   API_BASE_URL = "https://ai-analyst-five.vercel.app"
   WS_BASE_URL = "wss://ai-analyst-five.vercel.app"
   SERVERLESS_BACKEND = "true"
   ```
5. Deploy. In the app sidebar, ensure **"Serverless backend"** is checked so it
   uses the `/agent/run` endpoint.

### Local dev
```powershell
# Terminal 1 — backend
$env:VERCEL=""  # unset; runs with WebSocket + background tasks
uvicorn backend.main:app --host 127.0.0.1 --port 8000
# Terminal 2 — frontend
streamlit run ui/app.py --server.address 127.0.0.1 --server.port 8501
```
