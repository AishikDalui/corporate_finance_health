from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ChartConfig(BaseModel):
    """Configuration for rendering dynamic frontend charts."""

    chart_type: str = Field(..., description="Chart type: line, bar, pie, table, kpi_card")
    title: str = Field(..., description="Chart title for management presentation")
    x_axis: str = Field(..., description="Key for X-axis (e.g. fiscal_year_end, end)")
    y_axis: str = Field(..., description="Key for Y-axis (e.g. revenue, gross_margin_pct)")
    series: List[Dict[str, Any]] = Field(default_factory=list, description="Series definition with keys, labels, colors")
    format_type: str = Field("number", description="Formatting style: currency, percentage, number, ratio")


class ChatResponse(BaseModel):
    """Full AI response delivered to management."""

    message_id: str
    answer: str = Field(..., description="Executive narrative insight in plain business language")
    sql_query: str = Field(..., description="Generated and executed SQL query for auditability")
    data: List[Dict[str, Any]] = Field(default_factory=list, description="Raw rows returned by database execution")
    chart: Optional[ChartConfig] = None
    suggested_followups: List[str] = Field(default_factory=list, description="Next suggested analytical questions")
    confidence: float = Field(1.0, description="Confidence score 0.0 - 1.0")
    source: str = Field("llm", description="Origin of query: pre_built_library or generated_sql")
    execution_time_ms: float = 0.0


class KPISummary(BaseModel):
    """High-level fiscal year executive KPI card."""

    fiscal_year: str
    revenue_billion: float
    gross_margin_pct: float
    operating_margin_pct: float
    net_margin_pct: float
    current_ratio: float
    operating_cash_flow_billion: Optional[float] = None
    ocf_to_net_income: Optional[float] = None


class TableColumnInfo(BaseModel):
    name: str
    type: str
    nullable: bool = True


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
