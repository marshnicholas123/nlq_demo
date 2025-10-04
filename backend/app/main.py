from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import text2sql
from app.config import settings
from app.observability import phoenix_observability
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Nuclear Power Text2SQL API",
    description="Demo application for Text2SQL variants",
    version="1.0.0"
)


@app.on_event("startup")
async def startup_event():
    """Initialize Phoenix observability on application startup"""
    if settings.phoenix_enabled:
        try:
            logger.info("Initializing Phoenix observability...")
            phoenix_observability.initialize(
                project_name=settings.phoenix_project_name,
                endpoint=settings.phoenix_endpoint,
                launch_app=settings.phoenix_launch_app
            )
            logger.info("Phoenix observability initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Phoenix observability: {str(e)}")
    else:
        logger.info("Phoenix observability is disabled")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup Phoenix on application shutdown"""
    if settings.phoenix_enabled and phoenix_observability.is_initialized():
        logger.info("Shutting down Phoenix observability...")
        phoenix_observability.shutdown()


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(text2sql.router, prefix="/api/text2sql", tags=["text2sql"])


@app.get("/")
async def root():
    return {
        "message": "Nuclear Power Text2SQL API",
        "endpoints": [
            "/api/text2sql/simple",
            "/api/text2sql/advanced",
            "/api/text2sql/chat",
            "/api/text2sql/agentic"
        ],
        "observability": {
            "phoenix_enabled": settings.phoenix_enabled,
            "phoenix_initialized": phoenix_observability.is_initialized()
        }
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "observability": {
            "phoenix_enabled": settings.phoenix_enabled,
            "phoenix_initialized": phoenix_observability.is_initialized()
        }
    }


@app.get("/phoenix")
async def phoenix_status():
    """Get Phoenix observability status"""
    return {
        "enabled": settings.phoenix_enabled,
        "initialized": phoenix_observability.is_initialized(),
        "project_name": settings.phoenix_project_name,
        "endpoint": settings.phoenix_endpoint or "local (http://127.0.0.1:6006)"
    }