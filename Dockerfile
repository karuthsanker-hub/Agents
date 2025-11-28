# Dockerfile for Arctic Debate Card Agent
# Author: Shiv Sanker
# Optimized for Railway deployment

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for Docker cache)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for persistent data
RUN mkdir -p /app/chroma_db /app/logs

# Make start script executable
RUN chmod +x start.sh

# Railway uses PORT environment variable
EXPOSE ${PORT}

# Run the application (Railway sets PORT)
CMD ["sh", "start.sh"]

