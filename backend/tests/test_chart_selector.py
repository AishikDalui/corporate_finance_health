"""Unit tests for Dynamic Chart Selector."""
from backend.app.core.chart_selector import ChartSelector


def test_single_row_selects_kpi_card():
    data = [{"fiscal_year_end": "2025-09-27", "revenue_billion": 395.8, "gross_margin_pct": 46.9}]
    chart = ChartSelector.select_chart("What was revenue in 2025?", data)
    assert chart is not None
    assert chart.chart_type == "kpi_card"


def test_time_series_selects_line_chart():
    data = [
        {"fiscal_year_end": "2023-09-30", "revenue_billion": 383.2},
        {"fiscal_year_end": "2024-09-28", "revenue_billion": 391.0},
        {"fiscal_year_end": "2025-09-27", "revenue_billion": 395.8},
    ]
    chart = ChartSelector.select_chart("Revenue trajectory", data)
    assert chart is not None
    assert chart.chart_type == "line"
    assert chart.x_axis == "fiscal_year_end"


def test_explicit_preference_overrides_heuristic():
    data = [
        {"fiscal_year_end": "2024-09-28", "gross_margin_pct": 46.2},
        {"fiscal_year_end": "2025-09-27", "gross_margin_pct": 46.9},
    ]
    chart = ChartSelector.select_chart("Gross margin", data, chart_preference="bar")
    assert chart is not None
    assert chart.chart_type == "bar"


def test_percentage_format_inference():
    data = [
        {"fiscal_year_end": "2024-09-28", "gross_margin_pct": 46.2},
        {"fiscal_year_end": "2025-09-27", "gross_margin_pct": 46.9},
    ]
    chart = ChartSelector.select_chart("Gross margin", data)
    assert chart.format_type == "percentage"
