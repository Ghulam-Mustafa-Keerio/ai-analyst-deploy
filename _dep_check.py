import sys
mods = ["fastapi","uvicorn","streamlit","pandas","numpy","sklearn","httpx","websockets","joblib","openpyxl","sqlalchemy","pymongo","multipart"]
ok = []
bad = []
for m in mods:
    try:
        __import__(m)
        ok.append(m)
    except Exception as e:
        bad.append(f"{m}: {e}")
with open("dep_check.txt","w") as f:
    f.write("OK: " + ", ".join(ok) + "\n")
    f.write("BAD: " + "; ".join(bad) + "\n")
    f.write("PY: " + sys.version + "\n")
