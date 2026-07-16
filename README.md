# Autonomous Data Science Agent OS v2

A modular, real-time **hybrid** autonomous data-science platform. A deterministic
scikit-learn pipeline does the heavy lifting (profiling, training, evaluation),
while an **optional LLM layer** adds natural-language reasoning — model debate,
plain-language insights, and an experiment-aware advisor. The platform degrades
gracefully: with no LLM configured it still runs the full pipeline using
deterministic fallbacks, so it works on self-hosted and serverless deployments
alike.

Highlights:

- FastAPI backend with async routes and WebSocket event streaming
- Multi-agent analysis and training runtime (9 observable stages)
- **Hybrid LLM reasoning** (OpenAI-compatible or Gemini) with deterministic fallback
- **AutoML rigor**: model zoo, lightweight hyperparameter optimization, cross-validation stability, and target-leakage detection
- **Deployable artifacts**: trained pipelines are persisted and downloadable
- Streamlit frontend split into pages, components, services, and state
- Dataset memory, experiment tracking, and domain reference assets
- Domain detection from dataset schema across 30+ business domains

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

## Hybrid LLM Layer

The platform is *hybrid*: a deterministic ML pipeline plus an optional LLM for
reasoning. Configure one provider via environment variables (no code changes, no
new hard dependencies — uses `httpx`):

```powershell
# OpenAI-compatible (OpenAI, Azure, OpenRouter, Ollama, vLLM, Together, ...)
$env:OPENAI_API_KEY="sk-..."
$env:OPENAI_MODEL="gpt-4o-mini"          # optional
$env:OPENAI_BASE_URL="https://..."        # optional, for non-OpenAI gateways

# OR Google Gemini
$env:GEMINI_API_KEY="..."
$env:GEMINI_MODEL="gemini-1.5-flash"     # optional
```

When no key is set, the `ModelDebateAgent`, `InsightGenerationAgent`, and
Advisor fall back to deterministic, auditable behaviour — the pipeline never
crashes for lack of an LLM.

## AutoML Capabilities

- **Model zoo**: linear, random_forest, gradient_boosting, svm, knn (classification & regression)
- **Hyperparameter optimization**: lightweight `GridSearchCV` per model family
- **Cross-validation**: 5-fold stability reporting (`cv_mean` / `cv_std`)
- **Leakage detection**: flags columns that are likely target proxies (IDs, labels, outcome fields)
- **Model persistence**: trained `Pipeline` artifacts are saved and downloadable from the Intelligence tab

## Data Sources

Every source is normalised to a local Parquet file so the rest of the pipeline is
unchanged. Select a source from the Dashboard ingest panel:

| Source | Key | Notes |
| --- | --- | --- |
| Upload | `upload` | Local CSV / Parquet file |
| Sample | `sample` | Built-in synthetic datasets (titanic, iris, housing, credit, sales) |
| SQL | `sql` | Postgres / MySQL / SQLite via SQLAlchemy (`source_url` + table/query) |
| Remote URL | `url` | Remote CSV / Parquet over HTTP(S) |
| JSON | `json` | JSON file or endpoint (records / split orient) |
| Excel | `excel` | XLSX / XLS workbook sheet (`source_url` + sheet name/index) |
| Google Sheets | `sheets` | Published CSV link or Sheets edit URL |
| REST API | `rest` | JSON endpoint; optional `data_key` to locate the array |
| MongoDB | `mongo` | `mongodb://` connection string + collection name (requires `pymongo`) |

## 3D Visualisation

The Streamlit UI renders interactive Plotly 3D views (requires `plotly`):

- **3D data-source map** — every source as a node in a deterministic constellation
- **3D pipeline graph** — agent stages on a helix (Intelligence tab)
- **3D experiment space** — experiments placed by accuracy / F1 / train time
- **3D dataset embedding** — PCA projection grounding the Advisor (Advisor tab)
- **3D schema field** — columns on a grid; marker size encodes missing-ratio
- **3D metrics globe** — each metric a vertex; radius encodes normalised score
- **3D feature importance** — features on a helix; radius encodes importance

## Scope

The maintained v2 surface is `backend/`, `ui/`, `skills/business_domains/`, tests, and deployment/config files. Legacy Celery, old monolithic Streamlit, external skill dumps, generated reports, and unrelated package trees have been removed.
