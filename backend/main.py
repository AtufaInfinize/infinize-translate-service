"""
FastAPI Main Application
Entry point for the real-time audio translation service.
"""

import logging
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from backend.api.websocket import websocket_endpoint
from backend.config import get_settings, get_supported_languages_list
import os

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set specific loggers to appropriate levels
logging.getLogger('uvicorn').setLevel(logging.INFO)
logging.getLogger('fastapi').setLevel(logging.INFO)
logging.getLogger('backend.services.deepgram_transcribe_service').setLevel(logging.DEBUG)
logging.getLogger('backend.services.pipeline_manager').setLevel(logging.DEBUG)

# Create FastAPI app
app = FastAPI(
    title="Real-Time Audio Translation Service",
    description="Streams audio, transcribes with AWS Transcribe, translates with AWS Translate, "
                "and synthesizes speech with AWS Polly",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development - restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get settings
settings = get_settings()

# Mount static files (frontend)
frontend_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")
    logger.info(f"Mounted static files from {frontend_dir}")
else:
    logger.warning(f"Frontend directory not found: {frontend_dir}")


@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Serve the main frontend HTML page.
    """
    index_path = os.path.join(frontend_dir, "index.html")

    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return HTMLResponse(
            content="""
            <html>
                <head><title>Translation Service</title></head>
                <body>
                    <h1>Real-Time Audio Translation Service</h1>
                    <p>Frontend not found. Please ensure the frontend directory exists.</p>
                    <p>API is running. WebSocket endpoint: <code>ws://localhost:8000/ws/translate</code></p>
                </body>
            </html>
            """,
            status_code=200
        )


@app.get("/health")
async def health():
    """
    Health check endpoint.
    """
    return {
        "status": "healthy",
        "service": "translation-service",
        "version": "1.0.0"
    }


@app.get("/api/languages")
async def get_languages():
    """
    Get list of supported languages.

    Returns:
        List of language objects with code and name
    """
    return {
        "languages": get_supported_languages_list()
    }


@app.get("/api/config")
async def get_config():
    """
    Get service configuration (non-sensitive).

    Returns:
        Configuration information
    """
    return {
        "sample_rate": settings.sample_rate,
        "audio_chunk_size": settings.audio_chunk_size,
        "aws_region": settings.aws_region,
        "supported_languages": len(get_supported_languages_list())
    }


@app.websocket("/ws/translate")
async def websocket_route(websocket: WebSocket):
    """
    WebSocket endpoint for real-time audio translation.

    Protocol:
    1. Client sends config: {'type': 'config', 'source_language': 'en-US', 'target_language': 'es-ES'}
    2. Client streams audio: {'type': 'audio', 'audio': 'base64...'}
    3. Server sends transcripts, translations, and audio
    4. Client stops: {'type': 'stop'}

    Args:
        websocket: WebSocket connection
    """
    await websocket_endpoint(websocket)


@app.on_event("startup")
async def startup_event():
    """
    Run on application startup.
    """
    logger.info("=" * 60)
    logger.info("Real-Time Audio Translation Service Starting...")
    logger.info(f"AWS Region: {settings.aws_region}")
    logger.info(f"Sample Rate: {settings.sample_rate}Hz")
    logger.info(f"Supported Languages: {len(get_supported_languages_list())}")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """
    Run on application shutdown.
    """
    logger.info("Shutting down Translation Service...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )
