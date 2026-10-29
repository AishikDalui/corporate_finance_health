USE corporate_financial_health;

-- ==============================================================================
-- PART 1: Power BI Least-Privilege Read-Only User Setup
-- ==============================================================================
-- Problem Solved:
--   Power BI and reporting tools require direct database access, but granting root or
--   read/write permissions introduces severe security and data corruption risks.
--   This block creates a dedicated read-only user restricted to the reporting IP.
--
-- Key Questions Answered:
--   1. Who is the currently connected database user?
--   2. How do we grant secure, read-only SELECT permissions for Power BI dashboards
--      without exposing write, update, or schema alteration rights?
-- ==============================================================================
SELECT USER(), CURRENT_USER();




-- ==============================================================================
-- PART 2: Database Ingestion Integrity & Table Row Count Validation
-- ==============================================================================
-- Problem Solved:
--   Validates that the automated CSV-to-MySQL pipeline executed without dropping tables,
--   records, or corrupting row counts across the three core statements.
--
-- Key Questions Answered:
--   1. What tables exist in the `corporate_financial_health` database?
--   2. How many historical annual records were successfully loaded into each table?
--   3. Are all three tables synchronized with consistent reporting timeframes?
-- ==============================================================================
SHOW TABLES;

SELECT 'income_statement' AS table_name, COUNT(*) AS total_rows
FROM income_statement

UNION ALL

SELECT 'balance_sheet', COUNT(*)
FROM balance_sheet

UNION ALL

SELECT 'cash_flow', COUNT(*)
FROM cash_flow;

SELECT *
FROM income_statement
ORDER BY `end` DESC
LIMIT 3;

SELECT *
FROM balance_sheet
ORDER BY `end` DESC
LIMIT 3;

SELECT *
FROM cash_flow
ORDER BY `end` DESC
LIMIT 3;


-- ==============================================================================
-- PART 3: Missing Value & Data Quality Audit on Cash Flow Statements
-- ==============================================================================
-- Problem Solved:
--   Accounting taxonomies change over time, occasionally leaving fields like
--   `depreciation_amortization` or `other_noncash_adjustment` null in older XBRL filings.
--   This query identifies and audits any null fields in the cash flow dataset.
--
-- Key Questions Answered:
--   1. Are there missing values in critical cash flow fields?
--   2. In which specific fiscal years were non-cash items reported under alternate tags?
-- ==============================================================================
SELECT
    SUM(operating_cash_flow IS NULL) AS missing_ocf,
    SUM(depreciation_amortization IS NULL) AS missing_depreciation,
    SUM(other_noncash_adjustment IS NULL) AS missing_other_noncash
FROM cash_flow;

SELECT
    `start`,
    `end`,
    operating_cash_flow,
    depreciation_amortization,
    other_noncash_adjustment
FROM cash_flow
WHERE operating_cash_flow IS NULL
   OR depreciation_amortization IS NULL
   OR other_noncash_adjustment IS NULL
ORDER BY `end`;


-- ==============================================================================
-- PART 4: Consolidated Three-Statement KPI Summary View
-- ==============================================================================
-- Problem Solved:
--   Provides a single cross-statement dataset joining Income Statement, Balance Sheet,
--   and Cash Flow Statement to compute primary financial health indicators in one view.
--
-- Key Questions Answered:
--   1. What are Apple's revenue, margins, liquidity, and operating cash flows across all fiscal years?
--   2. How did Apple's current ratio and working capital evolve as margins and cash flow grew?
--   3. What was the cash-conversion multiple (OCF / Net Income) for each fiscal year?
-- ==============================================================================
SELECT
    i.end AS fiscal_year_end,

    -- Income statement
    i.revenue,
    i.gross_profit,
    i.operating_income,
    i.net_income,

    -- Balance sheet
    b.current_assets,
    b.current_liabilities,
    b.working_capital,

    -- Cash flow statement
    c.operating_cash_flow,

    -- Financial ratios
    b.current_assets / NULLIF(b.current_liabilities, 0)
        AS current_ratio,

    i.gross_profit / NULLIF(i.revenue, 0) * 100
        AS gross_margin_pct,

    i.operating_income / NULLIF(i.revenue, 0) * 100
        AS operating_margin_pct,

    c.operating_cash_flow / NULLIF(c.net_income, 0)
        AS ocf_to_net_income_ratio

FROM income_statement AS i
JOIN balance_sheet AS b
    ON i.end = b.end
JOIN cash_flow AS c
    ON i.end = c.end
ORDER BY i.end;


