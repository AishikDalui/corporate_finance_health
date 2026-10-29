# Data Dictionary: Corporate Financial Health Analysis

## Overview
This document defines the schema, key metrics, data types, descriptions, and business logic for the datasets used in the Corporate Financial Health project. The data spans company metadata, balance sheets, income statements, cash flow statements, and computed financial health ratios.

> **Primary Key Architecture**: In entity master tables (e.g., `company_metadata`), `company_id` serves as a standalone Primary Key. For all time-series financial datasets (`income_statement`, `balance_sheet`, `cash_flow`, `financial_ratios`), a single company has multiple reporting periods across fiscal years. Thus, the logical composite primary key is **`(company_id, fiscal_year, fiscal_quarter)`**.

> **Unit & Currency Standardization Convention**:
> - **Monetary Values**: All reported financial statement amounts across clean storage tables (`income_statement`, `balance_sheet`, `cash_flow`) are stored in **unscaled base functional currency units (USD)** (e.g., `416161000000` for $416.161 billion). Storing unscaled integers/decimals in storage and SQL tables avoids floating-point precision loss and ensures clean cross-table joins.
> - **Ratios & Margins**: Margins and growth rates are stored as percentages on a `0–100%` scale (e.g., `46.91`), while liquidity/solvency multipliers (e.g., `current_ratio`) are stored as decimal multiples.

---

## 1. Company Metadata (`data/cleaned/company_metadata.csv`)

| Column Name | Data Type | Key / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `company_id` | `VARCHAR(50)` | Primary Key | Unique internal system identifier for the corporation |
| `ticker` | `VARCHAR(20)` | Unique, Non-Null | Stock market symbol (e.g., `AAPL`, `MSFT`, `RELIANCE.NS`) |
| `company_name` | `VARCHAR(150)` | Non-Null | Full registered legal name of the corporation |
| `exchange` | `VARCHAR(50)` | Non-Null | Stock exchange listing (e.g., `NASDAQ`, `NYSE`, `BSE`, `NSE`) |
| `country` | `VARCHAR(50)` | Non-Null | Country of incorporation or headquarter location (e.g., `USA`, `IND`) |
| `currency` | `VARCHAR(3)` | ISO 4217 | Reporting functional currency code (e.g., `USD`, `INR`, `EUR`) |
| `fiscal_year_end` | `VARCHAR(10)` | `MM-DD` | Date ending the fiscal year (e.g., `12-31`, `03-31`) |
| `reporting_period` | `VARCHAR(20)` | `Annual`, `Quarterly` | Granularity of financial statement reporting |
| `filing_date` | `DATE` | `YYYY-MM-DD` | Official regulatory submission date of the filing (e.g., SEC 10-K / 10-Q date) |
| `data_source` | `VARCHAR(50)` | Non-Null | Data provider or origin system (e.g., `Yahoo Finance`, `SEC EDGAR`, `Bloomberg`, `API`) |

---

## 2. Income Statement (`data/cleaned/income_statement.csv`)

*Composite Primary Key: `(company_id, fiscal_year, fiscal_quarter)`*

| Column Name | Data Type | Key / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `company_id` | `VARCHAR(50)` | FK (Composite PK) | Foreign key referencing `company_metadata.company_id` |
| `company_name` | `VARCHAR(100)` | Non-Null | Registered name of the corporation |
| `fiscal_year` | `INT` | Non-Null (Composite PK) | Fiscal year of reported metrics (e.g., `2023`, `2024`) |
| `fiscal_quarter` | `VARCHAR(2)` | Non-Null (Composite PK) | Reporting period / quarter (`Q1`, `Q2`, `Q3`, `Q4`, or `FY` for annual) |
| `revenue` | `DECIMAL(18,2)` | `revenue >= 0` | Revenue reported by the company for the applicable reporting period. |
| `cost_of_goods_sold` | `DECIMAL(18,2)` | `cogs >= 0` | Direct costs attributable to the production of goods/services |
| `gross_profit` | `DECIMAL(18,2)` | Computed | Gross profit reported by the company (or `revenue - cost_of_goods_sold`) |
| `operating_expenses` | `DECIMAL(18,2)` | `opex >= 0` | SG&A, R&D, and other core operating costs |
| `operating_income` | `DECIMAL(18,2)` | Reported / Derived | Operating income (EBIT) as reported by the company. Obtained from filings when available; derived from gross profit, operating expenses, and other operating items only when appropriate. |
| `interest_expense` | `DECIMAL(18,2)` | `interest_expense >= 0` | Periodic interest payable on outstanding debt |
| `tax_expense` | `DECIMAL(18,2)` | Numeric | Income tax provision for the period |
| `net_income` | `DECIMAL(18,2)` | Computed | Total earnings or loss after all expenses, interest, and taxes |

---

## 3. Balance Sheet (`data/cleaned/balance_sheet.csv`)

*Composite Primary Key: `(company_id, fiscal_year, fiscal_quarter)`*

