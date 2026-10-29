"""Pre-built Query Library mapping executive questions to vetted analytical SQL queries."""
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import re


@dataclass
class QueryTemplate:
    """Pre-built financial query definition."""

    id: str
    name: str
    description: str
    keywords: List[str]
    sql: str
    chart_type: str = "line"
    format_type: str = "number"
    x_axis: str = "fiscal_year_end"
    y_axis: str = "value"
    title: str = "Financial Analysis"


class QueryLibrary:
    """Library of verified SQL queries derived from the project's Exp2.sql, exp3.sql, and Untitled.sql."""

    def __init__(self):
        self.templates: Dict[str, QueryTemplate] = self._init_templates()

    def _init_templates(self) -> Dict[str, QueryTemplate]:
        return {
            "profitability_margins": QueryTemplate(
                id="profitability_margins",
                name="Multi-Stage Profitability Margins",
                description="Gross, operating, and net margins across fiscal years",
                keywords=["margin", "margins", "profitability", "gross margin", "operating margin", "net margin"],
                sql="""
SELECT
    end AS fiscal_year_end,
    ROUND(revenue / 1e9, 2) AS revenue_billion,
    gross_margin_pct,
    operating_margin_pct,
    net_margin_pct
FROM income_statement
ORDER BY end ASC;
""".strip(),
                chart_type="line",
                format_type="percentage",
                x_axis="fiscal_year_end",
                y_axis="gross_margin_pct",
                title="Apple Inc. Multi-Stage Profitability Margins (%)",
            ),

            "margin_expansion_trends": QueryTemplate(
                id="margin_expansion_trends",
                name="YoY Margin Expansion & Contraction",
                description="Year-over-year percentage point changes in margins using window functions",
                keywords=["expansion", "contraction", "margin trend", "margin change", "volatility", "spread"],
                sql="""
WITH margin_trends AS (
    SELECT
        end AS fiscal_year_end,
        gross_margin_pct,
        operating_margin_pct,
        net_margin_pct,
        LAG(gross_margin_pct) OVER (ORDER BY end) AS previous_gross_margin,
        LAG(operating_margin_pct) OVER (ORDER BY end) AS previous_operating_margin,
        LAG(net_margin_pct) OVER (ORDER BY end) AS previous_net_margin
    FROM income_statement
)
SELECT
    fiscal_year_end,
    ROUND(gross_margin_pct - previous_gross_margin, 2) AS gross_margin_change_pp,
    ROUND(operating_margin_pct - previous_operating_margin, 2) AS operating_margin_change_pp,
    ROUND(net_margin_pct - previous_net_margin, 2) AS net_margin_change_pp
FROM margin_trends
WHERE previous_gross_margin IS NOT NULL
ORDER BY fiscal_year_end ASC;
""".strip(),
                chart_type="bar",
                format_type="number",
                x_axis="fiscal_year_end",
                y_axis="gross_margin_change_pp",
                title="Year-over-Year Margin Expansion / Contraction (pp)",
            ),

            "solvency_and_leverage": QueryTemplate(
                id="solvency_and_leverage",
                name="Balance Sheet Leverage & Solvency",
                description="Liabilities-to-equity ratio and asset encumbrance percentage",
                keywords=["solvency", "leverage", "debt", "liabilities to equity", "debt to equity", "gearing"],
                sql="""
SELECT
    end AS fiscal_year_end,
    ROUND(total_assets / 1e9, 2) AS total_assets_billion,
    ROUND(total_liabilities / 1e9, 2) AS total_liabilities_billion,
    ROUND(stockholders_equity / 1e9, 2) AS equity_billion,
    ROUND(total_liabilities / NULLIF(stockholders_equity, 0), 4) AS liabilities_to_equity_ratio,
    ROUND(total_liabilities / NULLIF(total_assets, 0) * 100, 2) AS liabilities_to_assets_pct
FROM balance_sheet
ORDER BY end ASC;
""".strip(),
                chart_type="line",
                format_type="ratio",
                x_axis="fiscal_year_end",
                y_axis="liabilities_to_equity_ratio",
                title="Apple Inc. Financial Leverage & Liabilities-to-Equity Ratio",
            ),

            "financial_health_master": QueryTemplate(
                id="financial_health_master",
                name="Master Cross-Statement Health Dashboard",
                description="Consolidated 3-statement metrics joining income statement, balance sheet, and cash flow",
                keywords=["master", "overview", "executive summary", "dashboard", "health summary", "kpi summary", "all metrics"],
                sql="""
SELECT
    i.end AS fiscal_year_end,
    ROUND(i.revenue / 1e9, 2) AS revenue_billion,
    ROUND(i.net_income / 1e9, 2) AS net_income_billion,
    i.gross_margin_pct,
    b.current_ratio,
    ROUND(b.working_capital / 1e9, 2) AS working_capital_billion,
    ROUND(cf.operating_cash_flow / 1e9, 2) AS ocf_billion,
    cf.ocf_to_net_income
FROM income_statement AS i
INNER JOIN balance_sheet AS b ON i.end = b.end
INNER JOIN cash_flow AS cf ON i.end = cf.end
ORDER BY i.end ASC;
""".strip(),
                chart_type="table",
                format_type="mixed",
                x_axis="fiscal_year_end",
                y_axis="revenue_billion",
                title="Executive Three-Statement Financial Health Master View",
            ),

            "liquidity_working_capital": QueryTemplate(
                id="liquidity_working_capital",
                name="Liquidity & Working Capital Structure",
                description="Current assets, current liabilities, working capital, and current ratio",
                keywords=["liquidity", "current ratio", "working capital", "current assets", "current liabilities", "cash position"],
                sql="""
SELECT
    end AS fiscal_year_end,
    ROUND(current_assets / 1e9, 2) AS current_assets_billion,
    ROUND(current_liabilities / 1e9, 2) AS current_liabilities_billion,
    ROUND(working_capital / 1e9, 2) AS working_capital_billion,
    current_ratio,
    ROUND(cash / 1e9, 2) AS cash_billion
FROM balance_sheet
ORDER BY end ASC;
""".strip(),
                chart_type="line",
                format_type="ratio",
                x_axis="fiscal_year_end",
                y_axis="current_ratio",
                title="Working Capital & Liquidity Indicators",
            ),

            "cash_flow_quality": QueryTemplate(
                id="cash_flow_quality",
                name="Earnings Quality & Cash Conversion",
                description="Comparing Operating Cash Flow with Net Income to verify earnings quality",
                keywords=["earnings quality", "cash conversion", "operating cash flow", "ocf", "cash flow quality", "cash vs net income"],
                sql="""
SELECT
    i.end AS fiscal_year_end,
    ROUND(i.net_income / 1e9, 2) AS net_income_billion,
    ROUND(c.operating_cash_flow / 1e9, 2) AS ocf_billion,
    ROUND(c.operating_cash_flow / NULLIF(i.net_income, 0), 4) AS ocf_to_net_income_ratio,
    ROUND((c.operating_cash_flow - i.net_income) / 1e9, 2) AS cash_surplus_billion
FROM income_statement AS i
JOIN cash_flow AS c ON i.end = c.end
ORDER BY i.end ASC;
""".strip(),
                chart_type="bar",
                format_type="currency",
                x_axis="fiscal_year_end",
                y_axis="ocf_billion",
                title="Earnings Quality: Operating Cash Flow vs. Net Income ($B)",
            ),

            "cash_conversion_cycle": QueryTemplate(
                id="cash_conversion_cycle",
                name="Cash Conversion Cycle (DSO + DIO - DPO)",
                description="Supply chain working capital velocity and cash turnaround duration",
                keywords=["cash conversion cycle", "ccc", "dso", "dio", "dpo", "supplier credit", "receivables days"],
                sql="""
WITH operating_metrics AS (
    SELECT
        b.`end` AS fiscal_year_end,
        b.accounts_receivable,
        b.inventory,
        a.accounts_payable,
        i.revenue,
        i.cogs,
        LAG(b.accounts_receivable) OVER (ORDER BY b.`end`) AS previous_ar,
        LAG(b.inventory) OVER (ORDER BY b.`end`) AS previous_inventory,
        LAG(a.accounts_payable) OVER (ORDER BY b.`end`) AS previous_ap
    FROM balance_sheet b
    JOIN income_statement i ON b.`end` = i.`end`
    JOIN accounts_payable a ON b.`end` = a.`end`
)
SELECT
    fiscal_year_end,
    ROUND(((accounts_receivable + previous_ar) / 2.0) / NULLIF(revenue, 0) * 365, 2) AS estimated_dso_days,
    ROUND(((inventory + previous_inventory) / 2.0) / NULLIF(cogs, 0) * 365, 2) AS estimated_dio_days,
    ROUND(((accounts_payable + previous_ap) / 2.0) / NULLIF(cogs, 0) * 365, 2) AS estimated_dpo_days,
    ROUND(
        (((accounts_receivable + previous_ar) / 2.0) / NULLIF(revenue, 0) * 365) +
        (((inventory + previous_inventory) / 2.0) / NULLIF(cogs, 0) * 365) -
        (((accounts_payable + previous_ap) / 2.0) / NULLIF(cogs, 0) * 365),
        2
    ) AS estimated_ccc_days
FROM operating_metrics
WHERE previous_ar IS NOT NULL
  AND previous_inventory IS NOT NULL
  AND previous_ap IS NOT NULL
ORDER BY fiscal_year_end ASC;
""".strip(),
                chart_type="line",
                format_type="number",
                x_axis="fiscal_year_end",
                y_axis="estimated_ccc_days",
                title="Apple Inc. Cash Conversion Cycle (Days) — Negative CCC Efficiency",
            ),

            "inventory_efficiency": QueryTemplate(
                id="inventory_efficiency",
                name="Inventory Turnover & Days Inventory Outstanding (DIO)",
                description="DIO and inventory management velocity",
                keywords=["inventory", "inventory turnover", "dio", "inventory days", "cogs inventory"],
                sql="""
WITH inventory_metrics AS (
    SELECT
        b.end AS fiscal_year_end,
        b.inventory,
        i.cogs,
        LAG(b.inventory) OVER (ORDER BY b.end) AS previous_inventory
    FROM balance_sheet b
    JOIN income_statement i ON b.end = i.end
)
SELECT
    fiscal_year_end,
    ROUND(inventory / 1e9, 2) AS inventory_billion,
    ROUND(cogs / 1e9, 2) AS cogs_billion,
    ROUND(((inventory + previous_inventory) / 2.0) / NULLIF(cogs, 0) * 365, 2) AS estimated_dio_days
FROM inventory_metrics
WHERE previous_inventory IS NOT NULL
ORDER BY fiscal_year_end ASC;
""".strip(),
                chart_type="bar",
                format_type="number",
                x_axis="fiscal_year_end",
                y_axis="estimated_dio_days",
                title="Apple Inc. Days Inventory Outstanding (DIO)",
            ),

            "days_sales_outstanding": QueryTemplate(
                id="days_sales_outstanding",
                name="Days Sales Outstanding (DSO)",
                description="Customer receivables collection duration in days",
                keywords=["dso", "days sales", "days sales outstanding", "receivable days", "receivables days", "collection period", "customer collection", "total dso"],
                sql="""
WITH receivables_trend AS (
    SELECT
        b.end AS fiscal_year_end,
        i.revenue,
        b.accounts_receivable,
        LAG(b.accounts_receivable) OVER (ORDER BY b.end) AS previous_year_receivables
    FROM balance_sheet AS b
    JOIN income_statement AS i ON b.end = i.end
)
SELECT
    fiscal_year_end,
    ROUND(revenue / 1e9, 2) AS revenue_billion,
    ROUND(accounts_receivable / 1e9, 2) AS accounts_receivable_billion,
    ROUND(((accounts_receivable + previous_year_receivables) / 2.0) / NULLIF(revenue, 0) * 365, 2) AS estimated_dso_days
FROM receivables_trend
WHERE previous_year_receivables IS NOT NULL
ORDER BY fiscal_year_end ASC;
""".strip(),
                chart_type="bar",
                format_type="number",
                x_axis="fiscal_year_end",
                y_axis="estimated_dso_days",
                title="Apple Inc. Days Sales Outstanding (DSO in Days)",
            ),

            "days_payable_outstanding": QueryTemplate(
                id="days_payable_outstanding",
                name="Days Payable Outstanding (DPO)",
                description="Supplier payment duration and trade credit in days",
                keywords=["dpo", "days payable", "days payable outstanding", "payable days", "payables days", "supplier payment", "supplier credit", "total dpo"],
                sql="""
WITH payable_metrics AS (
    SELECT
        b.`end` AS fiscal_year_end,
        a.accounts_payable,
        i.cogs,
        LAG(a.accounts_payable) OVER (ORDER BY b.`end`) AS previous_accounts_payable
    FROM balance_sheet b
    JOIN accounts_payable a ON b.`end` = a.`end`
    JOIN income_statement i ON b.`end` = i.`end`
)
SELECT
    fiscal_year_end,
    ROUND(accounts_payable / 1e9, 2) AS accounts_payable_billion,
    ROUND(cogs / 1e9, 2) AS cogs_billion,
    ROUND(((accounts_payable + previous_accounts_payable) / 2.0) / NULLIF(cogs, 0) * 365, 2) AS estimated_dpo_days
FROM payable_metrics
WHERE previous_accounts_payable IS NOT NULL
ORDER BY fiscal_year_end ASC;
""".strip(),
                chart_type="bar",
                format_type="number",
                x_axis="fiscal_year_end",
                y_axis="estimated_dpo_days",
                title="Apple Inc. Days Payable Outstanding (DPO in Days)",
            ),

            "revenue_growth_trajectory": QueryTemplate(
                id="revenue_growth_trajectory",
                name="Revenue Trajectory & Net Income Scale",
                description="Topline and bottomline scale in billions over time",
                keywords=["revenue", "sales", "top line", "revenue growth", "net sales", "income trajectory"],
                sql="""
SELECT
    end AS fiscal_year_end,
    ROUND(revenue / 1e9, 2) AS revenue_billion,
    ROUND(net_income / 1e9, 2) AS net_income_billion,
    gross_margin_pct,
    net_margin_pct
FROM income_statement
ORDER BY end ASC;
""".strip(),
                chart_type="line",
                format_type="currency",
                x_axis="fiscal_year_end",
                y_axis="revenue_billion",
                title="Revenue ($B) & Net Income ($B) Trajectory",
            ),
        }

    def match(self, question: str, year_filter: Optional[int] = None) -> Optional[QueryTemplate]:
        """Score question against query template keywords and return best match or None."""
        if not question:
            return None

        q_lower = question.lower()
        best_template: Optional[QueryTemplate] = None
        max_score = 0

        for template in self.templates.values():
            score = 0
            for kw in template.keywords:
                # Use regex word boundary check so exact acronyms like \bdso\b or \bccc\b match
                pattern = rf"\b{re.escape(kw)}\b"
                if re.search(pattern, q_lower):
                    words_in_kw = len(kw.split())
                    # High confidence score for exact term match
                    score += words_in_kw * 4 if words_in_kw > 1 else 3
                elif kw in q_lower and len(kw) > 3:
                    score += 1

            if score > max_score and score >= 2:
                max_score = score
                best_template = template

        if not best_template:
            return None

        # Auto-detect year from question if not explicitly supplied
        effective_year = year_filter
        if not effective_year:
            year_match = re.search(r"\b(20[0-2][0-9])\b", question)
            if year_match:
                effective_year = int(year_match.group(1))

        # If a year filter is specified or detected, clone and adjust the SQL query cleanly
        if effective_year:
            adjusted_sql = self._apply_year_filter(best_template.sql, effective_year)
            return QueryTemplate(
                id=best_template.id,
                name=f"{best_template.name} ({effective_year})",
                description=best_template.description,
                keywords=best_template.keywords,
                sql=adjusted_sql,
                chart_type="kpi_card",
                format_type=best_template.format_type,
                x_axis=best_template.x_axis,
                y_axis=best_template.y_axis,
                title=f"{best_template.title} — FY{effective_year}",
            )

        return best_template

    def _apply_year_filter(self, sql: str, year: int) -> str:
        """Inject year filter into the SQL query cleanly using a subquery or CTE to prevent ambiguous columns."""
        clean_sql = sql.strip().rstrip(";")
        if clean_sql.upper().startswith("WITH"):
            return f"""
WITH base_query AS (
{clean_sql}
)
SELECT * FROM base_query
WHERE YEAR(fiscal_year_end) = {year}
ORDER BY fiscal_year_end ASC;
""".strip()
        else:
            return f"""
SELECT * FROM (
{clean_sql}
) AS _report_data
WHERE YEAR(_report_data.fiscal_year_end) = {year}
ORDER BY _report_data.fiscal_year_end ASC;
""".strip()
