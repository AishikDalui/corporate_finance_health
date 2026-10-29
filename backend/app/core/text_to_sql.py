"""End-to-end Text-to-SQL Pipeline orchestrating query resolution, execution, and presentation."""
import time
import uuid
from typing import Optional, List, Dict, Any
from backend.app.models.request import ChatRequest
from backend.app.models.response import ChatResponse, ChartConfig
from backend.app.core.query_library import QueryLibrary, QueryTemplate
from backend.app.core.sql_validator import SQLValidator
from backend.app.core.llm_client import LLMClient
from backend.app.core.chart_selector import ChartSelector
from backend.app.core.insight_generator import InsightGenerator
from backend.app.db.connection import DatabaseConnection


class TextToSQLPipeline:
    """Enterprise Text-to-SQL orchestrator."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.query_library = QueryLibrary()
        self.llm_client = llm_client or LLMClient()

    async def process_chat(self, request: ChatRequest) -> ChatResponse:
        """Process incoming natural language question and deliver full executive dashboard response."""
        start_time = time.time()
        message_id = str(uuid.uuid4())

        question = request.message.strip()
        year_filter = request.year_filter
        chart_pref = request.chart_preference or "auto"

        # Step 1: Check Pre-built Query Library
        matched_template = self.query_library.match(question, year_filter=year_filter)
        sql_query = ""
        source = "pre_built_library"
        template_chart_type = None
        template_title = None

        if matched_template:
            sql_query = matched_template.sql
            template_chart_type = matched_template.chart_type
            template_title = matched_template.title
        else:
            # Step 2: Use LLM Text-to-SQL
            llm_sql = await self.llm_client.generate_sql(question, year_filter=year_filter)
            if llm_sql:
                sql_query = llm_sql
                source = "llm_generated_sql"
            else:
                # No template matched and no LLM API key configured for ad-hoc SQL generation
                return ChatResponse(
                    message_id=message_id,
                    answer=(
                        f"I could not find a pre-built analytical template directly matching **\"{question}\"**.\n\n"
                        f"• **Quick Fix**: Select one of the verified executive analyses below or use the buttons above.\n"
                        f"• **For Ad-hoc AI**: Configure an `OPENAI_API_KEY` in your `.env` file to enable dynamic Text-to-SQL generation for custom questions."
                    ),
                    sql_query="-- No matching template. Configure OPENAI_API_KEY in .env for custom Text-to-SQL.",
                    data=[],
                    chart=None,
                    suggested_followups=[
                        "What is Apple's Days Sales Outstanding (DSO)?",
                        "Show me the Cash Conversion Cycle (CCC)",
                        "Show multi-stage profitability margins over time",
                        "What is Apple's current ratio and working capital?",
                    ],
                    confidence=0.0,
                    source="unmatched_query",
                    execution_time_ms=(time.time() - start_time) * 1000,
                )

        # Step 3: Validate SQL Safety
        is_valid, validation_msg = SQLValidator.validate(sql_query)
        if not is_valid:
            return ChatResponse(
                message_id=message_id,
                answer=f"⚠️ Query could not be safely executed: {validation_msg}. Please rephrase your question.",
                sql_query=sql_query,
                data=[],
                chart=None,
                suggested_followups=InsightGenerator.generate_suggested_followups(question, []),
                confidence=0.0,
                source=source,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # Step 4: Execute SQL against Database
        data: List[Dict[str, Any]] = []
        try:
            data = DatabaseConnection.execute_query(sql_query)
        except Exception as db_err:
            # If database execution throws, deliver structured diagnostic response
            return ChatResponse(
                message_id=message_id,
                answer=(
                    f"Generated query was: `{sql_query}`\n\n"
                    f"Notice: Database connection or query execution encountered: `{str(db_err)}`.\n"
                    f"Please verify MySQL server is running or check table permissions."
                ),
                sql_query=sql_query,
                data=[],
                chart=None,
                suggested_followups=InsightGenerator.generate_suggested_followups(question, []),
                confidence=0.5,
                source=source,
                execution_time_ms=(time.time() - start_time) * 1000,
            )

        # Step 5: Generate Executive Narrative
        # Strict Cost & Performance Optimization:
        # Known questions use instant local rule-based insights ($0 cost, 0 API calls).
        # OpenAI API is ONLY triggered for unknown/custom questions.
        if source == "llm_generated_sql":
            narrative = await self.llm_client.generate_narrative(question, sql_query, data)
        else:
            narrative = None

        if not narrative:
            narrative = InsightGenerator.generate_rule_based_insight(
                question, data, template_id=matched_template.id if matched_template else ""
            )

        # Step 6: Configure Visual Chart
        chart = ChartSelector.select_chart(
            question=question,
            data=data,
            template_chart_type=template_chart_type,
            template_title=template_title,
            chart_preference=chart_pref,
        )

        # Step 7: Suggested Follow-ups
        followups = InsightGenerator.generate_suggested_followups(
            question, data, template_id=matched_template.id if matched_template else ""
        )

        elapsed_ms = (time.time() - start_time) * 1000

        return ChatResponse(
            message_id=message_id,
            answer=narrative,
            sql_query=SQLValidator.sanitize(sql_query),
            data=data,
            chart=chart,
            suggested_followups=followups,
            confidence=0.95 if source == "pre_built_library" else 0.88,
            source=source,
            execution_time_ms=round(elapsed_ms, 2),
        )
