"""
Main FastAPI application entrypoint.
Mounts routers, configures CORS, serves static files, and initializes database.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.core.config import settings
from backend.database.connection import init_db
from backend.api import health, chat, rag, search, documents, multimodal, audio, emotional

# Setup logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

# Ensure media storage directories exist before mounting static files
upload_dir = settings.get_upload_path()
generated_dir = settings.get_generated_media_path()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan events: initialize database schema.
    """
    logger.info("Initializing database schemas...")
    try:
        init_db()
        logger.info("Application startup completed successfully.")
    except Exception as e:
        logger.error("Startup initialization warning: %s", str(e))
    yield
    logger.info("Application shutting down.")


app = FastAPI(
    title=settings.APP_NAME,
    description="Beginner-friendly Multimodal AI Chatbot API with RAG, Web Search, Audio, Vision, and Emotional Support.",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits localhost streamlit calls
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount local media directory for serving generated images and audio
app.mount("/media/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")
app.mount("/media/generated", StaticFiles(directory=str(generated_dir)), name="generated")

# Include Core System Routers
app.include_router(health.router)
app.include_router(chat.router)
app.include_router(rag.router)
app.include_router(search.router)
app.include_router(documents.router)
app.include_router(multimodal.router)
app.include_router(audio.router)
app.include_router(emotional.router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Gracefully handle unhandled exceptions to prevent stack traces leaking to clients.
    """
    logger.error("Unhandled server exception on %s: %s", request.url.path, str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please verify your configuration or check logs."}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
