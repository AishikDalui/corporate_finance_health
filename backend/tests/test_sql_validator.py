"""Unit tests for SQL Safety Validator."""
import pytest
from backend.app.core.sql_validator import SQLValidator


def test_valid_select_query():
    sql = "SELECT end, revenue, gross_margin_pct FROM income_statement WHERE YEAR(end) = 2024 ORDER BY end ASC;"
    is_valid, msg = SQLValidator.validate(sql)
    assert is_valid is True
    assert "Valid" in msg


def test_valid_cte_query():
    sql = """
    WITH margin_trends AS (
        SELECT end, gross_margin_pct, LAG(gross_margin_pct) OVER (ORDER BY end) AS prev_margin
        FROM income_statement
    )
    SELECT * FROM margin_trends WHERE prev_margin IS NOT NULL;
    """
    is_valid, msg = SQLValidator.validate(sql)
    assert is_valid is True


def test_valid_multi_table_join():
    sql = """
    SELECT i.end, i.revenue, b.total_assets, c.operating_cash_flow
    FROM income_statement i
    JOIN balance_sheet b ON i.end = b.end
    JOIN cash_flow c ON i.end = c.end
    ORDER BY i.end;
    """
    is_valid, msg = SQLValidator.validate(sql)
    assert is_valid is True


def test_blocks_insert():
    sql = "INSERT INTO income_statement (revenue) VALUES (1000000);"
    is_valid, msg = SQLValidator.validate(sql)
    assert is_valid is False
    assert "forbidden keyword" in msg.lower() or "only select" in msg.lower()


def test_blocks_update():
    sql = "UPDATE balance_sheet SET cash = 0 WHERE end = '2025-09-27';"
    is_valid, msg = SQLValidator.validate(sql)
    assert is_valid is False
    assert "forbidden" in msg.lower() or "only select" in msg.lower()


def test_blocks_delete():
    sql = "DELETE FROM cash_flow WHERE end = '2024-09-28';"
    is_valid, msg = SQLValidator.validate(sql)
    assert is_valid is False
    assert "forbidden" in msg.lower() or "only select" in msg.lower()


def test_blocks_drop_table():
    sql = "DROP TABLE income_statement;"
    is_valid, msg = SQLValidator.validate(sql)
    assert is_valid is False
    assert "forbidden" in msg.lower() or "only select" in msg.lower()


def test_blocks_stacked_queries():
    sql = "SELECT * FROM income_statement; DROP TABLE balance_sheet;"
    is_valid, msg = SQLValidator.validate(sql)
    assert is_valid is False
    assert "multiple" in msg.lower() or "forbidden" in msg.lower()


def test_blocks_unauthorized_tables():
    sql = "SELECT * FROM users WHERE id = 1;"
    is_valid, msg = SQLValidator.validate(sql)
    assert is_valid is False
    assert "unauthorized table" in msg.lower()


def test_blocks_system_schema():
    sql = "SELECT * FROM information_schema.tables;"
    is_valid, msg = SQLValidator.validate(sql)
    assert is_valid is False
    assert "forbidden" in msg.lower() or "unauthorized" in msg.lower()


def test_sanitizer_removes_markdown_ticks():
    raw = "```sql\nSELECT * FROM income_statement;\n```"
    sanitized = SQLValidator.sanitize(raw)
    assert not sanitized.startswith("```")
    assert not sanitized.endswith("```")
    assert not sanitized.endswith(";")
    assert "SELECT * FROM income_statement" == sanitized


def test_blocks_empty_query():
    is_valid, msg = SQLValidator.validate("")
    assert is_valid is False
