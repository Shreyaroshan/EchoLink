# ── STAGE 1: BUILD FRONTEND REACT APP ───────────────────────────────────
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY echolink_frontend/package*.json ./
RUN npm ci
COPY echolink_frontend/ ./
RUN npm run build

# ── STAGE 2: BUILD BACKEND PYTHON SERVER ───────────────────────────────
FROM python:3.12-slim
WORKDIR /app

# Prevent python from writing pyc files and buffering logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install runtime dependencies for psycopg2/database if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy FastAPI backend code
COPY echolink_api/ .

# Copy built frontend assets from Stage 1 into backend's root folder as 'dist'
COPY --from=frontend-builder /app/dist ./dist

# Expose unified application port
EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
