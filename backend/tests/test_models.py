"""Unit tests for Pydantic request and response models."""
from backend.app.models.request import ChatRequest, FeedbackRequest
from backend.app.models.response import ChatResponse, ChartConfig, KPISummary


def test_chat_request_validation():
    req = ChatRequest(message="What was Apple's gross margin in 2024?", year_filter=2024)
    assert req.message == "What was Apple's gross margin in 2024?"
    assert req.year_filter == 2024
    assert req.chart_preference == "auto"
    assert req.session_id == "default-session"


def test_chart_config_validation():
    chart = ChartConfig(
        chart_type="line",
        title="Gross Margin Trend",
        x_axis="fiscal_year_end",
        y_axis="gross_margin_pct",
        series=[{"dataKey": "gross_margin_pct", "label": "Gross Margin %", "color": "#0071E3"}],
        format_type="percentage",
    )
    assert chart.chart_type == "line"
    assert len(chart.series) == 1


def test_chat_response_serialization():
    resp = ChatResponse(
        message_id="msg-123",
        answer="Apple's gross margin expanded.",
        sql_query="SELECT gross_margin_pct FROM income_statement",
        data=[{"gross_margin_pct": 46.9}],
        confidence=0.95,
        source="pre_built_library",
    )
    data_dict = resp.model_dump()
    assert data_dict["message_id"] == "msg-123"
    assert data_dict["confidence"] == 0.95


def test_kpi_summary_model():
    kpi = KPISummary(
        fiscal_year="2025-09-27",
        revenue_billion=395.8,
        gross_margin_pct=46.91,
        operating_margin_pct=31.97,
        net_margin_pct=26.3,
        current_ratio=0.87,
    )
    assert kpi.revenue_billion == 395.8
    assert kpi.current_ratio == 0.87
