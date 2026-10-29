-- ==============================================================================
-- PART 1: Staging Trade Accounts Payable Data
-- ==============================================================================
-- Problem Solved:
--   Accounts Payable (AP) represents trade credit provided by component suppliers and
--   contract manufacturers (e.g., Foxconn). Because AP wasn't initially included in the
--   generic balance sheet table, this query creates and populates a dedicated historical
--   accounts payable table from Apple's 10-K filings (FY2016–FY2025).
--
-- Key Questions Answered:
--   1. What is Apple's trade credit balance owed to suppliers at each fiscal year-end?
--   2. How has Apple's reliance on supplier trade financing scaled alongside revenue growth?
-- ==============================================================================
CREATE TABLE accounts_payable (
    `end` DATE PRIMARY KEY,
    accounts_payable BIGINT
);

SELECT COUNT(*) AS total_rows
FROM accounts_payable;

INSERT INTO accounts_payable (`end`, accounts_payable)
VALUES
('2016-09-24', 37294000000),
('2017-09-30', 44242000000),
('2018-09-29', 55888000000),
('2019-09-28', 46236000000),
('2020-09-26', 42296000000),
('2021-09-25', 54763000000),
('2022-09-24', 64115000000),
('2023-09-30', 62611000000),
('2024-09-28', 68960000000),
('2025-09-27', 69860000000);

SELECT *
FROM accounts_payable
ORDER BY `end`;


-- ==============================================================================
-- PART 2: Days Payable Outstanding (DPO) Calculation
-- ==============================================================================
-- Problem Solved:
--   Measures how effectively Apple leverages supplier financing terms.
--   Calculates Days Payable Outstanding (DPO) using average accounts payable
--   divided by Cost of Goods Sold (COGS) multiplied by 365 days.
--
-- Key Questions Answered:
--   1. How many days on average does Apple take to pay its trade vendors and suppliers?
--   2. Is Apple using supplier credit as an interest-free source of operational working capital?
--   3. Are supplier payment terms stretching longer or tightening over time?
-- ==============================================================================
WITH payable_metrics AS (
    SELECT
        b.`end` AS fiscal_year_end,
        a.accounts_payable,
        i.cogs,
        LAG(a.accounts_payable) OVER (
            ORDER BY b.`end`
        ) AS previous_accounts_payable
    FROM balance_sheet b
    JOIN accounts_payable a
        ON b.`end` = a.`end`
    JOIN income_statement i
        ON b.`end` = i.`end`
)
SELECT
    fiscal_year_end,
    accounts_payable,
    previous_accounts_payable,
    cogs,
    ROUND(
        (
            (accounts_payable + previous_accounts_payable) / 2.0
        ) / NULLIF(cogs, 0) * 365,
        2
    ) AS estimated_dpo_days
FROM payable_metrics
WHERE previous_accounts_payable IS NOT NULL
ORDER BY fiscal_year_end;


-- ==============================================================================
-- PART 3: Comprehensive Cash Conversion Cycle (CCC = DSO + DIO - DPO)
-- ==============================================================================
-- Problem Solved:
--   Assesses complete operational working capital velocity by synthesizing:
--     • Days Sales Outstanding (DSO): Customer collection time
--     • Days Inventory Outstanding (DIO): Inventory holding time
--     • Days Payable Outstanding (DPO): Supplier payment time
--   Computes the overall Cash Conversion Cycle (CCC).
--
-- Key Questions Answered:
--   1. How many days does cash remain tied up in Apple's operational cycle?
--   2. Does Apple operate with a negative Cash Conversion Cycle (getting paid by customers
--      long before paying suppliers)?
--   3. How does Apple's supply chain power enable it to fund ongoing operations with supplier cash?
-- ==============================================================================
WITH operating_metrics AS (
    SELECT
        b.`end` AS fiscal_year_end,
        b.accounts_receivable,
        b.inventory,
        a.accounts_payable,
        i.revenue,
        i.cogs,

        LAG(b.accounts_receivable) OVER (
            ORDER BY b.`end`
        ) AS previous_ar,

        LAG(b.inventory) OVER (
            ORDER BY b.`end`
        ) AS previous_inventory,

        LAG(a.accounts_payable) OVER (
            ORDER BY b.`end`
        ) AS previous_ap

    FROM balance_sheet b
    JOIN income_statement i
        ON b.`end` = i.`end`
    JOIN accounts_payable a
        ON b.`end` = a.`end`
)
SELECT
    fiscal_year_end,

    ROUND(
        ((accounts_receivable + previous_ar) / 2.0)
        / NULLIF(revenue, 0) * 365,
        2
    ) AS estimated_dso_days,

    ROUND(
        ((inventory + previous_inventory) / 2.0)
        / NULLIF(cogs, 0) * 365,
        2
    ) AS estimated_dio_days,

    ROUND(
        ((accounts_payable + previous_ap) / 2.0)
        / NULLIF(cogs, 0) * 365,
        2
    ) AS estimated_dpo_days,

    ROUND(
        (
            ((accounts_receivable + previous_ar) / 2.0)
            / NULLIF(revenue, 0) * 365
        )
        +
        (
            ((inventory + previous_inventory) / 2.0)
            / NULLIF(cogs, 0) * 365
        )
        -
        (
            ((accounts_payable + previous_ap) / 2.0)
            / NULLIF(cogs, 0) * 365
        ),
        2
    ) AS estimated_ccc_days

