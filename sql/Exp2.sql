USE corporate_financial_health;

-- ==============================================================================
-- QUERY 1: Multi-Stage Profitability Margins Over Time
-- ==============================================================================
-- Problem Solved:
--   Raw dollar figures for Revenue and Net Income don't reflect operational efficiency.
--   This query evaluates Apple's conversion efficiency at every tier of the income statement
--   by calculating percentage margins across fiscal years.
--
-- Key Questions Answered:
--   1. What proportion of revenue is retained after accounting for direct production costs (Gross Margin)?
--   2. How effectively does Apple manage overhead and operational costs to yield Operating Income (Operating Margin)?
--   3. What is the ultimate bottom-line profit margin after all interest, taxes, and expenses (Net Margin)?
-- ==============================================================================
SELECT
    end AS fiscal_year_end,
    revenue,
    gross_profit,
    operating_income,
    net_income,

    ROUND(gross_profit / NULLIF(revenue, 0) * 100, 2)
        AS gross_margin_pct,

    ROUND(operating_income / NULLIF(revenue, 0) * 100, 2)
        AS operating_margin_pct,

    ROUND(net_income / NULLIF(revenue, 0) * 100, 2)
        AS net_margin_pct

FROM income_statement
ORDER BY end;


-- ==============================================================================
-- QUERY 2: Year-over-Year (YoY) Margin Volatility & Expansion/Contraction
-- ==============================================================================
-- Problem Solved:
--   Static margin percentages do not show whether performance is improving or declining.
--   Using window functions (LAG), this query measures the exact percentage-point (pp)
--   expansion or compression of margins from one fiscal year to the next.
--
-- Key Questions Answered:
--   1. Did Apple experience margin expansion or margin compression in each fiscal year?
--   2. Are cost increases in supply chain/production outpacing price increases (gross margin change)?
--   3. Is operating leverage expanding operating margins faster than gross margins?
-- ==============================================================================
WITH margin_trends AS (
    SELECT
        end AS fiscal_year_end,
        gross_margin_pct,
        operating_margin_pct,
        net_margin_pct,

        LAG(gross_margin_pct) OVER (
            ORDER BY end
        ) AS previous_gross_margin,

        LAG(operating_margin_pct) OVER (
            ORDER BY end
        ) AS previous_operating_margin,

        LAG(net_margin_pct) OVER (
            ORDER BY end
        ) AS previous_net_margin

    FROM income_statement
)

SELECT
    fiscal_year_end,

    ROUND(
        gross_margin_pct - previous_gross_margin, 2
    ) AS gross_margin_change_pp,

    ROUND(
        operating_margin_pct - previous_operating_margin, 2
    ) AS operating_margin_change_pp,

    ROUND(
        net_margin_pct - previous_net_margin, 2
    ) AS net_margin_change_pp

FROM margin_trends
WHERE previous_gross_margin IS NOT NULL
ORDER BY fiscal_year_end;


-- ==============================================================================
-- QUERY 3: Balance Sheet Schema Inspection & Solvency/Leverage Analysis
-- ==============================================================================
-- Problem Solved:
--   Monitors capital structure and financial leverage to identify insolvency risk
--   caused by high liabilities relative to the equity base and total assets.
--
-- Key Questions Answered:
--   1. What is Apple's liabilities-to-equity ratio, and how has it expanded due to aggressive share repurchases?
--   2. What percentage of Apple's total asset base is funded via obligations and liabilities vs. equity?
-- ==============================================================================
DESCRIBE balance_sheet;

SELECT
    end AS fiscal_year_end,
    total_assets,
    total_liabilities,
    stockholders_equity,

    ROUND(
        total_liabilities / NULLIF(stockholders_equity, 0),
        4
    ) AS liabilities_to_equity_ratio,

    ROUND(
        total_liabilities / NULLIF(total_assets, 0) * 100,
        2
    ) AS liabilities_to_assets_pct

FROM balance_sheet
ORDER BY end;


-- ==============================================================================
-- QUERY 4: Funded Debt Capital Structure & Financial Risk Breakdown
-- ==============================================================================
-- Problem Solved:
--   Total liabilities include operational obligations (accounts payable, deferred revenue, accrued expenses).
--   This query isolates contractual interest-bearing debt (commercial paper + term debt)
--   for recent fiscal years to analyze true solvency risk and balance sheet gearing.
--
-- Key Questions Answered:
--   1. What is Apple's true debt-to-equity multiple when evaluating contractual interest-bearing debt?
--   2. What proportion of total liabilities is funded debt vs. operational trade liabilities?
--   3. What percentage of Apple's total assets is encumbered by interest-bearing borrowings?
-- ==============================================================================
WITH debt_data AS (
    SELECT
        '2024-09-28' AS fiscal_year_end,
        106629000000 AS total_debt

    UNION ALL

    SELECT
        '2025-09-27',
        98657000000
)

