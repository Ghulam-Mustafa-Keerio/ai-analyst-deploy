import asyncio, io, pandas as pd, httpx, json

from backend.main import app


async def main():
    df = pd.DataFrame({
        "age": [21, 35, 42, 29, 51, 33, 44, 26, 39, 48, 31, 57],
        "income": [40, 66, 81, 52, 94, 63, 85, 47, 71, 90, 59, 102],
        "segment": ["a", "b", "b", "a", "c", "b", "c", "a", "b", "c", "a", "c"],
        "converted": [0, 1, 1, 0, 1, 0, 1, 0, 1, 1, 0, 1],
    })
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as c:
        up = await c.post("/upload", files={"file": ("smoke.csv", buf.getvalue())})
        did = up.json()["dataset"]["dataset_id"]
        st = await c.post("/agent/start", json={"dataset_id": did, "mode": "autonomous", "target": "converted"})
        jid = st.json()["job_id"]
        for _ in range(400):
            s = await c.get(f"/agent/jobs/{jid}")
            b = s.json()
            if b["status"] in ("completed", "failed"):
                break
            await asyncio.sleep(0.5)
        print("STATUS:", b["status"])
        for e in b["events"]:
            if e["agent"] in ("ModelDebateAgent", "InsightGenerationAgent"):
                print(e["agent"], "->", json.dumps(e["payload"])[:400])
        adv = await c.post("/chat", json={"job_id": jid, "message": "Which feature matters most?"})
        print("ADVISOR:", adv.json()["answer"][:200])


asyncio.run(main())