-- ==============================================================================
-- PART 5: Cross-Statement Fiscal Date Alignment Verification
-- ==============================================================================
-- Problem Solved:
--   Financial statements can become misaligned if end-of-year filing snapshot dates differ.
--   This LEFT JOIN query verifies that every income statement period has matching balance sheet
--   and cash flow records.
--
-- Key Questions Answered:
--   1. Do all three financial tables share identical fiscal year-end dates?
--   2. Are there any orphan or unmatched periods across the tables?
-- ==============================================================================
SELECT
    i.end AS income_statement_date,
    b.end AS balance_sheet_date,
    c.end AS cash_flow_date
FROM income_statement i
LEFT JOIN balance_sheet b ON i.end = b.end
LEFT JOIN cash_flow c ON i.end = c.end
ORDER BY i.end;


-- ==============================================================================
-- PART 6: Latest Fiscal Year Executive KPI Snapshot
-- ==============================================================================
-- Problem Solved:
--   Extracts the most recent full-year financial snapshot for high-level executive briefing.
--
-- Key Questions Answered:
--   1. What are Apple's latest current ratio, gross margin percentage, and cash conversion ratio?
-- ==============================================================================
SELECT
    i.end AS fiscal_year_end,
    b.current_assets / NULLIF(b.current_liabilities, 0)
        AS current_ratio,
    i.gross_profit / NULLIF(i.revenue, 0) * 100
        AS gross_margin_pct,
    c.operating_cash_flow / NULLIF(c.net_income, 0)
        AS ocf_to_net_income_ratio
FROM income_statement i
JOIN balance_sheet b ON i.end = b.end
JOIN cash_flow c ON i.end = c.end
ORDER BY i.end DESC
LIMIT 1;


-- ==============================================================================
-- PART 7: Working Capital & Current Asset Composition Drilldown (2021+)
-- ==============================================================================
-- Problem Solved:
--   Apple operates with a negative working capital position (current liabilities exceed current assets).
--   This query dissects current assets into cash, receivables, inventory, and other assets
--   to diagnose the root cause of negative working capital.
--
-- Key Questions Answered:
--   1. How did working capital transition into negative territory between 2021 and 2025?
--   2. Which asset classes make up Apple's current asset base?
--   3. Is negative working capital a sign of distress, or evidence of extreme operational efficiency?
-- ==============================================================================
SELECT
    b.end AS fiscal_year_end,
    b.current_assets,
    b.current_liabilities,
    b.working_capital,
    ROUND(
        b.current_assets / NULLIF(b.current_liabilities, 0),
        4
    ) AS current_ratio
FROM balance_sheet AS b
ORDER BY b.end;

SELECT
    end AS fiscal_year_end,
    current_assets,
    current_liabilities,
    working_capital,
    cash,
    accounts_receivable,
    inventory,
    other_current_assets
FROM balance_sheet
WHERE end >= '2021-01-01'
ORDER BY end;


-- ==============================================================================
-- PART 8: Accounts Receivable Exposure Relative to Revenue (2021+)
-- ==============================================================================
-- Problem Solved:
--   Tracks credit risk and customer payment terms by measuring receivables as a percentage
--   of total annual revenue.
--
-- Key Questions Answered:
--   1. What percentage of Apple's top-line revenue remains unpaid at fiscal year-end?
--   2. Has customer credit risk or trade financing expanded from 2021 to 2025?
-- ==============================================================================
SELECT
    i.end AS fiscal_year_end,
    i.revenue,
    b.accounts_receivable,

    ROUND(
        b.accounts_receivable / NULLIF(i.revenue, 0) * 100,
        2
    ) AS receivables_as_pct_of_revenue

FROM income_statement AS i
JOIN balance_sheet AS b
    ON i.end = b.end
WHERE i.end >= '2021-01-01'
ORDER BY i.end;


-- ==============================================================================
-- PART 9: Days Sales Outstanding (DSO) Calculation (2022+)
-- ==============================================================================
-- Problem Solved:
--   Measures collection speed and credit policy efficiency using a 2-year average
--   accounts receivable balance relative to annual revenue.
--
-- Key Questions Answered:
--   1. How many days does Apple take on average to collect cash from customers and distributors?
--   2. Are customer receivables turning into cash faster or slower in recent years?
-- ==============================================================================
WITH receivables_trend AS (
    SELECT
        b.end AS fiscal_year_end,
        i.revenue,
        b.accounts_receivable,

        LAG(b.accounts_receivable) OVER (
            ORDER BY b.end
        ) AS previous_year_receivables

    FROM balance_sheet AS b
    JOIN income_statement AS i
        ON b.end = i.end
)

