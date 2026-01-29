"""
FastAPI Backend for SynthFHIR
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
import os

# Import routes
from api.routes import config, generation, knowledge, llm, export as export_routes

# Create FastAPI app
app = FastAPI(
    title="SynthFHIR API",
    description="Synthetic FHIR Data Generation Backend",
    version="1.0.0"
)

# Configure CORS
origins = [
    "http://localhost:3000",  # Next.js dev server
    "http://localhost:8000",  # FastAPI docs
    "https://synthfhir-frontend.vercel.app",  # Production frontend
    "*",  # Allow all origins for development (remove in production)
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(config.router, prefix="/api", tags=["Config"])
app.include_router(generation.router, prefix="/api", tags=["Generation"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge"])
app.include_router(llm.router, prefix="/api/llm", tags=["LLM"])
app.include_router(export_routes.router, prefix="/api", tags=["Export"])

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "SynthFHIR API"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "SynthFHIR API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for better error responses"""
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
