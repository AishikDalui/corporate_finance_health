from typing import Optional, Literal
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Incoming user chat request."""

    message: str = Field(..., description="Natural language question from management")
    year_filter: Optional[int] = Field(None, description="Selected fiscal year filter (e.g. 2022, 2023, 2024, 2025)")
    chart_preference: Optional[str] = Field("auto", description="Preferred chart visualization: auto, line, bar, pie, table, kpi_card")
    session_id: str = Field("default-session", description="Conversation session ID")


class FeedbackRequest(BaseModel):
    """User feedback on AI responses."""

    session_id: str
    message_id: str
    feedback: Literal["thumbs_up", "thumbs_down"]
    comment: Optional[str] = None
