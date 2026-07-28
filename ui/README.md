Streamlit UI — Usage Guide

This file explains how to run and use the Streamlit user interface for the Autonomous Data Science Agent OS v2.

Run the UI (after starting the backend):

```powershell
# Backend (terminal 1)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

# Frontend (terminal 2)
streamlit run ui/app.py --server.address 127.0.0.1 --server.port 8501
```

Access the UI at: http://127.0.0.1:8501

Dashboard quick-start

- Go to the **Dashboard** page.
- Choose a data source: `Upload`, `Sample`, or `SQL database`.
- For `Upload`, select a CSV, Parquet, JSON, or Excel file.
- The UI shows the uploaded filename and size. If the file exceeds the configured serverless upload cap, an error will be shown.

Serverless upload limit

- The frontend and backend respect the `SERVERLESS_MAX_UPLOAD_MB` environment variable.
- Default: `4` MB. To allow larger uploads on serverless platforms, increase this value and re-deploy both frontend and backend accordingly.

Domain-aware dashboard blueprint

- After upload or connection, the dataset is profiled and a detected `domain` is attached to the dataset profile.
- The UI surfaces a domain-based "dashboard blueprint" which includes suggested metrics, charts, and filters tailored to the domain and dataset columns.
- This blueprint is advisory — use it to quickly configure targets, features, and exploration panels.

Troubleshooting

- If uploads fail with a 413-style message, reduce the file size or self-host the backend (remove `VERCEL` or run on a VM/container).
- If the UI cannot reach the backend, confirm `API_BASE_URL` in the Streamlit sidebar or use environment variables to override defaults.

Contact

For questions or issues, open an issue in the repository or contact the project maintainer.