FROM operating_metrics
WHERE previous_ar IS NOT NULL
  AND previous_inventory IS NOT NULL
  AND previous_ap IS NOT NULL
ORDER BY fiscal_year_end;


-- ==============================================================================
-- PART 4: Year-over-Year (YoY) Changes in Operating Ratios & CCC
-- ==============================================================================
-- Problem Solved:
--   Tracks the yearly delta across all three operational components (DSO, DIO, DPO)
--   and the net CCC to pinpoint the exact driver of changes in working capital efficiency.
--
-- Key Questions Answered:
--   1. Did customer payment collections accelerate or slow down year-over-year (DSO change)?
--   2. Did inventory turnover speed up or suffer bottlenecks (DIO change)?
--   3. Did supplier payment extensions expand Apple's cash cushion (DPO change)?
--   4. Did Apple's overall Cash Conversion Cycle become more or less advantageous year-over-year?
-- ==============================================================================
WITH annual_metrics AS (
    SELECT
        b.`end` AS fiscal_year_end,
        b.accounts_receivable,
        b.inventory,
        a.accounts_payable,
        i.revenue,
        i.cogs,
        LAG(b.accounts_receivable) OVER (
            ORDER BY b.`end`
        ) AS previous_ar,
        LAG(b.inventory) OVER (
            ORDER BY b.`end`
        ) AS previous_inventory,
        LAG(a.accounts_payable) OVER (
            ORDER BY b.`end`
        ) AS previous_ap
    FROM balance_sheet b
    JOIN income_statement i
        ON b.`end` = i.`end`
    JOIN accounts_payable a
        ON b.`end` = a.`end`
),
ratios AS (
    SELECT
        fiscal_year_end,
        ROUND(
            ((accounts_receivable + previous_ar) / 2.0)
            / NULLIF(revenue, 0) * 365, 2
        ) AS dso,
        ROUND(
            ((inventory + previous_inventory) / 2.0)
            / NULLIF(cogs, 0) * 365, 2
        ) AS dio,
        ROUND(
            ((accounts_payable + previous_ap) / 2.0)
            / NULLIF(cogs, 0) * 365, 2
        ) AS dpo
    FROM annual_metrics
    WHERE previous_ar IS NOT NULL
      AND previous_inventory IS NOT NULL
      AND previous_ap IS NOT NULL
)
SELECT
    fiscal_year_end,
    dso,
    dio,
    dpo,
    ROUND(dso + dio - dpo, 2) AS ccc,
    ROUND(dso - LAG(dso) OVER (
        ORDER BY fiscal_year_end
    ), 2) AS dso_change,
    ROUND(dio - LAG(dio) OVER (
        ORDER BY fiscal_year_end
    ), 2) AS dio_change,
    ROUND(dpo - LAG(dpo) OVER (
        ORDER BY fiscal_year_end
    ), 2) AS dpo_change,
    ROUND(
        (dso + dio - dpo)
        - LAG(dso + dio - dpo) OVER (
            ORDER BY fiscal_year_end
        ), 2
    ) AS ccc_change
FROM ratios
ORDER BY fiscal_year_end;


