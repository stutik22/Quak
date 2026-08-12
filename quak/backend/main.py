"""
Main FastAPI application for QWAK Recipe Recommender.
"""
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

try:
    # Try relative imports first (when run as module)
    from .core.config import settings
    from .core.model_manager import model_manager
    from .core.caching import cache_manager
    from .api.recommend import router as recommend_router
    from .api.models import HealthResponse, ErrorResponse
except ImportError:
    # Fall back to absolute imports (when run directly)
    from core.config import settings
    from core.model_manager import model_manager
    from core.caching import cache_manager
    from api.recommend import router as recommend_router
    from api.models import HealthResponse, ErrorResponse

# Global variables for tracking application state
app_start_time = time.time()
models_status = {
    "tfidf_loaded": False,
    "embedding_loaded": False,
    "last_check": None
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    print(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Load models if preloading is enabled
    if settings.preload_models:
        print("Preloading models...")
        try:
            status = model_manager.load_models()
            models_status.update(status)
            print(f"Models loaded: {status}")
        except Exception as e:
            print(f"Error loading models: {e}")
    
    models_status["last_check"] = time.time()
    
    yield
    
    # Shutdown
    print("Shutting down QWAK Recipe Recommender")
    try:
        model_manager.unload_models()
        cache_manager.clear()
        print("Cleanup completed")
    except Exception as e:
        print(f"Error during cleanup: {e}")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered recipe recommendation system based on available ingredients",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(recommend_router)


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check the health status of the API and loaded models"
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint to verify API and model status.
    
    Returns:
        HealthResponse with current system status
    """
    uptime = time.time() - app_start_time
    
    # Get current model status
    current_status = model_manager.get_model_status()
    models_status.update(current_status)
    models_status["last_check"] = time.time()
    
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        models_loaded=models_status,
        uptime=uptime
    )


@app.get(
    "/health/detailed",
    summary="Detailed health check",
    description="Get detailed health information including memory usage and cache stats"
)
async def detailed_health_check():
    """
    Detailed health check with performance metrics.
    
    Returns:
        Detailed system information
    """
    uptime = time.time() - app_start_time
    model_info = model_manager.get_model_info()
    
    return {
        "status": "healthy",
        "version": settings.app_version,
        "uptime": uptime,
        "model_info": model_info,
        "cache_stats": cache_manager.get_stats(),
        "settings": {
            "preload_models": settings.preload_models,
            "enable_caching": settings.enable_caching,
            "enable_redis_cache": settings.enable_redis_cache,
            "max_ingredients": settings.max_ingredients,
            "request_timeout": settings.request_timeout
        }
    }


@app.post(
    "/admin/reload-models",
    summary="Reload models",
    description="Reload all ML models (admin endpoint)"
)
async def reload_models():
    """
    Reload all models (admin endpoint).
    
    Returns:
        Model loading status
    """
    try:
        status = model_manager.reload_models()
        models_status.update(status)
        models_status["last_check"] = time.time()
        
        return {
            "message": "Models reloaded successfully",
            "status": status,
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload models: {str(e)}"
        )


@app.post(
    "/admin/clear-cache",
    summary="Clear cache",
    description="Clear all cached data (admin endpoint)"
)
async def clear_cache():
    """
    Clear all cached data (admin endpoint).
    
    Returns:
        Cache clearing status
    """
    try:
        success = cache_manager.clear()
        
        return {
            "message": "Cache cleared successfully" if success else "Failed to clear cache",
            "success": success,
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear cache: {str(e)}"
        )


@app.post(
    "/admin/optimize-memory",
    summary="Optimize memory",
    description="Perform memory optimization operations (admin endpoint)"
)
async def optimize_memory():
    """
    Perform memory optimization (admin endpoint).
    
    Returns:
        Memory optimization results
    """
    try:
        results = model_manager.optimize_memory()
        
        return {
            "message": "Memory optimization completed",
            "results": results,
            "timestamp": time.time()
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to optimize memory: {str(e)}"
        )


@app.get(
    "/",
    summary="Root endpoint",
    description="API information and status"
)
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs_url": "/docs" if settings.debug else "disabled",
        "health_url": "/health"
    }


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
            "code": "INTERNAL_ERROR"
        }
    )


# HTTP exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Handler for HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "code": f"HTTP_{exc.status_code}"
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info"
    )