"""Unit tests for Pre-built Query Library."""
from backend.app.core.query_library import QueryLibrary


def test_match_profitability_margins():
    lib = QueryLibrary()
    template = lib.match("What are Apple's multi-stage profitability margins?")
    assert template is not None
    assert template.id == "profitability_margins"
    assert "gross_margin_pct" in template.sql


def test_match_cash_conversion_cycle():
    lib = QueryLibrary()
    template = lib.match("Show me the cash conversion cycle and working capital days")
    assert template is not None
    assert template.id == "cash_conversion_cycle"
    assert "estimated_ccc_days" in template.sql


def test_match_solvency_and_leverage():
    lib = QueryLibrary()
    template = lib.match("What is Apple's balance sheet solvency and liabilities to equity leverage?")
    assert template is not None
    assert template.id == "solvency_and_leverage"
    assert "liabilities_to_equity_ratio" in template.sql


def test_match_earnings_quality():
    lib = QueryLibrary()
    template = lib.match("Compare operating cash flow with net income for earnings quality")
    assert template is not None
    assert template.id == "cash_flow_quality"
    assert "operating_cash_flow" in template.sql


def test_year_filter_applied_to_query():
    lib = QueryLibrary()
    template = lib.match("Show profitability margins", year_filter=2024)
    assert template is not None
    assert "2024" in template.sql
    assert "2024" in template.name
    assert "_report_data" in template.sql or "base_query" in template.sql


def test_multi_table_join_prevents_ambiguous_end_column():
    lib = QueryLibrary()
    template = lib.match("Show executive financial health summary for 2025", year_filter=2025)
    assert template is not None
    assert template.id == "financial_health_master"
    assert "_report_data.fiscal_year_end" in template.sql
    assert "YEAR(end)" not in template.sql  # Ensure ambiguous column is never used


def test_auto_detect_year_from_question_text():
    lib = QueryLibrary()
    template = lib.match("Show executive financial health summary for 2024")
    assert template is not None
    assert "2024" in template.name
    assert "2024" in template.sql


def test_match_total_dso():
    lib = QueryLibrary()
    template = lib.match("total dso")
    assert template is not None
    assert template.id == "days_sales_outstanding"
    assert "estimated_dso_days" in template.sql


def test_match_dpo():
    lib = QueryLibrary()
    template = lib.match("what is total dpo in 2024")
    assert template is not None
    assert template.id == "days_payable_outstanding"
    assert "2024" in template.sql
    assert "estimated_dpo_days" in template.sql


def test_no_match_for_unrelated_query():
    lib = QueryLibrary()
    template = lib.match("Who is the CEO of Apple?")
    assert template is None
