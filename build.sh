#!/usr/bin/env bash
# Render Build Script — Backend only (Frontend is deployed separately on Netlify)
# https://fluffy-bombolone-5fa6b1.netlify.app/

set -e

echo "=== VerifAI Backend Build ==="
echo "Python version: $(python --version)"

echo "=== Installing Python dependencies ==="
cd backend
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Build complete ==="
echo "Backend ready. Start with: uvicorn main:app --host 0.0.0.0 --port \$PORT"
