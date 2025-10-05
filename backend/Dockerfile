# syntax=docker/dockerfile:1.7

FROM python:3.12-slim

# 환경변수
ENV POETRY_VERSION=1.8.3 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH="/app"

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 작업 디렉토리
WORKDIR /app

# Poetry 및 의존성 설치
COPY pyproject.toml poetry.lock* ./
RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}" && \
    poetry config virtualenvs.create false && \
    poetry install --only main --no-interaction --no-ansi

# 애플리케이션 코드 복사
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY entrypoint.sh ./entrypoint.sh

# 비root 사용자 생성 및 entrypoint 실행 권한
RUN addgroup --system app && adduser --system --ingroup app app && \
    chmod +x /app/entrypoint.sh && \
    chown -R app:app /app && \
    mkdir -p /data && chown -R app:app /data

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${PORT:-8000}/health || exit 1

CMD ["/app/entrypoint.sh"]
