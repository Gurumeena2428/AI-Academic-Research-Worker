from backend.agent.service import _fallback_plan, _broaden_query, _parse_json


def test_fallback_comparison_plan_has_methodology_and_metrics():
    plan = _fallback_plan("Compare three papers and their evaluation metrics")
    joined = " ".join(plan).lower()
    assert "methodology" in joined
    assert "metrics" in joined


def test_broaden_query_contains_original_task_terms():
    result = _broaden_query("compare papers", "extract methodology")
    assert "compare papers" in result
    assert "methodology" in result


def test_parse_json_handles_markdown_fence():
    assert _parse_json('```json\n{"steps":["search"]}\n```')["steps"] == ["search"]
