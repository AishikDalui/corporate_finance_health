"""Schema context builder that produces rich DDL and business rules for the LLM."""
from typing import Dict, Any


class SchemaContextBuilder:
    """Generates structured schema descriptions and financial business definitions for LLM prompting."""

    TABLE_SCHEMAS: Dict[str, str] = {
        "income_statement": """
CREATE TABLE income_statement (
    start DATE COMMENT 'Fiscal period start date (YYYY-MM-DD)',
    end DATE COMMENT 'Fiscal period end date (YYYY-MM-DD) - primary date key for joins and filtering',
    revenue BIGINT COMMENT 'Total net sales revenue in unscaled USD (e.g. 394328000000 = $394.3B)',
    cogs BIGINT COMMENT 'Cost of goods sold in unscaled USD',
    operating_income BIGINT COMMENT 'Operating income / EBIT in unscaled USD',
    net_income BIGINT COMMENT 'Net profit after all taxes and expenses in unscaled USD',
    gross_profit BIGINT COMMENT 'Gross profit (revenue - cogs) in unscaled USD',
    gross_margin_pct DOUBLE COMMENT 'Gross profit margin % (e.g. 46.91 means 46.91%)',
    operating_margin_pct DOUBLE COMMENT 'Operating margin % (e.g. 31.97%)',
    net_margin_pct DOUBLE COMMENT 'Net profit margin % (e.g. 26.3%)'
);
-- Historical coverage: FY2007 through FY2025 (~19 annual reporting periods).
""",
        "balance_sheet": """
CREATE TABLE balance_sheet (
    end DATE COMMENT 'Fiscal year end date (YYYY-MM-DD) - primary date key',
    total_assets BIGINT COMMENT 'Total assets in unscaled USD',
    total_liabilities BIGINT COMMENT 'Total liabilities in unscaled USD',
    stockholders_equity BIGINT COMMENT 'Shareholders equity / book value in unscaled USD',
    current_assets BIGINT COMMENT 'Total current assets in unscaled USD',
    current_liabilities BIGINT COMMENT 'Total current obligations due within 1 year in unscaled USD',
    working_capital BIGINT COMMENT 'Working capital (current_assets - current_liabilities) in unscaled USD. Note: Apple intentionally operates with negative working capital',
    current_ratio DOUBLE COMMENT 'Current ratio multiplier (current_assets / current_liabilities)',
    cash BIGINT COMMENT 'Cash, cash equivalents, and marketable securities in unscaled USD',
    accounts_receivable BIGINT COMMENT 'Trade receivables from customers in unscaled USD',
    inventory BIGINT COMMENT 'Total inventory in unscaled USD',
    other_current_assets BIGINT COMMENT 'Prepaid expenses and other current assets in unscaled USD',
    cash_pct DOUBLE COMMENT 'Cash as % of current assets',
    ar_pct DOUBLE COMMENT 'Receivables as % of current assets',
    inventory_pct DOUBLE COMMENT 'Inventory as % of current assets',
    other_current_assets_pct DOUBLE COMMENT 'Other current assets %'
);
-- Historical coverage: FY2008 through FY2025 (~18 annual reporting periods).
""",
        "cash_flow": """
CREATE TABLE cash_flow (
    start DATE COMMENT 'Period start date (YYYY-MM-DD)',
    end DATE COMMENT 'Period end date (YYYY-MM-DD) - primary date key',
    operating_cash_flow DOUBLE COMMENT 'Cash generated from operating activities (OCF) in unscaled USD',
    net_income BIGINT COMMENT 'Net income reported in unscaled USD',
    depreciation_amortization DOUBLE COMMENT 'Non-cash depreciation & amortization expense',
    share_based_compensation BIGINT COMMENT 'Stock-based compensation expense add-back',
    accounts_receivable_adjustment BIGINT COMMENT 'Cash impact from changes in accounts receivable',
    inventory_adjustment BIGINT COMMENT 'Cash impact from changes in inventory',
    accounts_payable_adjustment BIGINT COMMENT 'Cash impact from changes in accounts payable',
    other_operating_assets_adjustment BIGINT COMMENT 'Cash impact from other operating assets',
    other_operating_liabilities_adjustment BIGINT COMMENT 'Cash impact from other operating liabilities',
    other_noncash_adjustment TEXT COMMENT 'Miscellaneous non-cash adjustments',
    ocf_to_net_income DOUBLE COMMENT 'Earnings quality ratio (operating_cash_flow / net_income)',
    ocf_minus_net_income DOUBLE COMMENT 'Cash surplus (operating_cash_flow - net_income)'
);
-- Historical coverage: FY2007 through FY2025 (~19 annual reporting periods).
""",
        "accounts_payable": """
CREATE TABLE accounts_payable (
    end DATE COMMENT 'Fiscal year end date (YYYY-MM-DD)',
    accounts_payable BIGINT COMMENT 'Trade accounts payable owed to suppliers in unscaled USD'
);
-- Historical coverage: FY2016 through FY2025.
""",
    }

    @classmethod
    def get_full_schema_context(cls) -> str:
        """Return full formatted SQL DDL and analytical guidelines."""
        sections = [
            "### CORPORATE FINANCIAL HEALTH DATABASE SCHEMA",
            "Database: MySQL 8.0 (corporate_financial_health)",
        ]

        for table, ddl in cls.TABLE_SCHEMAS.items():
            sections.append(f"\n-- Table: {table}\n{ddl.strip()}")

        rules = """
### ANALYTICAL RULES & CONVENTIONS:
1. JOIN CONDITION: All financial statements join on `end` (e.g. `income_statement.end = balance_sheet.end`).
2. CURRENCY & SCALE: All monetary values in storage are unscaled base USD (e.g. $394,328,000,000).
   When presenting to management, convert to billions using `ROUND(val / 1e9, 2) AS val_billion`.
3. PERCENTAGES: Margins (`gross_margin_pct`, `operating_margin_pct`, `net_margin_pct`) are stored as 0-100 values (e.g. 46.91).
4. DATE FILTERING: To filter for a calendar or fiscal year, use `YEAR(end) = <YEAR>` or `end = '<YYYY-MM-DD>'`.
5. DIVISION SAFETY: Always wrap denominators with `NULLIF(col, 0)` to prevent division-by-zero errors.
6. TIME SERIES ORDERING: Always sort chronological outputs with `ORDER BY end ASC` (or DESC for latest snapshot).
7. WORKING CAPITAL: Current ratio < 1.0 and negative working capital for Apple is normal and reflects high supplier financing power (negative Cash Conversion Cycle).
"""
        sections.append(rules)
        return "\n".join(sections)
