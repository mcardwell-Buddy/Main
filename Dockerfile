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

# Use uvicorn to run the FastAPI app
CMD exec uvicorn backend.main:app --host 0.0.0.0 --port 8080
