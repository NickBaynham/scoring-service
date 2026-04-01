# syntax=docker/dockerfile:1
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PDM_CHECK_UPDATE=false

RUN pip install --no-cache-dir pdm==2.25.4

WORKDIR /app

COPY pyproject.toml pdm.lock README.md alembic.ini ./
COPY alembic ./alembic
COPY app ./app

RUN pdm config python.use_venv false \
    && pdm install --prod --no-editable --frozen-lockfile

CMD ["pdm", "run", "python", "-m", "app.workers.scoring_worker"]
