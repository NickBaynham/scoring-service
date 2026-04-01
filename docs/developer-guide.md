# Developer guide

## Local workflow

1. `make install` — install PDM groups.
2. `cp .env.example .env` — configure DB and LLM.
3. `make docker-up` — Postgres.
4. `make migrate` — schema.
5. `make dev` + `make worker` — API and worker.

## Static checks before you push

CI runs **Ruff** (lint + format check), **mypy** on `app/`, and **pytest** with coverage. Reproduce locally:

```bash
make format   # optional: ruff format + apply safe fixes
make check    # lint + typecheck + full test suite (same spirit as CI)
```

Optional: validate GitHub Actions YAML if you have [actionlint](https://github.com/rhysd/actionlint) installed:

```bash
make workflow-check
```

## Adding a scorer

1. Add a `ScoreDimension` value (or reuse an existing profile dimension).
2. Subclass `app/scorers/base.py::BaseScorer`.
3. Register the scorer in `app/services/scoring_service.py::build_scorers`.
4. Add prompt text in `app/llm/prompts.py` and structured schema in `app/llm/schemas.py` if the output shape changes.
5. Extend aggregation in `app/services/aggregation.py` if weights change.
6. Add unit tests and an e2e mock path.

## Prompts and versions

- Prompt strings live in `app/llm/prompts.py`; bump `prompt_version` on `BaseScorer` when behavior changes.
- Score profile version is stored on jobs (`profile_version`) for reproducibility.

## Migrations

```bash
make revision msg="add column foo"
make migrate
```

Use Alembic for all production schema changes; avoid `create_all` outside tests.

## Testing patterns

- **Unit**: pure functions (aggregation, parsers, prompt builders, `build_job_queue` factory).
- **Contract**: `/openapi.json` shape and required paths.
- **Integration**: ASGI client + overridden DB session (SQLite in memory).
- **E2E**: `respx` mocks for `POST .../chat/completions` — full job lifecycle.

Pytest markers: `@pytest.mark.unit`, `contract`, `integration`, `e2e` (see `pyproject.toml` `[tool.pytest.ini_options]`).

## Debugging the worker

- Ensure `DATABASE_URL` matches the API.
- Watch logs for `job_id` and `correlation_id` (`X-Request-ID` on HTTP).
- For SQLite tests, dequeue uses a simple `SELECT` without `SKIP LOCKED` semantics.
- **SQS mode** (`JOB_QUEUE_BACKEND=sqs`): API must be able to `SendMessage` and workers must `ReceiveMessage`/`DeleteMessage` on the same queue. After `POST /v1/score-jobs`, the handler **commits** the transaction, then `notify_job_enqueued` sends the `job_id` JSON payload.