SELECT
    b.end AS fiscal_year_end,
    d.total_debt,
    b.stockholders_equity,
    b.total_liabilities,
    b.total_assets,

    ROUND(
        d.total_debt / NULLIF(b.stockholders_equity, 0),
        4
    ) AS debt_to_equity_ratio,

    ROUND(
        d.total_debt / NULLIF(b.total_assets, 0) * 100,
        2
    ) AS debt_to_assets_pct,

    ROUND(
        d.total_debt / NULLIF(b.total_liabilities, 0) * 100,
        2
    ) AS debt_as_pct_of_liabilities

FROM balance_sheet b
JOIN debt_data d
    ON b.end = d.fiscal_year_end
ORDER BY b.end;


-- ==============================================================================
-- QUERY 5: Master Cross-Statement Financial Health Dashboard
-- ==============================================================================
-- Problem Solved:
--   Financial health cannot be evaluated by looking at one statement in isolation.
--   This query joins the Income Statement, Balance Sheet, and Cash Flow Statement
--   into a single analytical dataset spanning profitability, liquidity, solvency, and cash conversion.
--
-- Key Questions Answered:
--   1. Are bottom-line profits converting into actual operating cash flows (OCF-to-Net Income)?
--   2. How do current ratio and working capital behave relative to revenue and net income growth?
--   3. Does the company maintain adequate liquidity while scaling revenues and expanding margins?
-- ==============================================================================
SELECT
    i.end AS fiscal_year_end,
    i.revenue,
    i.gross_profit,
    i.operating_income,
    i.net_income,

    b.total_assets,
    b.total_liabilities,
    b.stockholders_equity,
    b.current_assets,
    b.current_liabilities,
    b.working_capital,
    b.current_ratio,

    cf.operating_cash_flow,
    cf.ocf_to_net_income,

    ROUND(
        i.gross_profit / NULLIF(i.revenue, 0) * 100,
        2
    ) AS gross_margin_pct,

    ROUND(
        i.operating_income / NULLIF(i.revenue, 0) * 100,
        2
    ) AS operating_margin_pct,

    ROUND(
        i.net_income / NULLIF(i.revenue, 0) * 100,
        2
    ) AS net_margin_pct,

    ROUND(
        b.total_liabilities / NULLIF(b.total_assets, 0) * 100,
        2
    ) AS liabilities_to_assets_pct,

    ROUND(
        b.total_liabilities /
        NULLIF(b.stockholders_equity, 0),
        4
    ) AS liabilities_to_equity_ratio

FROM income_statement AS i
INNER JOIN balance_sheet AS b
    ON i.end = b.end
INNER JOIN cash_flow AS cf
    ON i.end = cf.end
ORDER BY i.end;


-- ==============================================================================
-- QUERY 6: Inventory Turnover Efficiency & Days Inventory Outstanding (DIO)
-- ==============================================================================
-- Problem Solved:
--   Using year-end inventory alone can distort turnover calculations due to seasonal peaks.
--   This query calculates Days Inventory Outstanding (DIO) using average inventory
--   (average of current year and prior year) relative to Cost of Goods Sold (COGS).
--
-- Key Questions Answered:
--   1. How many days on average does inventory sit before being converted into a finished sale?
--   2. How lean is Apple's inventory management compared to hardware and electronics manufacturing benchmarks?
--   3. Is inventory buildup tying up excessive working capital?
-- ==============================================================================
WITH inventory_metrics AS (
    SELECT
        b.end AS fiscal_year_end,
        b.inventory,
        i.cogs,

        LAG(b.inventory) OVER (
            ORDER BY b.end
        ) AS previous_inventory

    FROM balance_sheet b
    JOIN income_statement i
        ON b.end = i.end
)

SELECT
    fiscal_year_end,
    inventory,
    previous_inventory,
    cogs,

    ROUND(
        ((inventory + previous_inventory) / 2.0)
        / NULLIF(cogs, 0) * 365,
        2
    ) AS estimated_dio_days

FROM inventory_metrics
WHERE previous_inventory IS NOT NULL
ORDER BY fiscal_year_end;

DESCRIBE balance_sheet;
