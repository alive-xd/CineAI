# ── Stage 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install CPU-only PyTorch first (dramatically smaller than CUDA build)
# This must come BEFORE requirements.txt to avoid pip resolving the CUDA version
RUN pip install --no-cache-dir \
    torch==2.3.0 \
    --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the sentence-transformers model so it's baked into the image
# Avoids runtime download on first request (cold start latency)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# ── Stage 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Runtime system deps only
# ca-certificates is REQUIRED for outbound HTTPS (TMDb API calls via httpx)
# python:3.11-slim strips it out — without it TLS handshake fails with ConnectError
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    ca-certificates \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11 /usr/local/lib/python3.11
COPY --from=builder /usr/local/bin /usr/local/bin
# Copy pre-downloaded model
COPY --from=builder /root/.cache/huggingface /root/.cache/huggingface

# Copy application code
COPY . .

# Non-root user for security
RUN useradd -m -u 1001 cineai && chown -R cineai:cineai /app
USER cineai

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# Uvicorn with 2 workers on free tier (512MB RAM constraint)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", \
     "--workers", "2", "--loop", "uvloop", "--access-log"]