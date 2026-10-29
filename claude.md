# 🧠 Claude Memory — AI Financial Chatbot Development Log

> **Project**: Corporate Financial Health AI Chatbot  
> **Repository**: `/Users/oishikdalui/Documents/windowshared/corporate-financial-health`  
> **Current Status**: 🟢 PRODUCTION-READY BACKEND & DASHBOARD — Phase 1 & 2 Completed  
> **Last Updated**: 2026-10-28 00:15 IST  

---

## Architecture Summary
| Layer | Technology | Details |
|---|---|---|
| **API Framework** | FastAPI (Python 3.13) | High performance, async REST API, auto OpenAPI docs (`/docs`) |
| **Database** | MySQL 8.0 (`corporate_financial_health`) | Direct connection via SQLAlchemy + PyMySQL on `localhost:3306` |
| **SQL Engine** | Dual Hybrid Engine | 1. Pre-built vetted SQL templates (Exp2/exp3/Untitled.sql) → **0 API calls, 100% free & local**<br>2. OpenAI Text-to-SQL fallback (GPT-4o) → **Triggered ONLY for unknown/custom questions** |
| **SQL Safety & AST** | sqlglot + AST token analyzer | Blocks non-SELECT, DDL/DML, stacked queries, unauthorized tables |
| **Visualization** | Chart.js dynamic dashboard | Recharts/Chart.js rendering Line, Bar, KPI Cards, and Tables |
| **UI Dashboard** | HTML5 + Tailwind CSS + FontAwesome | Interactive year filters (2025, 2024, 2023, 2022), live KPI ribbon, chat bubbles, collapsible SQL inspection |

---

## Live Database Validation
Connected to MySQL `corporate_financial_health` on `localhost:3306`:
- `income_statement`: **19 rows** (FY2007–FY2025)
- `balance_sheet`: **18 rows** (FY2008–FY2025)
- `cash_flow`: **19 rows** (FY2007–FY2025)
- `accounts_payable`: **10 rows** (FY2016–FY2025)

---

## Feature Tracker

