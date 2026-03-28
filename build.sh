#!/usr/bin/env bash
# Render Build Script — builds React frontend + installs Python deps

set -e

echo "=== Installing Node.js dependencies ==="
npm install

echo "=== Building React frontend ==="
npm run build

echo "=== Installing Python dependencies ==="
cd backend
pip install -r requirements.txt
cd ..

echo "=== Build complete ==="
echo "Frontend built to dist/"
echo "Backend deps installed"
