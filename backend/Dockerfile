# ─────────────────────────────────────────────────────────────────────────────
# RelateFX Backend — Production Dockerfile
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ─── Runtime stage ────────────────────────────────────────────────────────────
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application code
COPY . .

# Run as non-root
RUN useradd -m -r -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# All config via environment variables (see .env.example)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]