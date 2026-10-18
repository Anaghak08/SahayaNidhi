#!/bin/bash
set -e

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install --quiet -r requirements.txt

echo "Starting FastAPI Server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
