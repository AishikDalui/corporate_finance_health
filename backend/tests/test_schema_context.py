"""Unit tests for Schema Context Builder."""
from backend.app.core.schema_context import SchemaContextBuilder


def test_schema_contains_all_core_tables():
    context = SchemaContextBuilder.get_full_schema_context()
    assert "income_statement" in context
    assert "balance_sheet" in context
    assert "cash_flow" in context
    assert "accounts_payable" in context


def test_schema_contains_column_guidelines():
    context = SchemaContextBuilder.get_full_schema_context()
    assert "gross_margin_pct" in context
    assert "current_ratio" in context
    assert "operating_cash_flow" in context
    assert "unscaled USD" in context


def test_schema_contains_join_rules():
    context = SchemaContextBuilder.get_full_schema_context()
    assert "JOIN CONDITION" in context
    assert "end" in context
