"""FastAPI Application Entry Point with Web Dashboard Interface."""
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.app.config import settings
from backend.app.api.routes.chat import router as chat_router
from backend.app.api.routes.data import router as data_router

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Production-grade AI Financial Analyst providing Text-to-SQL analytics, dynamic chart generation, and executive insights.",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers under /api/v1 prefix
app.include_router(chat_router, prefix="/api/v1")
app.include_router(data_router, prefix="/api/v1")

STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", tags=["Dashboard"], include_in_schema=False)
def get_dashboard():
    """Serve the interactive executive financial health web dashboard."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Corporate Financial Health AI API is running. Access /docs for Swagger UI."}


@app.get("/api/v1/health", tags=["Health"])
def health_check():
    """Health check endpoint for container liveness probes."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
