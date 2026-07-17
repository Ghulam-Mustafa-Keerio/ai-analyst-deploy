from __future__ import annotations

from typing import Any

import math
import streamlit as st  # type: ignore


def scatter_3d(points: list[dict[str, Any]], *, height: int = 460, color: str = "#2563eb", title: str = "") -> None:
    """Render an interactive 3D point cloud from embedding points.

    ``points`` is a list of dicts with keys ``x``, ``y``, ``z`` and optional
    ``label``. Falls back to a message when plotly is unavailable.
    """
    try:
        import plotly.graph_objects as go  # type: ignore
    except ImportError:
        st.info("3D visualisation requires `plotly`. Install it to see the point cloud.")
        return

    if not points:
        st.caption("No points to render in 3D.")
        return

    xs: list[float] = [float(p["x"]) for p in points]
    ys: list[float] = [float(p["y"]) for p in points]
    zs: list[float] = [float(p["z"]) for p in points]
    labels: list[str] = [str(p.get("label", "")) for p in points]

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="markers",
                text=labels,
                hoverinfo="text",
                marker=dict(size=4, color=color, opacity=0.85, line=dict(width=0)),
            )
        ]
    )
    fig.update_layout(
        title=title or None,
        height=height,
        margin=dict(l=0, r=0, t=30 if title else 0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        scene=dict(
            xaxis=dict(showbackground=False, gridcolor="rgba(100,116,139,0.15)"),
            yaxis=dict(showbackground=False, gridcolor="rgba(100,116,139,0.15)"),
            zaxis=dict(showbackground=False, gridcolor="rgba(100,116,139,0.15)"),
        ),
        font=dict(color="#1e293b"),
    )
    st.plotly_chart(fig, use_container_width=True)


def pipeline_3d(stages: list[dict[str, Any]], *, height: int = 520) -> None:
    """Render the agent pipeline as a 3D node graph.

    ``stages`` is a list of dicts with ``name`` and ``status``
    (queued | running | completed | failed). Nodes are laid out on a helix so
    the execution order reads as a 3D spiral.
    """
    try:
        import plotly.graph_objects as go  # type: ignore
    except ImportError:
        st.info("3D visualisation requires `plotly`. Install it to see the pipeline graph.")
        return

    if not stages:
        st.caption("No pipeline stages to render.")
        return

    status_color = {
        "completed": "#16a34a",
        "failed": "#dc2626",
        "running": "#2563eb",
        "queued": "#94a3b8",
    }
    n = len(stages)
    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    colors: list[str] = []
    texts: list[str] = []
    sizes: list[int] = []
    for i, stage in enumerate(stages):
        angle = i / max(n - 1, 1) * 2 * math.pi * 1.5
        radius = 1.0 + 0.15 * (i % 3)
        xs.append(radius * math.cos(angle))
        ys.append(radius * math.sin(angle))
        zs.append(i / max(n - 1, 1) * 4 - 2)
        status = stage.get("status", "queued")
        colors.append(status_color.get(status, "#94a3b8"))
        texts.append(f"{stage['name']}<br><span style='font-size:11px'>{status}</span>")
        sizes.append(14 if status == "running" else 10)

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="markers+lines+text",
                text=[s["name"] for s in stages],
                textposition="top center",
                hovertext=texts,
                hoverinfo="text",
                marker=dict(size=sizes, color=colors, opacity=0.95, line=dict(width=0)),
                line=dict(color="rgba(100,116,139,0.35)", width=3),
            )
        ]
    )
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        scene=dict(
            xaxis=dict(showbackground=False, showticklabels=False, gridcolor="rgba(156,176,205,0.12)"),
            yaxis=dict(showbackground=False, showticklabels=False, gridcolor="rgba(156,176,205,0.12)"),
            zaxis=dict(showbackground=False, showticklabels=False, gridcolor="rgba(156,176,205,0.12)"),
        ),
        font=dict(color="#1e293b"),
    )
    st.plotly_chart(fig, use_container_width=True)