-- ==============================================================================
-- PART 5: Automated Diagnostic Classification of Working Capital Shifts
-- ==============================================================================
-- Problem Solved:
--   Translates numerical changes into human-readable business observations
--   using CASE logic for executive reporting and operational reviews.
--
-- Key Questions Answered:
--   1. What is the qualitative operational narrative for customer collections in each year?
--   2. Are inventory buffers building up or turning over leaner?
--   3. Are suppliers receiving faster or slower payments?
-- ==============================================================================
WITH annual_metrics AS (
    SELECT
        b.`end` AS fiscal_year_end,
        b.accounts_receivable,
        b.inventory,
        a.accounts_payable,
        i.revenue,
        i.cogs,

        LAG(b.accounts_receivable) OVER (
            ORDER BY b.`end`
        ) AS previous_ar,

        LAG(b.inventory) OVER (
            ORDER BY b.`end`
        ) AS previous_inventory,

        LAG(a.accounts_payable) OVER (
            ORDER BY b.`end`
        ) AS previous_ap

    FROM balance_sheet b
    JOIN income_statement i
        ON b.`end` = i.`end`
    JOIN accounts_payable a
        ON b.`end` = a.`end`
),

ratios AS (
    SELECT
        fiscal_year_end,

        accounts_receivable,
        inventory,
        accounts_payable,

        ROUND(
            ((accounts_receivable + previous_ar) / 2.0)
            / NULLIF(revenue, 0) * 365, 2
        ) AS dso,

        ROUND(
            ((inventory + previous_inventory) / 2.0)
            / NULLIF(cogs, 0) * 365, 2
        ) AS dio,

        ROUND(
            ((accounts_payable + previous_ap) / 2.0)
            / NULLIF(cogs, 0) * 365, 2
        ) AS dpo

    FROM annual_metrics
    WHERE previous_ar IS NOT NULL
      AND previous_inventory IS NOT NULL
      AND previous_ap IS NOT NULL
),

ccc_metrics AS (
    SELECT
        fiscal_year_end,
        accounts_receivable,
        inventory,
        accounts_payable,
        dso,
        dio,
        dpo,
        dso + dio - dpo AS ccc
    FROM ratios
),

trend_metrics AS (
    SELECT
        *,
        LAG(dso) OVER (
            ORDER BY fiscal_year_end
        ) AS previous_dso,

        LAG(dio) OVER (
            ORDER BY fiscal_year_end
        ) AS previous_dio,

        LAG(dpo) OVER (
            ORDER BY fiscal_year_end
        ) AS previous_dpo,

        LAG(ccc) OVER (
            ORDER BY fiscal_year_end
        ) AS previous_ccc
    FROM ccc_metrics
)

SELECT
    fiscal_year_end,

    ROUND(dso, 2) AS dso_days,
    ROUND(dio, 2) AS dio_days,
    ROUND(dpo, 2) AS dpo_days,
    ROUND(ccc, 2) AS ccc_days,

    ROUND(dso - previous_dso, 2) AS dso_change,
    ROUND(dio - previous_dio, 2) AS dio_change,
    ROUND(dpo - previous_dpo, 2) AS dpo_change,
    ROUND(ccc - previous_ccc, 2) AS ccc_change,

    CASE
        WHEN dso - previous_dso > 0
            THEN 'Receivables days increased'
        WHEN dso - previous_dso < 0
            THEN 'Receivables days decreased'
        ELSE 'No change in receivables days'
    END AS receivables_observation,

    CASE
        WHEN dio - previous_dio > 0
            THEN 'Inventory days increased'
        WHEN dio - previous_dio < 0
            THEN 'Inventory days decreased'
        ELSE 'No change in inventory days'
    END AS inventory_observation,

    CASE
        WHEN dpo - previous_dpo > 0
            THEN 'Supplier payment days increased'
        WHEN dpo - previous_dpo < 0
            THEN 'Supplier payment days decreased'
        ELSE 'No change in supplier payment days'
    END AS supplier_payment_observation

FROM trend_metrics
ORDER BY fiscal_year_end;


