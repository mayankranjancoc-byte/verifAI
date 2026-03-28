"""
Vercel Serverless Function — wraps FastAPI app for serverless deployment.
Routes /api/* requests to the FastAPI backend.

Environment variables (GEMINI_API_KEY, NEWS_API_KEY, etc.) must be set
in the Vercel dashboard under Project Settings > Environment Variables.
"""

import sys
import os

# Add backend to Python path so pipeline imports work
backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend')
sys.path.insert(0, backend_dir)

# Also try loading .env for local testing (won't exist on Vercel)
try:
    from dotenv import load_dotenv
    env_path = os.path.join(backend_dir, '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
except ImportError:
    pass

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routes
from routes.analyze import router as analyze_router

app = FastAPI(title="VerifAI API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(analyze_router, prefix="/api")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "VerifAI",
        "runtime": "vercel-serverless",
        "gemini_configured": bool(os.environ.get("GEMINI_API_KEY")),
        "news_configured": bool(os.environ.get("NEWS_API_KEY")),
    }
