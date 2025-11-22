"""Main FastAPI application for YouTube Analytics backend."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.database.connection import db
from src.api.routes import accounts, channels, videos, analytics

# Create FastAPI app
app = FastAPI(
    title="YouTube Analytics API",
    description="REST API for YouTube Studio analytics data management and querying",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Startup/Shutdown Events ====================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    print("Starting YouTube Analytics API...")
    db.create_tables()
    health = db.health_check()
    if health:
        print("✓ Database connection healthy")
    else:
        print("✗ Warning: Database health check failed")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("Shutting down YouTube Analytics API...")
    db.close()


# ==================== Health Check ====================

@app.get("/health", tags=["system"])
async def health_check():
    """Check API and database health."""
    return {
        "status": "healthy",
        "database": "connected" if db.health_check() else "disconnected",
    }


# ==================== Root Endpoint ====================

@app.get("/", tags=["system"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "YouTube Analytics API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "endpoints": {
            "accounts": "/accounts",
            "channels": "/channels",
            "videos": "/videos",
            "analytics": "/analytics",
        },
    }


# ==================== Route Registration ====================

# Include routers
app.include_router(accounts.router)
app.include_router(channels.router)
app.include_router(videos.router)
app.include_router(analytics.router)


# ==================== Error Handling ====================

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions."""
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
