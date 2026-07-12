# Autonomous Data Science Agent OS v2

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

## Run

```powershell
pip install -r requirements-v2.txt
uvicorn backend.main:app --reload
streamlit run ui/app.py
```

## Architecture

- `backend/api`: FastAPI upload, agent, chat, and WebSocket routes.
- `backend/agents`: observable multi-agent runtime and pipeline agents.
- `backend/tools`: async data loading, ML training, and evaluation helpers.
- `backend/memory`: in-memory dataset lineage, experiments, and preferences.
- `backend/ws`: job-scoped WebSocket event hub with replay history.
- `ui`: Streamlit shell split into pages, components, state, and services.
- `skills/business_domains`: maintained domain reference set used by the profiler domain detector.
