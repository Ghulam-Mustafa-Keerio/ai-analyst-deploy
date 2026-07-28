from ui.pages import dashboard


def test_dashboard_helpers_handle_missing_or_invalid_dataset_payloads() -> None:
    assert dashboard._dataset_schema(None) == {}
    assert dashboard._dataset_schema({"schema": {"age": "int64"}}) == {"age": "int64"}
    assert dashboard._dataset_columns(None) == []
    assert dashboard._dataset_columns({"schema": {"age": "int64", "city": "object"}}) == ["age", "city"]
    assert dashboard._dataset_id(None) == ""
    assert dashboard._dataset_id({"dataset_id": "abc123"}) == "abc123"
