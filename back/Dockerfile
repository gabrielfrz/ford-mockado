# syntax=docker/dockerfile:1

FROM python:3.11-slim-bookworm AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    VIRTUAL_ENV=/opt/venv
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN python -m venv "${VIRTUAL_ENV}"

WORKDIR /build
COPY requirements_install.txt ./
RUN pip install --requirement requirements_install.txt

FROM python:3.11-slim-bookworm AS runtime

ARG IMAGE_VERSION=0.1.0
LABEL org.opencontainers.image.title="dashboarddr-back" \
    org.opencontainers.image.description="D&R Dashboard FastAPI backend" \
    org.opencontainers.image.version="${IMAGE_VERSION}"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    VIRTUAL_ENV=/opt/venv \
    PORT=8080
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"

RUN groupadd --gid 10001 app \
    && useradd --uid 10001 --gid app --create-home --home-dir /home/app app

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=app:app app/main.py ./app/main.py
COPY --chown=app:app app/openapi.py ./app/openapi.py
COPY --chown=app:app app/core ./app/core
COPY --chown=app:app app/controllers ./app/controllers
COPY --chown=app:app app/routes ./app/routes
COPY --chown=app:app app/schemas ./app/schemas
COPY --chown=app:app app/services ./app/services
COPY --chown=app:app scripts ./scripts

# The API writes its normal logs to stdout. The refresh runner also keeps a
# per-execution file, so its directory must be writable by the non-root user.
RUN mkdir -p /app/logs && chown -R app:app /app

USER 10001:10001

EXPOSE 8080
STOPSIGNAL SIGTERM

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.getenv('PORT', '8080') + '/openapi.json', timeout=3)" || exit 1

CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port \"${PORT:-8080}\""]
