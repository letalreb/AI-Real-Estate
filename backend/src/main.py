"""
Main FastAPI application entry point.
Configures API routes, middleware, and WebSocket connections.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
import structlog
from contextlib import asynccontextmanager

from .config import settings
from .database import engine, Base
from .api import auctions, users, preferences, websocket as ws_module

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ] if settings.LOG_FORMAT == "json" else [
        structlog.dev.ConsoleRenderer()
    ],
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info("starting_application", environment=settings.ENVIRONMENT)
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    logger.info("shutting_down_application")


# Create FastAPI application
app = FastAPI(
    title="AI Real Estate Auction Analyzer API",
    description="API for analyzing and ranking Italian real estate auctions",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auctions.router, prefix="/api/v1", tags=["auctions"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(preferences.router, prefix="/api/v1", tags=["preferences"])

# Mount Prometheus metrics
if settings.ENABLE_METRICS:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "AI Real Estate Auction Analyzer API",
        "docs": "/docs",
        "health": "/health"
    }


@app.websocket("/ws/notifications")
async def websocket_endpoint(websocket: WebSocket, token: str = None):
    """
    WebSocket endpoint for real-time notifications.
    
    Query params:
        token: JWT authentication token
    """
    await ws_module.handle_websocket_connection(websocket, token)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(
        "unhandled_exception",
        error=str(exc),
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
