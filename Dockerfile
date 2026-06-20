# =============================================================
# ESTIA — AI Multimodal Hotel Concierge Assistant
# Production Dockerfile
# =============================================================

# ── Stage 1: dependency builder ────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt


# ── Stage 2: production image ──────────────────────────────────
FROM python:3.11-slim AS production

# Non-root user for security
RUN addgroup --system estia && adduser --system --group estia

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /root/.local /home/estia/.local

# Copy application code
COPY app/       ./app/
COPY static/    ./static/
COPY knowledge/ ./knowledge/

# ChromaDB data volume mount point
RUN mkdir -p /app/chroma_db && chown -R estia:estia /app

USER estia

# Make sure scripts in .local are usable
ENV PATH=/home/estia/.local/bin:$PATH
ENV PYTHONPATH=/app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD python -c "import httpx; httpx.get('http://localhost:8000/health').raise_for_status()"

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
