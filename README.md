# Autonomous Data Science Agent OS v2

This project is a modular, real-time autonomous data science platform. It replaces the old monolithic dashboard with:

- FastAPI backend with async routes and WebSocket event streaming
- Multi-agent analysis and training runtime
- Streamlit frontend split into pages, components, services, and state
- Dataset memory, experiment tracking, and domain reference assets
- Domain detection from dataset schema, aligned to `skills/business_domains`

## Architecture

```text
backend/
  api/       upload, agent, chat, WebSocket routes
  agents/   planner, profiler, quality, feature, model, training, insight agents
  tools/    async data loading, ML training, evaluation
  memory/   dataset memory, experiment store, preferences
  ws/       structured event stream

ui/
  app.py
  pages/        dashboard, intelligence, advisor
  components/   cards, chat bubbles, feature selector
  services/     httpx API client and WebSocket client
  state/        cached session state helpers

skills/business_domains/
  domain references used to keep the platform aligned with real data science domains
```

## Event Schema

```json
{
  "id": "uuid",
  "type": "agent_step",
  "job_id": "uuid",
  "agent": "ModelSelectionAgent",
  "message": "Selected random_forest based on profile and autonomy mode.",
  "status": "completed",
  "payload": {
    "selected_model": "random_forest"
  },
  "timestamp": "2026-07-09T00:00:00+00:00"
}
```

## Run Locally

```powershell
pip install -r requirements-v2.txt
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
streamlit run ui/app.py --server.address 127.0.0.1 --server.port 8501
```

Open:

- API docs: http://127.0.0.1:8000/docs
- UI: http://127.0.0.1:8501

## Docker

```powershell
docker compose up --build
```

## Tests

```powershell
pytest
```

## Domain Alignment

Uploaded datasets are profiled for likely business domain using column names. The detected domain is emitted in the `DataProfilerAgent` event payload and available to downstream agents for domain-specific strategy, metrics, and explanations.

## Scope

The maintained v2 surface is `backend/`, `ui/`, `skills/business_domains/`, tests, and deployment/config files. Legacy Celery, old monolithic Streamlit, external skill dumps, generated reports, and unrelated package trees have been removed.