-- ==============================================================================
-- PART 6: Executive-Grade Working Capital Analysis with Negative CCC Semantics
-- ==============================================================================
-- Problem Solved:
--   For companies with negative CCC like Apple, a decrease in CCC is beneficial
--   (cash conversion becomes MORE negative, meaning suppliers finance more of the business).
--   This query adds explicit business logic handling negative CCC transitions and null-safe prior year comparisons.
--
-- Key Questions Answered:
--   1. Did Apple's working capital financing advantage widen (more negative CCC) or compress?
--   2. How do individual changes in DSO, DIO, and DPO interact to shape the overall CCC trend?
--   3. Are all boundary conditions (e.g. first year lacking historical comparison) gracefully handled?
-- ==============================================================================
WITH annual_metrics AS (
    SELECT
        b.`end` AS fiscal_year_end,
        b.accounts_receivable,
        b.inventory,
        a.accounts_payable,
        i.revenue,
        i.cogs,

        LAG(b.accounts_receivable) OVER (
            ORDER BY b.`end`
        ) AS previous_ar,

        LAG(b.inventory) OVER (
            ORDER BY b.`end`
        ) AS previous_inventory,

        LAG(a.accounts_payable) OVER (
            ORDER BY b.`end`
        ) AS previous_ap

    FROM balance_sheet b
    INNER JOIN income_statement i
        ON b.`end` = i.`end`
    INNER JOIN accounts_payable a
        ON b.`end` = a.`end`
),

ratios AS (
    SELECT
        fiscal_year_end,

        accounts_receivable,
        inventory,
        accounts_payable,

        previous_ar,
        previous_inventory,
        previous_ap,

        revenue,
        cogs,

        (
            ((accounts_receivable + previous_ar) / 2.0)
            / NULLIF(revenue, 0) * 365
        ) AS dso,

        (
            ((inventory + previous_inventory) / 2.0)
            / NULLIF(cogs, 0) * 365
        ) AS dio,

        (
            ((accounts_payable + previous_ap) / 2.0)
            / NULLIF(cogs, 0) * 365
        ) AS dpo

    FROM annual_metrics
),

ccc_metrics AS (
    SELECT
        *,
        dso + dio - dpo AS ccc
    FROM ratios
),

trend_metrics AS (
    SELECT
        *,

        LAG(dso) OVER (
            ORDER BY fiscal_year_end
        ) AS previous_dso,

        LAG(dio) OVER (
            ORDER BY fiscal_year_end
        ) AS previous_dio,

        LAG(dpo) OVER (
            ORDER BY fiscal_year_end
        ) AS previous_dpo,

        LAG(ccc) OVER (
            ORDER BY fiscal_year_end
        ) AS previous_ccc

    FROM ccc_metrics
)

SELECT
    fiscal_year_end,

    ROUND(dso, 2) AS dso_days,
    ROUND(dio, 2) AS dio_days,
    ROUND(dpo, 2) AS dpo_days,
    ROUND(ccc, 2) AS ccc_days,

    ROUND(dso - previous_dso, 2) AS dso_change,
    ROUND(dio - previous_dio, 2) AS dio_change,
    ROUND(dpo - previous_dpo, 2) AS dpo_change,
    ROUND(ccc - previous_ccc, 2) AS ccc_change,

    CASE
        WHEN previous_dso IS NULL
            THEN 'No prior-year comparison'
        WHEN dso > previous_dso
            THEN 'Receivables days increased'
        WHEN dso < previous_dso
            THEN 'Receivables days decreased'
        ELSE 'No change in receivables days'
    END AS receivables_observation,

    CASE
        WHEN previous_dio IS NULL
            THEN 'No prior-year comparison'
        WHEN dio > previous_dio
            THEN 'Inventory days increased'
        WHEN dio < previous_dio
            THEN 'Inventory days decreased'
        ELSE 'No change in inventory days'
    END AS inventory_observation,

    CASE
        WHEN previous_dpo IS NULL
            THEN 'No prior-year comparison'
        WHEN dpo > previous_dpo
            THEN 'Supplier payment days increased'
        WHEN dpo < previous_dpo
            THEN 'Supplier payment days decreased'
        ELSE 'No change in supplier payment days'
    END AS supplier_payment_observation,

    CASE
        WHEN previous_ccc IS NULL
            THEN 'No prior-year comparison'
        WHEN ccc > previous_ccc
            THEN 'CCC became less negative or more positive'
        WHEN ccc < previous_ccc
            THEN 'CCC became more negative'
        ELSE 'No change in CCC'
    END AS ccc_observation

FROM trend_metrics
WHERE previous_ar IS NOT NULL
  AND previous_inventory IS NOT NULL
  AND previous_ap IS NOT NULL
  AND dso IS NOT NULL
  AND dio IS NOT NULL
  AND dpo IS NOT NULL

ORDER BY fiscal_year_end;
