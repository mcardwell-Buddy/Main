FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Buddy code
COPY . .

# Port 8080 is what Firebase expects
EXPOSE 8080

# Use gunicorn to run the FastAPI app
CMD exec gunicorn --bind :8080 --workers 1 --timeout 0 backend.main:app
