#!/bin/zsh
# -------------------------------
# Dev Runner for TheButtonApp
# -------------------------------

PORT=8003
VENV_PATH="./.venv/bin/activate"

echo "🔹 Stopping any running uvicorn/python processes..."
pkill -f uvicorn
pkill -f python

sleep 1

echo "🔹 Checking if port $PORT is free..."
if lsof -i :$PORT >/dev/null; then
    echo "⚠️ Port $PORT still in use. Attempting to free it..."
    PID=$(lsof -ti :$PORT)
    sudo kill -9 $PID
    sleep 1
fi

echo "🔹 Activating virtual environment..."
source $VENV_PATH

# Use python3 explicitly in case python points to system Python
PYTHON_BIN=$(which python3)
echo "🔹 Using Python at: $PYTHON_BIN"

echo "🔹 Starting uvicorn on http://127.0.0.1:$PORT ..."
$PYTHON_BIN -m uvicorn app.main:app --host 127.0.0.1 --port $PORT --reload --log-level debug &

sleep 2
echo "🔹 Opening browser to http://127.0.0.1:$PORT/docs ..."
open http://127.0.0.1:$PORT/docs

echo "✅ Dev Runner finished. App should be running."