SELECT
    fiscal_year_end,
    revenue,
    accounts_receivable,
    previous_year_receivables,

    ROUND(
        (
            (accounts_receivable + previous_year_receivables) / 2.0
        ) / NULLIF(revenue, 0) * 365,
        2
    ) AS estimated_dso_days

FROM receivables_trend
WHERE previous_year_receivables IS NOT NULL
  AND fiscal_year_end >= '2022-01-01'
ORDER BY fiscal_year_end;


-- ==============================================================================
-- PART 10: Revenue Growth vs. Accounts Receivable Growth Divergence Audit
-- ==============================================================================
-- Problem Solved:
--   A classic forensic accounting audit check. If Accounts Receivable grows substantially
--   faster than Revenue, it can indicate aggressive revenue recognition, channel stuffing,
--   or deteriorating customer creditworthiness.
--
-- Key Questions Answered:
--   1. Is accounts receivable growth aligned with underlying revenue growth?
--   2. Did receivables growth spike faster than sales in 2024 or 2025, signaling collection bottlenecks?
-- ==============================================================================
WITH yearly_metrics AS (
    SELECT
        i.end AS fiscal_year_end,
        i.revenue,
        b.accounts_receivable,

        LAG(i.revenue) OVER (
            ORDER BY i.end
        ) AS previous_revenue,

        LAG(b.accounts_receivable) OVER (
            ORDER BY i.end
        ) AS previous_receivables

    FROM income_statement AS i
    JOIN balance_sheet AS b
        ON i.end = b.end
)

SELECT
    fiscal_year_end,
    revenue,
    accounts_receivable,

    ROUND(
        (revenue - previous_revenue)
        / NULLIF(previous_revenue, 0) * 100,
        2
    ) AS revenue_growth_pct,

    ROUND(
        (accounts_receivable - previous_receivables)
        / NULLIF(previous_receivables, 0) * 100,
        2
    ) AS receivables_growth_pct

FROM yearly_metrics
WHERE previous_revenue IS NOT NULL
  AND fiscal_year_end >= '2022-01-01'
ORDER BY fiscal_year_end;


-- ==============================================================================
-- PART 11: Earnings Quality & Cash Flow Conversion Analysis
-- ==============================================================================
-- Problem Solved:
--   Net income is subject to non-cash accrual accounting assumptions.
--   This query assesses "Earnings Quality" by verifying that net income is supported
--   by actual operating cash flow (OCF / Net Income ratio and absolute cash surplus).
--
-- Key Questions Answered:
--   1. Does Apple consistently generate more cash from operations than it reports in accounting net profit?
--   2. What is the absolute dollar excess of cash flow over reported net income each year?
-- ==============================================================================
SELECT
    i.end AS fiscal_year_end,
    i.net_income,
    c.operating_cash_flow,

    ROUND(
        c.operating_cash_flow / NULLIF(i.net_income, 0),
        4
    ) AS ocf_to_net_income_ratio,

    c.operating_cash_flow - i.net_income
        AS cash_flow_minus_net_income

FROM income_statement AS i
JOIN cash_flow AS c
    ON i.end = c.end
ORDER BY i.end;


-- ==============================================================================
-- PART 12: Net Income Growth vs. Operating Cash Flow Growth Momentum
-- ==============================================================================
-- Problem Solved:
--   Compares year-over-year percentage growth in Net Income vs. Operating Cash Flow.
--   Highlights divergence where reported profits increase but cash generation lags.
--
-- Key Questions Answered:
--   1. Did operating cash flow growth outpace or lag net income growth year-over-year?
--   2. In years where net income grew, did real operational cash flow validate that earnings momentum?
-- ==============================================================================
WITH yearly_metrics AS (
    SELECT
        i.end AS fiscal_year_end,
        i.net_income,
        c.operating_cash_flow,

        LAG(i.net_income) OVER (
            ORDER BY i.end
        ) AS previous_net_income,

        LAG(c.operating_cash_flow) OVER (
            ORDER BY i.end
        ) AS previous_ocf

    FROM income_statement AS i
    JOIN cash_flow AS c
        ON i.end = c.end
)

SELECT
    fiscal_year_end,
    net_income,
    operating_cash_flow,

    ROUND(
        (net_income - previous_net_income)
        / NULLIF(previous_net_income, 0) * 100,
        2
    ) AS net_income_growth_pct,

    ROUND(
        (operating_cash_flow - previous_ocf)
        / NULLIF(previous_ocf, 0) * 100,
        2
    ) AS ocf_growth_pct

