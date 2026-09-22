# ============================================
# VoiceGuard API - Multi-stage Dockerfile
# ============================================
# Stage 1: CPU-only production image (default)
# Build with --build-arg COMPUTE=gpu for GPU
# ============================================

ARG PYTHON_VERSION=3.11
ARG COMPUTE=cpu

# -----------------------------------------------
# Base stage: shared system deps
# -----------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS base

WORKDIR /app

# Non-interactive frontend for apt
ENV DEBIAN_FRONTEND=noninteractive

# System dependencies for audio processing (libsndfile, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libsndfile1 \
    libsndfile1-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for runtime
RUN groupadd --gid 1000 voiceguard \
    && useradd --uid 1000 --gid voiceguard --shell /bin/bash --create-home voiceguard

# -----------------------------------------------
# Dependencies stage: install Python packages
# -----------------------------------------------
FROM base AS dependencies

COPY requirements.txt .

# Install CPU-only PyTorch first if COMPUTE=cpu to avoid pulling CUDA libs
ARG COMPUTE
RUN if [ "$COMPUTE" = "cpu" ]; then \
        pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu; \
    fi

# Install remaining requirements (torch will be skipped if already installed)
RUN pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------
# Production stage
# -----------------------------------------------
FROM base AS production

# Copy installed packages from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code (model weights are NOT copied — they are mounted at runtime)
COPY --chown=voiceguard:voiceguard . .

# Remove files that should never be in the image
RUN rm -rf venv .venv __pycache__ .pytest_cache tests evaluation .env .env.* .git .DS_Store

# Create model mount point with correct permissions
RUN mkdir -p /app/model_weights && chown voiceguard:voiceguard /app/model_weights

# Create writable cache directories
RUN mkdir -p /home/voiceguard/.cache && chown -R voiceguard:voiceguard /home/voiceguard/.cache

# Switch to non-root user
USER voiceguard

# Default environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENV=production \
    PORT=8000 \
    AASIST_MODEL_PATH=/app/model_weights/aasist \
    SPEECHBRAIN_CACHE_DIR=/app/model_weights/speechbrain

EXPOSE 8000

# Health check: the API returns 503 if Postgres/Redis are down
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--timeout-keep-alive", "120"]
