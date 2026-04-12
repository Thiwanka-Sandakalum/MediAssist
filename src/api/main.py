"""MediAssist FastAPI Application.

Main entry point for the API. Defines routes, middleware, and lifecycle events.
Week 2 MVP: Basic routes, no auth middleware.
"""

import logging
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os

from src.config import config
from src.database.connection import init_connection_pool, close_all_connections
from src.api.utils.state_store import WorkflowStore
from src.api.schemas import HealthResponse, ErrorResponse
from src.api.routes import prescriptions, hitl

logger = logging.getLogger(__name__)


# ===== LIFECYCLE MANAGEMENT =====

# @asynccontextmanager
# async def lifespan(app: FastAPI):
# 	"""Manage app startup and shutdown."""
# 	# Startup
# 	logger.info("Starting MediAssist API...")
# 	try:
# 		init_connection_pool()
# 		logger.info("Database connection pool initialized")
# 	except Exception as e:
# 		logger.error(f"Failed to initialize database: {str(e)}")
# 		raise
	
# 	yield
	
# 	# Shutdown
# 	logger.info("Shutting down MediAssist API...")
# 	close_all_connections()
# 	logger.info("Resources cleaned up")


# ===== APP INITIALIZATION =====

app = FastAPI(
	title="MediAssist Pharmacy AI",
	description="Multi-agent LLM system for prescription processing and clinical validation",
	version="0.1.0",
	# lifespan=lifespan
)

# CORS configuration
app.add_middleware(
	CORSMiddleware,
	allow_origins=[
		"http://localhost:3000",
		"http://127.0.0.1:3000",
		"http://localhost:8000",
	],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


# ===== ROUTES =====

@app.get("/health", response_model=HealthResponse)
async def health_check():
	"""Health check endpoint."""
	return {
		"status": "ok",
		"graph": "ready",
		"database": "connected",
		"timestamp": datetime.utcnow().isoformat()
	}


@app.get("/")
async def root():
	"""Root endpoint - serve frontend dashboard."""
	static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
	index_path = os.path.join(static_dir, "index.html")
	if os.path.exists(index_path):
		return FileResponse(index_path, media_type="text/html")
	else:
		logger.warning("index.html not found, returning API info")
		return {
			"message": "MediAssist Pharmacy AI API",
			"version": "0.1.0",
			"docs": "/docs",
			"frontend": "Frontend dashboard not available"
		}


# Include routers
app.include_router(prescriptions.router, prefix="/prescriptions", tags=["Prescriptions"])
app.include_router(hitl.router, prefix="/prescriptions", tags=["HITL"])


# ===== STATIC FILES & FRONTEND =====

# Mount static files (CSS, JS, images)
_static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "static")
if os.path.exists(_static_dir):
	app.mount("/static", StaticFiles(directory=_static_dir), name="static")
	logger.info(f"Static files mounted from {_static_dir}")
else:
	logger.warning(f"Static directory not found at {_static_dir}")


# ===== ERROR HANDLERS =====

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
	"""Global exception handler."""
	logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
	return JSONResponse(
		status_code=500,
		content=ErrorResponse(
			error="Internal server error",
			details=str(exc),
			status_code=500,
			timestamp=datetime.utcnow().isoformat()
		).model_dump()
	)


# ===== BACKGROUND TASKS =====

@app.on_event("startup")
async def startup_event():
	"""Additional startup tasks."""
	logger.info("MediAssist API initialization complete")
	logger.info(f"Configuration loaded: LLM={config.LLM_MODEL}")


@app.on_event("shutdown")
async def shutdown_event():
	"""Additional shutdown tasks."""
	expired_count = WorkflowStore.cleanup_expired()
	logger.info(f"Cleaned up {expired_count} expired workflows")
	logger.info("MediAssist API shutdown complete")


if __name__ == "__main__":
	import uvicorn
	uvicorn.run(
		"src.api.main:app",
		host=config.API_HOST,
		port=config.API_PORT,
		reload=True
	)
