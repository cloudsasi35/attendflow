FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy all application files first
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -e .

# Run the application
CMD ["uvicorn", "attendflow.main:app", "--host", "0.0.0.0", "--port", "8000"]
