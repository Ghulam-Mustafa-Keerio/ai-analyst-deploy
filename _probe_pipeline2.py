import sys, io, asyncio, json
sys.path.insert(0, ".")

import pandas as pd
import httpx
from backend.main import app

# Exercise the 3D UI component functions with mock data (no streamlit runtime needed
# beyond import; they guard plotly import and return early on empty input).
from ui.components.plot_3d import (
    sources_3d, schema_3d, metrics_3d, feature_importance_3d,
    scatter_3d, pipeline_3d, experiments_3d,
)

def check(name, fn):
    try:
        fn()
        print(f"[OK] {name}")
    except Exception as e:
        print(f"[FAIL] {name}: {type(e).__name__}: {e}")

check("sources_3d", lambda: sources_3d([{"key": "upload", "description": "x"}]))
check("schema_3d", lambda: schema_3d({"a": "int64", "b": "object"}, {"a": 0.1, "b": 0.5}))
check("metrics_3d", lambda: metrics_3d({"accuracy": 0.9, "f1": 0.8, "loss": 0.2}))
check("feature_importance_3d", lambda: feature_importance_3d({"x": 0.5, "y": 0.3, "z": 0.1}))
check("scatter_3d", lambda: scatter_3d([{"x": 0, "y": 0, "z": 0, "label": "1"}]))
check("pipeline_3d", lambda: pipeline_3d([{"name": "A", "status": "completed"}]))
check("experiments_3d", lambda: experiments_3d([{"job_id": "1", "accuracy": 0.9, "f1": 0.8, "train_time": 1.0}]))

async def pipeline():
    df = pd.DataFrame({
        "age": [21, 35, 42, 29, 51, 33, 44, 26, 39, 48, 31, 57],
        "income": [40, 66, 81, 52, 94, 63, 85, 47, 71, 90, 59, 102],
        "segment": ["a", "b", "b", "a", "c", "b", "c", "a", "b", "c", "a", "c"],
        "converted": [0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1],
    })
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        up = await client.post("/upload", files={"file": ("smoke.csv", buf.getvalue())})
        assert up.status_code == 200, up.status_code
        did = up.json()["dataset"]["dataset_id"]
        st = await client.post("/agent/start", json={"dataset_id": did, "mode": "autonomous", "target": "converted"})
        assert st.status_code == 200, st.status_code
        jid = st.json()["job_id"]
        for _ in range(180):
            r = await client.get(f"/agent/jobs/{jid}")
            b = r.json()
            if b["status"] in ("completed", "failed"):
                emb = await client.get(f"/data/datasets/{did}/embed-3d")
                print("[OK] pipeline status:", b["status"], "| embed pts:", len(emb.json().get("points", [])))
                if b["status"] == "failed":
                    for e in b["events"]:
                        if e.get("status") == "failed":
                            print("  FAIL EVENT:", e)
                return
            await asyncio.sleep(0.5)
    print("[FAIL] pipeline did not finish")

asyncio.run(pipeline())
