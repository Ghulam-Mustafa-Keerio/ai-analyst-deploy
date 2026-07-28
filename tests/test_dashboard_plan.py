from backend.tools.dashboard_plan import build_dashboard_plan


def test_build_dashboard_plan_uses_domain_and_columns() -> None:
    plan = build_dashboard_plan(
        ["revenue", "region", "order_date", "customer_segment"],
        {"domain": {"domain": "retail", "confidence": 0.91}},
    )

    assert plan["domain"] == "retail"
    assert plan["title"].startswith("Retail")
    assert "revenue" in plan["recommended_metrics"][0].lower()
    assert any("trend" in card.lower() for card in plan["recommended_charts"])


def test_build_dashboard_plan_falls_back_to_general_template() -> None:
    plan = build_dashboard_plan(["feature_a", "feature_b"], {"domain": {"domain": "general"}})

    assert plan["domain"] == "general"
    assert plan["recommended_metrics"]
    assert plan["recommended_charts"]
