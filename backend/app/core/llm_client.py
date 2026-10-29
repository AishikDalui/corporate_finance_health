"""LLM client for generating Text-to-SQL queries and executive insights."""
import re
from typing import Optional, List, Dict, Any
import httpx
from backend.app.config import settings
from backend.app.core.schema_context import SchemaContextBuilder


class LLMClient:
    """Handles communication with OpenAI / compatible LLM endpoints."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_sql: Optional[str] = None,
        model_insight: Optional[str] = None,
    ):
        self.api_key = api_key or settings.openai_api_key
        self.model_sql = model_sql or settings.openai_model_sql
        self.model_insight = model_insight or settings.openai_model_insight

    async def generate_sql(
        self,
        question: str,
        year_filter: Optional[int] = None,
    ) -> Optional[str]:
        """Convert natural language financial question into SQL query using LLM."""
        if not self.api_key:
            return None

        schema = SchemaContextBuilder.get_full_schema_context()
        year_hint = f" The user specifically selected fiscal year {year_filter}." if year_filter else ""

        system_prompt = f"""You are a principal financial data engineer at Apple Inc.
Convert management questions into an accurate, read-only MySQL 8.0 SELECT query.

{schema}

CRITICAL RULES:
1. ONLY return the raw SQL query. Do not wrap in markdown quotes or explanations.
2. ONLY use tables: income_statement, balance_sheet, cash_flow, accounts_payable.
3. Monetary figures in raw tables are unscaled USD. Always scale large figures to billions: ROUND(revenue / 1e9, 2) AS revenue_billion.
4. Join statements on `end` column.
5. If filtering by year, use YEAR(end) = <YEAR>.{year_hint}
6. Always include `end AS fiscal_year_end` and `ORDER BY end ASC`.
"""

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model_sql,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": question},
                        ],
                        "temperature": 0.0,
                    },
                )
                if response.status_code == 200:
                    payload = response.json()
                    raw_sql = payload["choices"][0]["message"]["content"]
                    # Clean markdown code blocks if any
                    clean_sql = re.sub(r"^```(?:sql)?\s*", "", raw_sql.strip(), flags=re.IGNORECASE)
                    clean_sql = re.sub(r"\s*```$", "", clean_sql.strip())
                    return clean_sql.strip()
        except Exception:
            return None

        return None

    async def generate_narrative(
        self,
        question: str,
        sql_query: str,
        data: List[Dict[str, Any]],
    ) -> Optional[str]:
        """Generate high-level narrative summary using LLM."""
        if not self.api_key or not data:
            return None

        prompt = f"""Executive Question: "{question}"
Executed SQL:
{sql_query}

Query Results (first 10 rows):
{data[:10]}

Provide a concise 2-3 paragraph executive summary for senior management. Highlight key numbers, growth or decline trends, margin dynamics, and business implications for Apple.
"""

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model_insight,
                        "messages": [
                            {"role": "system", "content": "You are a Chief Financial Analyst presenting directly to Apple's Board."},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.3,
                    },
                )
                if response.status_code == 200:
                    payload = response.json()
                    return payload["choices"][0]["message"]["content"].strip()
        except Exception:
            return None

        return None
