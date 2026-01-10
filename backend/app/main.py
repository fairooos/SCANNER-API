"""
SCANNER - Document Scanning API
Main FastAPI application entry point.
"""
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from app.api.v1.router import api_router

# Create FastAPI application
app = FastAPI(
    title="SCANNER API",
    version="1.0.0",
    description="Document scanning and OCR system for Emirates ID and Passports",
    docs_url="/docs",  # Swagger UI available at /docs
    redoc_url="/redoc",  # ReDoc available at /redoc
    openapi_url="/openapi.json"
)

# CORS Middleware
# In production, restrict origins to your frontend domain
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router with /api/v1 prefix
app.include_router(
    api_router,
    prefix="/api/v1"
)


# Root endpoint - API information
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - provides API information.
    """
    return {
        "name": "SCANNER API",
        "version": "1.0.0",
        "description": "Document scanning and OCR system for Emirates ID and Passports",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "endpoints": {
            "health": "/api/v1/health",
            "emirates_id_scan": "/api/v1/id/scan",
            "passport_scan": "/api/v1/passport/scan"
        }
    }


# Startup event - verify models are loadable (optional but recommended)
@app.on_event("startup")
async def startup_event():
    """
    Startup event handler.
    Can be used to:
    - Verify model files exist
    - Pre-load models
    - Initialize connections
    """
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting SCANNER API v1.0.0")
    
    yolo_path = Path("models/best.pt")
    logger.info(f"YOLO model path: {yolo_path}")
    
    # Verify YOLO model exists
    if not yolo_path.exists():
        logger.warning(f"YOLO model not found at {yolo_path}")
        logger.warning("Emirates ID scanning will fail until model is provided")
    else:
        logger.info("YOLO model found")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on shutdown.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Shutting down SCANNER API")
