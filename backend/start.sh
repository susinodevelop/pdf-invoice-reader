#!/bin/sh
# Script to start the FastAPI server via Uvicorn using the factory pattern.
# Read port from environment variable BACKEND_PORT or default to 8080.
PORT=${BACKEND_PORT:-8080}

exec uvicorn api.main:create_app --factory --host 0.0.0.0 --port "$PORT"
