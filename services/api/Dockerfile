# ═══════════════════════════════════════════════════════════════════════════════
# Feltabout API — Production Dockerfile for services/api
# ═══════════════════════════════════════════════════════════════════════════════
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─── Runtime stage ────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies including curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    espeak-ng \
    && rm -rf /var/lib/apt/lists/*

# Install Piper TTS
RUN pip install --no-cache-dir piper-tts

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Copy Piper voice models (bundled for production)
COPY models/piper/ /app/models/piper/

# Create non-root user for security
RUN useradd -m -r -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Health check - FastAPI /health endpoint
HEALTHCHECK --interval=10s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# All config via environment variables (see .env.example)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]