# syntax=docker/dockerfile:1.7

# --- Builder ---
FROM python:3.12-slim AS builder

ENV POETRY_VERSION=1.8.3 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}" && \
    poetry lock --no-update || true && \
    poetry export -f requirements.txt --without-hashes -o requirements.txt

RUN python -m venv /opt/venv && \
    . /opt/venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn

COPY backend ./backend

# --- Runtime ---
FROM python:3.12-slim AS runtime

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app/backend" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN addgroup --system app && adduser --system --ingroup app app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/backend /app/backend

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:8000/api/v1/health || exit 1

CMD ["sh", "-c", "/opt/venv/bin/gunicorn app.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --workers ${GUNICORN_WORKERS:-2} --timeout ${GUNICORN_TIMEOUT:-60}"]



