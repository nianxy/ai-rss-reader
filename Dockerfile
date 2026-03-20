FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

WORKDIR /app

# Minimal runtime deps
# RUN apt-get update \
#     && apt-get install -y --no-install-recommends ca-certificates \
#     && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for better layer caching.
COPY pyproject.toml README.md ./
COPY app ./app
RUN pip install --upgrade pip \
    && pip install --index-url "${PIP_INDEX_URL}" --trusted-host "${PIP_TRUSTED_HOST}" .

# Copy runtime files
COPY alembic.ini ./
COPY alembic ./alembic
COPY config ./config
COPY scripts ./scripts
COPY .env.example ./

# Create non-root user
RUN useradd -m -u 10001 appuser \
    && mkdir -p /app/data/digests \
    && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