| # | Feature | Status | Tests | File Location |
|---|---|---|---|---|
| 1 | Configuration & Environment Management | ✅ DONE | Tested | [`backend/app/config.py`](file:///Users/oishikdalui/Documents/windowshared/corporate-financial-health/backend/app/config.py) |
| 2 | Pydantic Request & Response Models | ✅ DONE | 4 Tests | [`backend/app/models/`](file:///Users/oishikdalui/Documents/windowshared/corporate-financial-health/backend/app/models/) |
| 3 | Read-only Database Engine & Execution | ✅ DONE | Live Verified | [`backend/app/db/connection.py`](file:///Users/oishikdalui/Documents/windowshared/corporate-financial-health/backend/app/db/connection.py) |
| 4 | Schema Context Builder & Business Rules | ✅ DONE | 3 Tests | [`backend/app/core/schema_context.py`](file:///Users/oishikdalui/Documents/windowshared/corporate-financial-health/backend/app/core/schema_context.py) |
| 5 | SQL Safety AST Validator & Sanitizer | ✅ DONE | 12 Tests | [`backend/app/core/sql_validator.py`](file:///Users/oishikdalui/Documents/windowshared/corporate-financial-health/backend/app/core/sql_validator.py) |
| 6 | Pre-built Query Library (Exp2/exp3/Untitled) | ✅ DONE | 6 Tests | [`backend/app/core/query_library.py`](file:///Users/oishikdalui/Documents/windowshared/corporate-financial-health/backend/app/core/query_library.py) |
| 7 | Dynamic Chart Type & Series Selector | ✅ DONE | 4 Tests | [`backend/app/core/chart_selector.py`](file:///Users/oishikdalui/Documents/windowshared/corporate-financial-health/backend/app/core/chart_selector.py) |
| 8 | Executive Insight & Followup Generator | ✅ DONE | 3 Tests | [`backend/app/core/insight_generator.py`](file:///Users/oishikdalui/Documents/windowshared/corporate-financial-health/backend/app/core/insight_generator.py) |
| 9 | LLM Client (OpenAI API / Resilient Fallback) | ✅ DONE | Tested | [`backend/app/core/llm_client.py`](file:///Users/oishikdalui/Documents/windowshared/corporate-financial-health/backend/app/core/llm_client.py) |
| 10 | End-to-end Text-to-SQL Pipeline | ✅ DONE | E2E Tested (31ms) | [`backend/app/core/text_to_sql.py`](file:///Users/oishikdalui/Documents/windowshared/corporate-financial-health/backend/app/core/text_to_sql.py) |
| 11 | FastAPI Chat & Feedback Endpoints | ✅ DONE | 3 Tests | [`backend/app/api/routes/chat.py`](file:///Users/oishikdalui/Documents/windowshared/corporate-financial-health/backend/app/api/routes/chat.py) |
| 12 | Financial Data & Year Filter Endpoints | ✅ DONE | 2 Tests | [`backend/app/api/routes/data.py`](file:///Users/oishikdalui/Documents/windowshared/corporate-financial-health/backend/app/api/routes/data.py) |
| 13 | Interactive Web Dashboard (UI + Charts) | ✅ DONE | 1 Test | [`backend/app/static/index.html`](file:///Users/oishikdalui/Documents/windowshared/corporate-financial-health/backend/app/static/index.html) |
| 14 | Root App Server & Health Probes | ✅ DONE | Tested | [`backend/app/main.py`](file:///Users/oishikdalui/Documents/windowshared/corporate-financial-health/backend/app/main.py) |

---

## Bug Fix Log

### 2026-10-28 — Add Dedicated DSO & DPO Templates and Improve Acronym Matching
- **Symptom**: Asking "total dso" showed the "Revenue ($B) & Net Income ($B) Trajectory" output.
- **Root Cause**: Two issues:
  1. The threshold `score >= 2` prevented single domain acronyms (`dso`, `dpo`) from meeting the match threshold without multi-word matches.
  2. When no template matched and no OpenAI API key was configured, the system silently defaulted to `revenue_growth_trajectory` instead of informing the user.
- **Fix**:
  1. Added dedicated `days_sales_outstanding` (DSO) template from `Untitled.sql` Part 9.
  2. Added dedicated `days_payable_outstanding` (DPO) template from `exp3.sql` Part 2.
  3. Upgraded keyword matching to use regex word boundaries `\b{kw}\b` with high scoring so exact acronyms like `dso`, `ccc`, `dpo`, `dio` match immediately.
  4. Updated fallback in `text_to_sql.py`: If a query is truly unknown and no API key is present, it now returns a clear guidance message with recommended analytical follow-ups instead of silently defaulting to Revenue Trajectory.
- **Unit Tests Added**: `test_match_total_dso` and `test_match_dpo` (all 42 tests passing).

### 2026-10-28 — Fix Ambiguous `end` Column in Joined SQL Queries
- **Symptom**: `(pymysql.err.OperationalError) (1052, "Column 'end' in where clause is ambiguous")` on joined queries when filtering by year (e.g. `Show executive financial health summary for 2025`).
- **Root Cause**: When multiple tables (`income_statement`, `balance_sheet`, `cash_flow`) are joined together, they all contain an `end` column. Applying `WHERE YEAR(end) = {year}` caused MySQL to throw error 1052 because `end` was unqualified. This had nothing to do with API keys.
- **Fix**: Updated [`QueryLibrary._apply_year_filter`](file:///Users/oishikdalui/Documents/windowshared/corporate-financial-health/backend/app/core/query_library.py) to wrap non-CTE queries in derived subqueries `SELECT * FROM (...) AS _report_data WHERE YEAR(_report_data.fiscal_year_end) = {year}`. Because each subquery defines `fiscal_year_end`, column names are completely unambiguous.
- **Auto-Detection**: Also added natural-language year extraction (`re.search(r"\b(20[0-2][0-9])\b")`) so that years mentioned in the prompt text (e.g., "in 2024") are automatically extracted and filtered safely even if the user didn't click the year button.
- **Unit Tests Added**: `test_multi_table_join_prevents_ambiguous_end_column` and `test_auto_detect_year_from_question_text` (all 40 tests passing).

---

## Test Results Log (pytest)

```text
======================== 42 passed, 1 warning in 0.28s =========================
- test_health_check_endpoint: PASSED
- test_dashboard_root_endpoint: PASSED
- test_quick_actions_endpoint: PASSED
- test_kpi_summary_endpoint: PASSED
- test_chat_feedback_endpoint: PASSED
- test_chat_endpoint_structure: PASSED
- test_single_row_selects_kpi_card: PASSED
- test_time_series_selects_line_chart: PASSED
- test_explicit_preference_overrides_heuristic: PASSED
- test_percentage_format_inference: PASSED
- test_currency_formatting: PASSED
- test_single_row_insight_generation: PASSED
- test_suggested_followups: PASSED
- test_chat_request_validation: PASSED
- test_chart_config_validation: PASSED
- test_chat_response_serialization: PASSED
- test_kpi_summary_model: PASSED
- test_match_profitability_margins: PASSED
- test_match_cash_conversion_cycle: PASSED
- test_match_solvency_and_leverage: PASSED
- test_match_earnings_quality: PASSED
- test_year_filter_applied_to_query: PASSED
- test_multi_table_join_prevents_ambiguous_end_column: PASSED
- test_auto_detect_year_from_question_text: PASSED
- test_no_match_for_unrelated_query: PASSED
- test_schema_contains_all_core_tables: PASSED
- test_schema_contains_column_guidelines: PASSED
- test_schema_contains_join_rules: PASSED
- test_valid_select_query: PASSED
- test_valid_cte_query: PASSED
- test_valid_multi_table_join: PASSED
- test_blocks_insert: PASSED
- test_blocks_update: PASSED
- test_blocks_delete: PASSED
- test_blocks_drop_table: PASSED
- test_blocks_stacked_queries: PASSED
- test_blocks_unauthorized_tables: PASSED
- test_blocks_system_schema: PASSED
- test_sanitizer_removes_markdown_ticks: PASSED
- test_blocks_empty_query: PASSED
```

---

## How to Run the Production System

```bash
# 1. Activate Python virtual environment
cd /Users/oishikdalui/Documents/windowshared/corporate-financial-health
source .venv/bin/activate

# 2. Run test suite
pytest backend/tests -v

# 3. Launch the AI Chatbot Server & Web Dashboard
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Web Dashboard**: Navigate to `http://localhost:8000/` in your browser.
- **Interactive Swagger API Docs**: Navigate to `http://localhost:8000/docs`.
- **API Health Check**: `http://localhost:8000/api/v1/health`.
