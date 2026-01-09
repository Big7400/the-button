#!/bin/bash

echo "=============================="
echo "🚀 Starting TheButtonApp"
echo "=============================="

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
VENV_PATH="$PROJECT_ROOT/.venv"
PORT=8001

# 1️⃣ Activate virtual environment
if [ -d "$VENV_PATH" ]; then
    echo "✅ Activating virtual environment..."
    source "$VENV_PATH/bin/activate"
else
    echo "❌ Virtual environment not found at $VENV_PATH"
    echo "Create it with: python3 -m venv .venv"
    exit 1
fi

# 2️⃣ Kill any process on the port
echo "🔍 Checking for processes on port $PORT..."
PIDS=$(lsof -ti :$PORT)

if [ -n "$PIDS" ]; then
    echo "⚠️  Killing existing processes on port $PORT: $PIDS"
    kill -9 $PIDS
else
    echo "✅ Port $PORT is free"
fi

# 3️⃣ Start FastAPI
echo "🚀 Launching FastAPI..."
uvicorn app.main:app \
    --reload \
    --host 0.0.0.0 \
    --port $PORT

echo "=============================="
