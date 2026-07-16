"""Harness to execute dashboard.render_dashboard() with a mocked Streamlit.

Surfaces real runtime/logic errors (KeyError, TypeError, etc.) that a plain
import won't catch. We only mock `streamlit` and `ui.services.api_client`;
everything else uses the real package so imports stay consistent.
"""
from __future__ import annotations

import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "ui" / "pages"))

# ---- Mock streamlit -------------------------------------------------------
class _State(dict):
    def __getattr__(self, k):
        try:
            return self[k]
        except KeyError:
            raise AttributeError(k)
    def __setattr__(self, k, v):
        self[k] = v

st = types.ModuleType("streamlit")
st.session_state = _State()
st.session_state.api_base_url = "http://127.0.0.1:8000"
st.session_state.ws_base_url = "ws://127.0.0.1:8000"
st.session_state.serverless = False
st.session_state.dataset = None
st.session_state.profile = None
st.session_state.job_id = None
st.session_state.events = []
st.session_state.last_experiments = []

_WIDGETS = {
    "Data source": "Upload",
    "Connection string": "",
    "Dataset URL": "",
    "JSON path or URL": "",
    "Excel path or URL": "",
    "Google Sheets link": "",
    "REST endpoint": "",
    "MongoDB connection string": "",
    "Collection name": "",
    "Sheet name or index": "0",
    "JSON data key (optional)": "",
    "Built-in sample": "iris",
    "Target column": "col0",
    "Model": "linear",
    "Autonomy": "autonomous",
}

def _radio(*a, **k):
    label = a[0] if a else k.get("label", "")
    return _WIDGETS.get(label, a[1] if len(a) > 1 else "")
def _selectbox(*a, **k):
    label = a[0] if a else k.get("label", "")
    opts = k.get("options", a[1] if len(a) > 1 else [])
    if opts:
        idx = k.get("index", 0)
        return opts[idx]
    return _WIDGETS.get(label, "")
def _text_input(*a, **k):
    return _WIDGETS.get(a[0] if a else k.get("label", ""), "")
def _text_area(*a, **k):
    return _WIDGETS.get(a[0] if a else k.get("label", ""), "")
def _file_uploader(*a, **k):
    return None
def _button(*a, **k):
    return False
def _segmented_control(*a, **k):
    return k.get("default", a[1] if len(a) > 1 else "")
def _columns(n):
    return [types.SimpleNamespace() for _ in range(n)]
def _expander(*a, **k):
    return types.SimpleNamespace(__enter__=lambda: None, __exit__=lambda *x: None)
def _spinner(*a, **k):
    return types.SimpleNamespace(__enter__=lambda: None, __exit__=lambda *x: None)

st.radio = _radio
st.selectbox = _selectbox
st.text_input = _text_input
st.text_area = _text_area
st.file_uploader = _file_uploader
st.button = _button
st.segmented_control = _segmented_control
st.columns = _columns
st.expander = _expander
st.set_page_config = lambda *a, **k: None
for name in ["markdown","title","caption","subheader","success","error","warning",
             "info","dataframe","plotly_chart","write"]:
    setattr(st, name, lambda *a, **k: None)
st.spinner = _spinner

sys.modules["streamlit"] = st

# ---- Mock api_client ------------------------------------------------------
api = types.ModuleType("ui.services.api_client")
api.run = lambda coro: {} if not hasattr(coro, "send") else {}
async def _noop(*a, **k):
    return {}
for fn in ["upload_dataset","list_samples","connect_source","get_domain_details",
           "preview_dataset","start_agent","run_agent","health"]:
    setattr(api, fn, _noop)
sys.modules["ui.services.api_client"] = api

# ---- Run ------------------------------------------------------------------
import dashboard
try:
    dashboard.render_dashboard()
    print("RENDER OK (no dataset path)")
except Exception:
    import traceback
    traceback.print_exc()
    print("RENDER FAILED")
