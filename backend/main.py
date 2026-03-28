"""
VerifAI Backend — FastAPI server for misinformation analysis.
Runs locally, uses Gemini Flash (free tier) for LLM inference.
"""

import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
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
    return {"status": "ok", "service": "VerifAI"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
