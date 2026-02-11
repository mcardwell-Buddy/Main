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

# Add /app to Python path so Back_End module can be found
ENV PYTHONPATH=/app

# Port 8080 is what Firebase expects
EXPOSE 8080

# Use uvicorn to run the full Buddy backend
CMD exec uvicorn "Back_End.main:app" --host 0.0.0.0 --port 8080
