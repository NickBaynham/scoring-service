# scoring-service

Production-oriented **Python** service for **VerifiedSignal**: accept document text or references, run multiple **LLM-based scorers**, aggregate results into a **credibility profile**, persist raw and derived outputs, and expose **async HTTP APIs**. The stack uses **FastAPI**, **Pydantic v2**, **SQLAlchemy 2.x** + **Alembic**, **httpx** for OpenAI-compatible calls, **PDM** for packaging, **Docker** for local and cloud images, **GitHub Actions** for CI/CD, and **AWS CDK (Python)** for infrastructure.

## Why this service exists

Integrators need a single place to submit documents (or text), receive structured credibility signals (logical soundness, verifiability, evidence, consistency, hallucination risk), and poll for completion. The design separates **API** (enqueue) from **workers** (execute LLM pipelines) and stores **auditable** rows for jobs, per-dimension scores, and issue spans.

## Architecture (summary)

1. **POST** `/v1/documents` or supply text on **POST** `/v1/score-jobs`.
2. A **score_jobs** row is created with status `queued`; with **SQS** enabled, the API **commits** then publishes `job_id` to the queue.
3. The **worker** pulls work via **database** polling (`SKIP LOCKED` on Postgres) or **SQS** long-poll, then runs: resolve text → extract claims → run scorers in parallel → aggregate → persist.
4. **GET** `/v1/documents/{id}/scores` returns the latest completed profile for a tenant + profile name.

See [docs/architecture.md](docs/architecture.md) for diagrams and data flow.

## Repository layout

| Path | Purpose |
|------|---------|
| `app/` | FastAPI app, domain services, LLM client, scorers, workers |
| `alembic/` | Database migrations |
| `tests/` | unit, contract, integration, e2e |
| `docker/` | `api.Dockerfile`, `worker.Dockerfile` |
| `infrastructure/cdk/` | AWS CDK Python stacks |
| `docs/` | End-user, developer, architecture, scoring model, API examples, CDK database notes |
| `scripts/` | Bootstrap, wait-for-Postgres, seed data |
| `.github/workflows/` | CI, Docker image build, CDK (manual) |

## Prerequisites