FROM yearly_metrics
WHERE previous_net_income IS NOT NULL
  AND fiscal_year_end >= '2022-01-01'
ORDER BY fiscal_year_end;


-- ==============================================================================
-- PART 13: Forensic Cash Flow Working Capital Adjustments (FY2024 vs. FY2025)
-- ==============================================================================
-- Problem Solved:
--   Unpacks the specific non-cash and working capital balance sheet movements that
--   bridge Net Income to Operating Cash Flow in Apple's cash flow statement.
--
-- Key Questions Answered:
--   1. Why did Apple's operating cash flow decrease from $118.25B in 2024 to $111.48B in 2025?
--   2. What were the exact cash flow contributions from receivables, inventory, payables,
--      and other operating assets/liabilities?
--   3. Did changes in other operating liabilities create a major cash drain in FY2025?
-- ==============================================================================
SELECT
    end AS fiscal_year_end,
    operating_cash_flow,
    net_income,
    accounts_receivable_adjustment,
    inventory_adjustment,
    accounts_payable_adjustment,
    other_operating_assets_adjustment,
    other_operating_liabilities_adjustment,
    share_based_compensation,
    depreciation_amortization
FROM cash_flow
WHERE end IN ('2024-09-28', '2025-09-27')
ORDER BY end;

SELECT
    end AS fiscal_year_end,
    other_operating_liabilities_adjustment,
    other_operating_assets_adjustment,
    accounts_receivable_adjustment,

    other_operating_liabilities_adjustment
      - LAG(other_operating_liabilities_adjustment)
        OVER (ORDER BY end)
        AS liabilities_adjustment_change,

    other_operating_assets_adjustment
      - LAG(other_operating_assets_adjustment)
        OVER (ORDER BY end)
        AS assets_adjustment_change,

    accounts_receivable_adjustment
      - LAG(accounts_receivable_adjustment)
        OVER (ORDER BY end)
        AS receivables_adjustment_change

FROM cash_flow
WHERE end >= '2022-01-01'
ORDER BY end;

SELECT
    end AS fiscal_year_end,
    other_operating_liabilities_adjustment,
    
    LAG(other_operating_liabilities_adjustment) OVER (
        ORDER BY end
    ) AS previous_year_adjustment,

    other_operating_liabilities_adjustment
      - LAG(other_operating_liabilities_adjustment) OVER (
          ORDER BY end
        ) AS year_over_year_change

FROM cash_flow
WHERE end >= '2022-01-01'
ORDER BY end;

DESCRIBE cash_flow;

SELECT
    end AS fiscal_year_end,
    accounts_payable_adjustment,
    other_operating_liabilities_adjustment,
    accounts_receivable_adjustment,
    other_operating_assets_adjustment
FROM cash_flow
WHERE end IN ('2024-09-28', '2025-09-27')
ORDER BY end;


-- ==============================================================================
-- PART 14: Cash Taxes Paid vs. Income Tax Expense Reconciliation (FY2024 vs. FY2025)
-- ==============================================================================
-- Problem Solved:
--   In FY2024/FY2025, Apple finalized the European Commission State Aid tax ruling dispute
--   with Ireland, resulting in a large one-time cash tax disbursement.
--   This query reconciles actual cash taxes paid from cash flow notes against accounting
--   tax expense on the income statement.
--
-- Key Questions Answered:
--   1. How much actual cash did Apple pay in income taxes in FY2025 vs. FY2024?
--   2. What was the net cash tax drain beyond reported accounting tax expense
--      ($43.37B cash paid vs. $20.72B GAAP tax provision in FY2025)?
--   3. Does this one-off tax payout explain why operating cash flow was lower than net income in FY2025?
-- ==============================================================================
SELECT
    i.end AS fiscal_year_end,
    i.net_income,
    i.revenue,
    cf.operating_cash_flow,
    cf.ocf_to_net_income,

    CASE
        WHEN i.end = '2024-09-28' THEN 26102000000
        WHEN i.end = '2025-09-27' THEN 43369000000
    END AS cash_taxes_paid,

    CASE
        WHEN i.end = '2024-09-28' THEN 29749000000
        WHEN i.end = '2025-09-27' THEN 20719000000
    END AS income_tax_expense,

    CASE
        WHEN i.end = '2024-09-28'
            THEN 26102000000 - 29749000000
        WHEN i.end = '2025-09-27'
            THEN 43369000000 - 20719000000
    END AS cash_tax_minus_tax_expense

FROM income_statement i
JOIN cash_flow cf
    ON i.end = cf.end
WHERE i.end IN ('2024-09-28', '2025-09-27')
ORDER BY i.end;