def experiments_3d(experiments: list[dict[str, Any]], *, height: int = 480) -> None:
    """Render completed experiments as a 3D scatter (metric space).

    Each experiment is placed by three numeric metrics when available
    (accuracy, f1, train_time). Missing metrics default to 0.
    """
    try:
        import plotly.graph_objects as go  # type: ignore
    except ImportError:
        st.info("3D visualisation requires `plotly`. Install it to see the experiment space.")
        return

    if not experiments:
        st.caption("No experiments to render.")
        return

    def _num(exp: dict[str, Any], key: str) -> float:
        # Metrics are stored nested under ``exp["metrics"]`` (see ExperimentStore).
        metrics = exp.get("metrics") or {}
        val = metrics.get(key)
        if isinstance(val, dict):
            val = val.get("value")
        try:
            return float(val)
        except (TypeError, ValueError):
            return 0.0

    xs: list[float] = [_num(e, "accuracy") for e in experiments]
    ys: list[float] = [_num(e, "f1") for e in experiments]
    zs: list[float] = [_num(e, "train_time") for e in experiments]
    labels: list[str] = [str(e.get("job_id", e.get("model", ""))[:8]) for e in experiments]

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="markers+text",
                text=labels,
                textposition="top center",
                hoverinfo="text",
                marker=dict(
                    size=10,
                    color=zs,
                    colorscale="Viridis",
                    opacity=0.9,
                    line=dict(width=0),
                ),
            )
        ]
    )
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        scene=dict(
            xaxis_title="accuracy",
            yaxis_title="f1",
            zaxis_title="train_time",
            xaxis=dict(gridcolor="rgba(156,176,205,0.15)"),
            yaxis=dict(gridcolor="rgba(156,176,205,0.15)"),
            zaxis=dict(gridcolor="rgba(156,176,205,0.15)"),
        ),
        font=dict(color="#1e293b"),
    )
    st.plotly_chart(fig, use_container_width=True)


def sources_3d(sources: list[dict[str, Any]], *, height: int = 460) -> None:
    """Render the available data sources as a 3D constellation.

    Each source is a node positioned by a stable hash of its key so the layout
    is deterministic. Hovering reveals the description. This gives the ingest
    panel a spatial, "control plane" feel.
    """
    try:
        import plotly.graph_objects as go  # type: ignore
    except ImportError:
        st.info("3D visualisation requires `plotly`. Install it to see the source map.")
        return

    if not sources:
        st.caption("No data sources available.")
        return

    def _pos(seed: str) -> tuple[float, float, float]:
        import hashlib

        h = hashlib.sha256(seed.encode()).digest()
        return (
            (int.from_bytes(h[0:2], "big") / 65535 - 0.5) * 6,
            (int.from_bytes(h[2:4], "big") / 65535 - 0.5) * 6,
            (int.from_bytes(h[4:6], "big") / 65535 - 0.5) * 6,
        )

    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    texts: list[str] = []
    colors: list[str] = []
    palette = ["#2563eb", "#16a34a", "#d97706", "#dc2626", "#7c3aed", "#0891b2", "#ca8a04", "#059669", "#e11d48"]
    for i, src in enumerate(sources):
        x, y, z = _pos(src.get("key", str(i)))
        xs.append(x)
        ys.append(y)
        zs.append(z)
        texts.append(f"<b>{src.get('key')}</b><br><span style='font-size:11px'>{src.get('description', '')}</span>")
        colors.append(palette[i % len(palette)])

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="markers+text",
                text=[s.get("key", "") for s in sources],
                textposition="top center",
                hovertext=texts,
                hoverinfo="text",
                marker=dict(size=14, color=colors, opacity=0.92, line=dict(width=0)),
            )
        ]
    )
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        scene=dict(
            xaxis=dict(showbackground=False, showticklabels=False, gridcolor="rgba(156,176,205,0.12)"),
            yaxis=dict(showbackground=False, showticklabels=False, gridcolor="rgba(156,176,205,0.12)"),
            zaxis=dict(showbackground=False, showticklabels=False, gridcolor="rgba(156,176,205,0.12)"),
        ),
        font=dict(color="#1e293b"),
    )
    st.plotly_chart(fig, use_container_width=True)


def schema_3d(schema: dict[str, str], missing_ratio: dict[str, float] | None = None, *, height: int = 460) -> None:
    """Render dataset columns as a 3D bar field.

    Columns are placed on a grid; bar height encodes missing-ratio (or 1.0 when
    unknown) so sparse columns tower above dense ones. Colour encodes dtype
    family (numeric vs categorical).
    """
    try:
        import plotly.graph_objects as go  # type: ignore
    except ImportError:
        st.info("3D visualisation requires `plotly`. Install it to see the schema field.")
        return

    if not schema:
        st.caption("No schema to render.")
        return

    missing_ratio = missing_ratio or {}
    cols = list(schema.keys())
    n = len(cols)
    side = max(int(n ** 0.5), 1)
    xs: list[int] = []
    ys: list[int] = []
    zs: list[float] = []
    heights: list[float] = []
    colors: list[str] = []
    texts: list[str] = []
    numeric_color, cat_color = "#2563eb", "#d97706"
    for i, col in enumerate(cols):
        gx = i % side
        gy = i // side
        miss = float(missing_ratio.get(col, 0.0))
        xs.append(gx)
        ys.append(gy)
        zs.append(miss / 2)
        heights.append(max(miss, 0.02))
        is_numeric = any(t in schema[col].lower() for t in ("int", "float", "double", "number"))
        colors.append(numeric_color if is_numeric else cat_color)
        texts.append(f"<b>{col}</b><br>dtype: {schema[col]}<br>missing: {miss:.1%}")

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="markers",
                hovertext=texts,
                hoverinfo="text",
                marker=dict(
                    size=[max(h * 22, 4) for h in heights],
                    color=colors,
                    opacity=0.9,
                    line=dict(width=0),
                ),
            )
        ]
    )
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        scene=dict(
            xaxis_title="column index",
            yaxis_title="column index",
            zaxis_title="missing ratio",
            xaxis=dict(gridcolor="rgba(156,176,205,0.12)"),
            yaxis=dict(gridcolor="rgba(156,176,205,0.12)"),
            zaxis=dict(gridcolor="rgba(156,176,205,0.12)"),
        ),
        font=dict(color="#1e293b"),
    )
    st.plotly_chart(fig, use_container_width=True)