- **Python 3.11+**
- **PDM** ([installation](https://pdm-project.org/latest/))
- **Docker** + **Docker Compose** (for Postgres and containers)
- Optional: **AWS CLI**, **CDK CLI**, **Node.js** (for `cdk` command), **[actionlint](https://github.com/rhysd/actionlint)** (for workflow YAML validation)

## Quick start (local, PDM)

```bash
make install          # or: pdm install -G dev -G test -G lint
cp .env.example .env    # set OPENAI_API_KEY, DATABASE_URL
make docker-up          # start Postgres
make migrate            # alembic upgrade head
# Terminal A:
make dev
# Terminal B:
make worker
```

Open **Swagger UI** at the service root (redirects to `/docs`): http://localhost:8000/

## Static checks and tests (local)

Run the same checks as CI before pushing:

```bash
make check              # ruff check + mypy app + pytest with coverage
```

| Step | What it runs |
|------|----------------|
| **Ruff** | `ruff check app tests` (after `make format` for format + auto-fix) |
| **mypy** | Strict typing on `app/` |
| **pytest** | All tests under `tests/` with coverage report |

Optional **GitHub Actions** workflow validation (install [actionlint](https://github.com/rhysd/actionlint) first):

```bash
make workflow-check
```

**CI** (`.github/workflows/ci.yml`) runs on push/PR to `main`: `pdm install`, `ruff check`, `ruff format --check`, `mypy app`, `pytest` with coverage XML artifact.

## Environment variables

See [.env.example](.env.example) for:

- `APP_ENV`, `APP_HOST`, `APP_PORT`, `LOG_LEVEL`
- `DATABASE_URL` (async URL, e.g. `postgresql+asyncpg://...`)
- `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `MODEL_NAME`, `LLM_*`
- `S3_BUCKET`, `AWS_REGION`, `AWS_ENDPOINT_URL` (optional S3-compatible endpoint)
- `API_KEY` (optional `X-API-Key` header for routes)
- `WORKER_POLL_INTERVAL_SECONDS`
- `JOB_QUEUE_BACKEND` (`database` or `sqs`), `SQS_QUEUE_URL`, `SQS_VISIBILITY_TIMEOUT_SECONDS` (when using SQS)

## Makefile targets

| Target | Description |
|--------|-------------|
| `make help` | List targets |
| `make install` | Install dev + test + lint groups |
| `make sync` | `pdm sync` with lockfile |
| `make format` | Ruff format + `ruff check --fix` |
| `make lint` | Ruff check |
| `make typecheck` | mypy on `app/` |
| `make check` | lint + typecheck + test (CI parity) |
| `make workflow-check` | actionlint on `.github/workflows` (requires `actionlint` on PATH) |
| `make test` | Full pytest + coverage |
| `make test-unit` | Unit tests |
| `make test-contract` | OpenAPI / schema contracts |
| `make test-integration` | Integration tests |
| `make test-e2e` | E2E with mocked LLM |
| `make run` | Uvicorn API |
| `make worker` | Scoring worker |
| `make dev` | API with reload |
| `make docker-build` | Build images |
| `make docker-up` / `make docker-down` | Compose |
| `make migrate` | Alembic upgrade |
| `make revision msg="..."` | New migration |
| `make seed` | Dev seed script |
| `make clean` | Caches |

## Database and migrations

- **Local**: Postgres from `docker-compose.yml` at `postgresql+asyncpg://scoring:scoring@localhost:5432/scoring`.
- **Apply**: `make migrate` (runs `alembic upgrade head`).
- **Create migration**: `make revision msg="describe change"`.

## Testing strategy

| Layer | Scope | Command |
|-------|--------|---------|
| **Unit** | Aggregation, parsing, prompts, job queue factory | `make test-unit` |
| **Contract** | OpenAPI paths and schema | `make test-contract` |
| **Integration** | Health + DB-backed app (in-memory SQLite in tests) | `make test-integration` |
| **E2E** | Document → job → worker → scores with **respx**-mocked LLM | `make test-e2e` |

Tests use **pytest-asyncio** and **httpx** `ASGITransport` against the FastAPI app. Pytest markers: `unit`, `contract`, `integration`, `e2e`.

## API overview

- `GET /health` — liveness and DB readiness.
- `POST /v1/documents` — register a document (optional before scoring).
- `POST /v1/score-jobs` — enqueue scoring (`202` + `job_id`); commits then **SQS notify** when `JOB_QUEUE_BACKEND=sqs`.
- `GET /v1/score-jobs/{job_id}?tenant_id=...` — job status.
- `GET /v1/documents/{document_id}/scores?tenant_id=...&profile=credibility_v1` — latest scores.

**OpenAPI**: `/` redirects to **Swagger UI** (`/docs`); machine-readable spec at `/openapi.json` and **ReDoc** at `/redoc`. Example curls: [docs/api-examples.md](docs/api-examples.md).

## Scoring model

Dimensions and aggregation formula: [docs/scoring-model.md](docs/scoring-model.md).

## Docker

```bash
export OPENAI_API_KEY=sk-...
make docker-build
make docker-up
make migrate   # from host with DATABASE_URL pointing at localhost:5432
```

Images: `docker/api.Dockerfile`, `docker/worker.Dockerfile`.

## GitHub Actions

| Workflow | When | What |
|----------|------|------|
| **`ci.yml`** | Push/PR to `main` | PDM install, ruff check + format check, mypy, pytest + coverage artifact |
| **`docker.yml`** | Manual `workflow_dispatch` (optional push) or tags `v*` | Build/push **two** images (`*-api`, `*-worker`) to registry. Configure repository **variables** `CONTAINER_REGISTRY`, `IMAGE_NAME` and secrets `REGISTRY_USERNAME`, `REGISTRY_PASSWORD` (or `GITHUB_TOKEN` for GHCR) |
| **`cdk.yml`** | Manual only | `synth`, `diff`, `deploy`, `destroy`. Set `AWS_ROLE_ARN` secret for OIDC/role assumption when needed |

## AWS CDK

Infrastructure lives in `infrastructure/cdk/`:

```bash
cd infrastructure/cdk
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
npm install -g aws-cdk@2   # optional if not installed
cdk bootstrap aws://ACCOUNT/REGION
cdk synth
cdk diff
cdk deploy --all
# cdk destroy --all   # when tearing down
```

Stacks: **Network** (VPC), **Storage** (S3), **PostgresDocker** (CloudFormation outputs with a `docker-compose` Postgres template — **no RDS bill**), **Secrets** (DATABASE_URL + OPENAI placeholders in Secrets Manager), **Jobs** (SQS queue), **Compute** (ECR, IAM roles, **ALB + Fargate API**, **Fargate worker**, CloudWatch logs). Point `DATABASE_URL` in Secrets Manager at **self-hosted Postgres** (Docker on EC2/ECS in the VPC, or an external host). See [docs/cdk-database.md](docs/cdk-database.md).

## Troubleshooting

- **503 on `/health`**: Postgres unreachable — check `DATABASE_URL` and `docker compose ps`.
- **Jobs stuck queued**: ensure the **worker** is running and can reach the DB; check `DATABASE_URL` matches. With **SQS**, confirm `SQS_QUEUE_URL`, IAM permissions, and that the API can `SendMessage` after commit.
- **LLM errors**: verify `OPENAI_BASE_URL` and `OPENAI_API_KEY`; see logs with `LOG_LEVEL=DEBUG`.
- **S3 text fetch**: set `AWS_*` and `S3_BUCKET`; for LocalStack/MinIO set `AWS_ENDPOINT_URL`.

## Future improvements

- **SQS** queue supports DLQ, FIFO, or multi-queue routing if product needs it.
- Add **OpenTelemetry** exporters when `OTEL_EXPORTER_OTLP_ENDPOINT` is set.
- Per-tenant rate limits and **JWT** auth.
- Separate read models for analytics and dashboards.

## License

See [LICENSE](LICENSE).
