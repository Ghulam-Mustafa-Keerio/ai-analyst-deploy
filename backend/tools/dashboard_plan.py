from __future__ import annotations

from typing import Any


def _infer_domain(columns: list[str]) -> str:
    text = " ".join(str(column).strip().lower() for column in columns if str(column).strip())
    if any(keyword in text for keyword in ["revenue", "sales", "profit", "order", "customer", "product", "price", "region", "store", "inventory"]):
        return "retail"
    if any(keyword in text for keyword in ["loan", "balance", "interest", "expense", "asset", "risk", "cash", "payment", "credit", "income", "finance"]):
        return "finance"
    if any(keyword in text for keyword in ["patient", "clinic", "diagnosis", "hospital", "medical", "treatment", "lab", "outcome", "visit"]):
        return "healthcare"
    if any(keyword in text for keyword in ["machine", "defect", "production", "throughput", "downtime", "yield", "line", "plant", "shift"]):
        return "manufacturing"
    return "general"


def build_dashboard_plan(columns: list[str], profile: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a domain-aware dashboard plan based on dataset profile and schema hints."""
    domain_profile = (profile or {}).get("domain") if isinstance(profile, dict) else None
    if isinstance(domain_profile, dict):
        domain_name = str(domain_profile.get("domain") or "general").strip().lower()
    else:
        domain_name = _infer_domain(columns)

    normalized_columns = [str(column).strip().lower() for column in columns if str(column).strip()]
    text = " ".join(normalized_columns)

    if domain_name in {"retail", "commerce", "ecommerce"}:
        title = "Retail growth dashboard"
        summary = "Track sales performance, customer segments, and regional demand to guide merchandising and inventory decisions."
        metrics = ["Revenue", "Orders", "Average order value", "Customer retention"]
        charts = ["Sales trend over time", "Category mix breakdown", "Regional performance map", "Customer cohort analysis"]
        filters = ["Region", "Channel", "Product category", "Customer segment"]
    elif domain_name in {"finance", "banking", "insurance"}:
        title = "Finance risk & performance dashboard"
        summary = "Monitor cash flow, revenue quality, and risk exposure with decision-ready thresholds."
        metrics = ["Revenue", "Margin", "Risk exposure", "Delinquency rate"]
        charts = ["Cash flow trend", "Risk concentration chart", "Portfolio mix view", "Forecast vs actual"]
        filters = ["Account segment", "Region", "Product type", "Risk band"]
    elif domain_name in {"healthcare", "medical", "pharma"}:
        title = "Healthcare operations dashboard"
        summary = "Surface utilization, outcomes, and care quality signals for clinicians and operations teams."
        metrics = ["Patient volume", "Readmission rate", "Satisfaction score", "Cost per visit"]
        charts = ["Daily volume trend", "Outcome distribution", "Care quality heatmap", "Cost comparison chart"]
        filters = ["Department", "Facility", "Patient cohort", "Time period"]
    elif domain_name in {"manufacturing", "industrial"}:
        title = "Manufacturing operations dashboard"
        summary = "Highlight throughput, failures, and quality to accelerate process improvement."
        metrics = ["Throughput", "Defect rate", "Downtime", "Yield"]
        charts = ["Production trend", "Downtime by line", "Quality control chart", "Root-cause breakdown"]
        filters = ["Line", "Shift", "Plant", "Product family"]
    else:
        title = "General analytics dashboard"
        summary = "Provide a versatile overview of the dataset shape, quality, and relationships."
        metrics = ["Row volume", "Missingness", "Distribution quality", "Feature impact"]
        charts = ["Data quality overview", "Feature distribution", "Correlation heatmap", "Outcome trend"]
        filters = ["Time window", "Segment", "Category", "Region"]

    if any(keyword in text for keyword in ["revenue", "sales", "profit", "order", "customer", "product", "region"]):
        metrics = [metric for metric in metrics if metric not in {"Row volume", "Feature impact"}] + ["Revenue contribution"]

    if any(keyword in text for keyword in ["date", "time", "month", "year", "day"]):
        charts = ["Trend over time"] + [chart for chart in charts if chart != "Trend over time"]

    return {
        "domain": domain_name or "general",
        "title": title,
        "summary": summary,
        "recommended_metrics": metrics,
        "recommended_charts": charts,
        "filters": filters,
    }