| Column Name | Data Type | Key / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `company_id` | `VARCHAR(50)` | FK (Composite PK) | Foreign key referencing `company_metadata.company_id` |
| `fiscal_year` | `INT` | Non-Null (Composite PK) | Fiscal year of reported metrics (e.g., `2023`, `2024`) |
| `fiscal_quarter` | `VARCHAR(2)` | Non-Null (Composite PK) | Reporting period / quarter (`Q1`, `Q2`, `Q3`, `Q4`, or `FY` for annual) |
| `cash_and_equivalents` | `DECIMAL(18,2)` | `>= 0` | Liquid assets held in cash, treasury bills, or short-term deposits |
| `accounts_receivable` | `DECIMAL(18,2)` | `>= 0` | Money owed by customers for goods/services delivered |
| `inventory` | `DECIMAL(18,2)` | `>= 0` | Total value of raw materials, work-in-progress, and finished goods |
| `total_current_assets` | `DECIMAL(18,2)` | Computed | Assets expected to be converted to cash within 1 year |
| `property_plant_equipment`| `DECIMAL(18,2)` | `>= 0` | Long-term tangible assets (PPE) less accumulated depreciation |
| `total_assets` | `DECIMAL(18,2)` | Computed | Sum of current and long-term non-current assets |
| `accounts_payable` | `DECIMAL(18,2)` | `>= 0` | Short-term obligations due to suppliers |
| `short_term_debt` | `DECIMAL(18,2)` | `>= 0` | Portion of debt due within 1 fiscal year |
| `total_current_liabilities`| `DECIMAL(18,2)` | Computed | Liabilities due within 1 fiscal year |
| `long_term_debt` | `DECIMAL(18,2)` | `>= 0` | Long-term loans, bonds, and financial obligations |
| `total_liabilities` | `DECIMAL(18,2)` | Computed | Sum of total current and non-current liabilities |
| `total_equity` | `DECIMAL(18,2)` | Computed | Shareholder equity (`total_assets - total_liabilities`) |

---

## 4. Cash Flow Statement (`data/cleaned/cash_flow.csv`)

*Composite Primary Key: `(company_id, fiscal_year, fiscal_quarter)`*

| Column Name | Data Type | Key / Constraints | Description |
| :--- | :--- | :--- | :--- |
| `company_id` | `VARCHAR(50)` | FK (Composite PK) | Foreign key referencing `company_metadata.company_id` |
| `fiscal_year` | `INT` | Non-Null (Composite PK) | Fiscal year (e.g., `2023`, `2024`) |
| `fiscal_quarter` | `VARCHAR(2)` | Non-Null (Composite PK) | Reporting period / quarter (`Q1`, `Q2`, `Q3`, `Q4`, or `FY` for annual) |
| `operating_cash_flow` | `DECIMAL(18,2)` | Numeric | Cash generated from core operations (CFO) |
| `capital_expenditures` | `DECIMAL(18,2)` | Numeric | Cash spent on acquiring or maintaining fixed assets (CapEx) |
| `investing_cash_flow` | `DECIMAL(18,2)` | Numeric | Net cash spent/earned from investments and CapEx (CFI) |
| `financing_cash_flow` | `DECIMAL(18,2)` | Numeric | Net cash flow from debt issuing/repayment, dividends, equity (CFF) |
| `free_cash_flow` | `DECIMAL(18,2)` | Computed | `operating_cash_flow - capital_expenditures` |

---

## 5. Financial Ratios & Health Indicators (`data/cleaned/financial_ratios.csv`)

*Composite Primary Key: `(company_id, fiscal_year, fiscal_quarter)`*

> **Note on Benchmarking & Interpretation**: Static universal benchmarks (e.g., `Current Ratio > 1.5`) are deliberately omitted. Evaluation of financial health relies on context-aware comparative analysis based on:
> - Historical company trends
> - Industry sector norms
> - Peer group comparisons
> - Company business model dynamics

| Metric Name | Formula / Logic | Description & Analytical Focus |
| :--- | :--- | :--- |
| `current_ratio` | `total_current_assets / total_current_liabilities` | Liquidity measure evaluating the capacity to cover short-term obligations |
| `quick_ratio` | `(cash_and_equivalents + accounts_receivable) / total_current_liabilities` | Strict liquidity measure evaluating immediate obligation coverage excluding inventory |
| `debt_to_equity` | `(short_term_debt + long_term_debt) / total_equity` | Financial leverage measuring explicit interest-bearing debt relative to equity |
| `liabilities_to_equity` | `total_liabilities / total_equity` | Total leverage measuring all liabilities (debt + non-debt operational obligations) relative to equity |
| `debt_to_assets` | `(short_term_debt + long_term_debt) / total_assets` | Proportion of company's total asset base financed through explicit debt |
| `interest_coverage` | `operating_income / interest_expense` | Solvency capability to service interest payments from operating income |
| `gross_margin` | `gross_profit / revenue` | Production efficiency and direct cost control ratio |
| `operating_margin` | `operating_income / revenue` | Core operational profitability margin |
| `net_profit_margin` | `net_income / revenue` | Bottom-line net profitability ratio |
| `return_on_assets` | `net_income / total_assets` | Efficiency in converting total assets into net profit |
| `return_on_equity` | `net_income / total_equity` | Net return generated per unit of shareholder capital |
| `altman_z_score` | Multi-factor Z-Score calculation * | Predictive distress score. *Note: Multiple Z-score formulations exist for manufacturing vs. non-manufacturing, service, and emerging market firms. The original model's fixed thresholds (e.g., Z > 2.99 = Safe) are context-dependent and will be adapted per company type during implementation.* |