def metrics_3d(metrics: dict[str, float], *, height: int = 460) -> None:
    """Render a model's metrics as a 3D surface of normalised scores.

    Each metric becomes a vertex on a unit sphere; the radial distance encodes
    the (0-1 normalised) score. Gives an at-a-glance "quality globe".
    """
    try:
        import plotly.graph_objects as go  # type: ignore
    except ImportError:
        st.info("3D visualisation requires `plotly`. Install it to see the metrics globe.")
        return

    if not metrics:
        st.caption("No metrics to render.")
        return

    keys = list(metrics.keys())
    n = len(keys)
    vals = [float(v) for v in metrics.values()]
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0
    norm = [(v - lo) / span for v in vals]

    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    texts: list[str] = []
    sizes: list[float] = []
    for i, (k, v, nv) in enumerate(zip(keys, vals, norm)):
        angle = i / max(n, 1) * 2 * math.pi
        r = 0.4 + nv * 0.6
        xs.append(r * math.cos(angle))
        ys.append(r * math.sin(angle))
        zs.append(nv)
        texts.append(f"<b>{k}</b>: {v:.4f}")
        sizes.append(8 + nv * 18)

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="markers+text",
                text=keys,
                textposition="top center",
                hovertext=texts,
                hoverinfo="text",
                marker=dict(size=sizes, color=zs, colorscale="Viridis", opacity=0.92, line=dict(width=0)),
            )
        ]
    )
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        scene=dict(
            xaxis=dict(showbackground=False, showticklabels=False, gridcolor="rgba(156,176,205,0.12)"),
            yaxis=dict(showbackground=False, showticklabels=False, gridcolor="rgba(156,176,205,0.12)"),
            zaxis=dict(showbackground=False, showticklabels=False, gridcolor="rgba(156,176,205,0.12)"),
        ),
        font=dict(color="#1e293b"),
    )
    st.plotly_chart(fig, use_container_width=True)


def feature_importance_3d(importance: dict[str, float], *, height: int = 460) -> None:
    """Render feature importance as a 3D helix.

    Features are ordered by importance and wrapped around a vertical helix;
    radial distance encodes the normalised importance so the most predictive
    features stand proud of the core.
    """
    try:
        import plotly.graph_objects as go  # type: ignore
    except ImportError:
        st.info("3D visualisation requires `plotly`. Install it to see feature importance.")
        return

    if not importance:
        st.caption("No feature importance to render.")
        return

    items = sorted(importance.items(), key=lambda kv: kv[1], reverse=True)
    n = len(items)
    vals = [float(v) for _, v in items]
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1.0

    xs: list[float] = []
    ys: list[float] = []
    zs: list[float] = []
    texts: list[str] = []
    colors: list[float] = []
    for i, (feat, v) in enumerate(items):
        t = i / max(n - 1, 1)
        angle = t * 2 * math.pi * 1.5
        nv = (v - lo) / span
        r = 0.3 + nv * 1.2
        xs.append(r * math.cos(angle))
        ys.append(r * math.sin(angle))
        zs.append(t * 4 - 2)
        texts.append(f"<b>{feat}</b>: {v:.4f}")
        colors.append(nv)

    fig = go.Figure(
        data=[
            go.Scatter3d(
                x=xs,
                y=ys,
                z=zs,
                mode="markers+lines+text",
                text=[f[:10] for f, _ in items],
                textposition="top center",
                hovertext=texts,
                hoverinfo="text",
                marker=dict(size=9, color=colors, colorscale="Plasma", opacity=0.95, line=dict(width=0)),
                line=dict(color="rgba(156,176,205,0.3)", width=2),
            )
        ]
    )
    fig.update_layout(
        height=height,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False,
        scene=dict(
            xaxis=dict(showbackground=False, showticklabels=False, gridcolor="rgba(156,176,205,0.12)"),
            yaxis=dict(showbackground=False, showticklabels=False, gridcolor="rgba(156,176,205,0.12)"),
            zaxis=dict(showbackground=False, showticklabels=False, gridcolor="rgba(156,176,205,0.12)"),
        ),
        font=dict(color="#1e293b"),
    )
    st.plotly_chart(fig, use_container_width=True)
