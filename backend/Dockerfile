FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app

FROM base AS builder
RUN pip install --no-cache-dir uv==0.4.*
COPY pyproject.toml ./
# pyproject sets `readme = "README.md"`, so the build needs it present.
COPY README.md ./
COPY src ./src
RUN uv pip install --system --no-cache .

FROM base AS runtime
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY src ./src
COPY alembic.ini ./
RUN useradd --uid 1000 --create-home app && chown -R app /app
USER app
EXPOSE 8000
CMD ["python", "-m", "vambora.main"]
