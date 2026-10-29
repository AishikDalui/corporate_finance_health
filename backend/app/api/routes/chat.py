"""Chat route handling executive NL queries."""
from fastapi import APIRouter, HTTPException, Depends
from backend.app.models.request import ChatRequest, FeedbackRequest
from backend.app.models.response import ChatResponse
from backend.app.core.text_to_sql import TextToSQLPipeline

router = APIRouter(prefix="/chat", tags=["Chat"])
pipeline = TextToSQLPipeline()


@router.post("", response_model=ChatResponse)
async def process_chat_message(request: ChatRequest):
    """Process executive natural language inquiry, generate SQL, and return analytical insight + charts."""
    try:
        response = await pipeline.process_chat(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@router.post("/feedback")
async def record_feedback(feedback: FeedbackRequest):
    """Record user thumbs up/down feedback for model reinforcement."""
    # In production, persist to audit database
    return {"status": "success", "message": "Feedback recorded successfully"}
