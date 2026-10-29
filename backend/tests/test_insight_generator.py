"""Unit tests for Executive Insight Generator."""
from backend.app.core.insight_generator import InsightGenerator


def test_currency_formatting():
    assert InsightGenerator.format_currency(395800000000) == "$395.80B"
    assert InsightGenerator.format_currency(45000000) == "$45.00M"
    assert InsightGenerator.format_currency(1200000000000) == "$1.20T"
    assert InsightGenerator.format_currency(-5000000000) == "-$5.00B"


def test_single_row_insight_generation():
    data = [{"fiscal_year_end": "2025-09-27", "revenue_billion": 395.8, "gross_margin_pct": 46.91}]
    insight = InsightGenerator.generate_rule_based_insight("Revenue in 2025", data)
    assert "2025-09-27" in insight
    assert "46.91%" in insight


def test_suggested_followups():
    margin_followups = InsightGenerator.generate_suggested_followups("What is the gross margin?", [])
    assert len(margin_followups) >= 2
    assert any("margin" in f.lower() or "cash" in f.lower() for f in margin_followups)

    ccc_followups = InsightGenerator.generate_suggested_followups("Show working capital and liquidity", [])
    assert len(ccc_followups) >= 2
