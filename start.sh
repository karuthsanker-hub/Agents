#!/bin/sh
# Start script for Railway deployment
# Author: Shiv Sanker

# Default to port 8000 if PORT is not set
PORT=${PORT:-8000}

echo "Starting Arctic Debate Card Agent on port $PORT..."
exec python -m uvicorn server.main:app --host 0.0.0.0 --port $PORT

