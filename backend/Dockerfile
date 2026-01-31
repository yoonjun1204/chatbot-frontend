# backend/Dockerfile
FROM python:3.14-slim

# Set working directory inside the container
WORKDIR /app

# Install system dependencies (needed for psycopg2 & friends)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend code
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Run seed script, then start the app
# Use /bin/bash -c to chain commands together
CMD ["/bin/bash", "-c", "python seed.py && uvicorn main:app --host 0.0.0.0 --port $PORT"]
