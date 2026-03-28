"""
VerifAI Backend — FastAPI server for misinformation analysis.
Serves React frontend (dist/) in production, API on /api/*.
"""

import os
from pathlib import Path
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Optional
import uvicorn

from routes.analyze import router as analyze_router

app = FastAPI(
    title="VerifAI API",
    description="Misinformation Intelligence Backend",
    version="1.0.0"
)

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
        "gemini_configured": bool(os.environ.get("GEMINI_API_KEY")),
        "news_configured": bool(os.environ.get("NEWS_API_KEY")),
    }

# Serve React frontend in production
DIST_DIR = Path(__file__).resolve().parent.parent / "dist"
if DIST_DIR.exists():
    # Serve static assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory=str(DIST_DIR / "assets")), name="assets")

    # Catch-all: serve index.html for SPA client-side routing
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        file_path = DIST_DIR / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(DIST_DIR / "index.html"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8001))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
