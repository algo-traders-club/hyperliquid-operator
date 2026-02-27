FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:0.10.7 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

FROM python:3.12-slim
RUN groupadd -g 10001 app && useradd -u 10000 -g app -m appuser \
    && mkdir -p /data && chown appuser:app /data
WORKDIR /app
COPY --from=builder --chown=appuser:app /app /app
ENV PATH="/app/.venv/bin:$PATH"
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD ["hl-op", "health", "--quiet"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
