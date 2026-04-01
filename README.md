# scoring-service

Production-oriented **Python** service for **VerifiedSignal**: accept document text or references, run multiple **LLM-based scorers**, aggregate results into a **credibility profile**, persist raw and derived outputs, and expose **async HTTP APIs**. The stack uses **FastAPI**, **Pydantic v2**, **SQLAlchemy 2.x** + **Alembic**, **httpx** for OpenAI-compatible calls, **PDM** for packaging, **Docker** for local and cloud images, **GitHub Actions** for CI/CD, and **AWS CDK (Python)** for infrastructure.

## Why this service exists

Integrators need a single place to submit documents (or text), receive structured credibility signals (logical soundness, verifiability, evidence, consistency, hallucination risk), and poll for completion. The design separates **API** (enqueue) from **workers** (execute LLM pipelines) and stores **auditable** rows for jobs, per-dimension scores, and issue spans.

## Architecture (summary)

1. **POST** `/v1/documents` or supply text on **POST** `/v1/score-jobs`.
2. A **score job** row is created with status `queued`.
3. The **worker** claims jobs from Postgres (`SKIP LOCKED` on supported engines) and runs: resolve text → extract claims → run scorers in parallel → aggregate → persist.
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
| `docs/` | End-user, developer, architecture, scoring model, API examples |
| `scripts/` | Bootstrap, wait-for-Postgres, seed data |

## Prerequisites

- **Python 3.11+**
- **PDM** ([installation](https://pdm-project.org/latest/))
- **Docker** + **Docker Compose** (for Postgres and containers)
- Optional: **AWS CLI**, **CDK CLI**, **Node.js** (for `cdk` command)

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

Open **Swagger UI**: http://localhost:8000/docs

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
| `make format` | Ruff format + auto-fix |
| `make lint` | Ruff check |
| `make typecheck` | mypy on `app/` |
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
| **Unit** | Aggregation, parsing, prompts | `make test-unit` |
| **Contract** | OpenAPI paths and schema | `make test-contract` |
| **Integration** | Health + DB-backed app (in-memory SQLite in tests) | `make test-integration` |
| **E2E** | Document → job → worker → scores with **respx**-mocked LLM | `make test-e2e` |

Tests use **pytest-asyncio** and **httpx** `ASGITransport` against the FastAPI app.

## API overview

- `GET /health` — liveness and DB readiness.
- `POST /v1/documents` — register a document (optional before scoring).
- `POST /v1/score-jobs` — enqueue scoring (`202` + `job_id`).
- `GET /v1/score-jobs/{job_id}?tenant_id=...` — job status.
- `GET /v1/documents/{document_id}/scores?tenant_id=...&profile=credibility_v1` — latest scores.

**OpenAPI**: `/docs` and `/openapi.json`. Example curls: [docs/api-examples.md](docs/api-examples.md).

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

- **`.github/workflows/ci.yml`** — on every push/PR: PDM install, ruff, mypy, pytest coverage.
- **`.github/workflows/docker.yml`** — **manual** (`workflow_dispatch`) or **tags** `v*`: build/push API and worker images. Set `CONTAINER_REGISTRY`, `IMAGE_NAME`, and registry credentials as secrets/variables.
- **`.github/workflows/cdk.yml`** — **manual only**: `synth`, `diff`, `deploy`, `destroy`. AWS resources are **not** created automatically on push.

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
- **Jobs stuck queued**: ensure the **worker** is running and can reach the DB; check `DATABASE_URL` matches.
- **LLM errors**: verify `OPENAI_BASE_URL` and `OPENAI_API_KEY`; see logs with `LOG_LEVEL=DEBUG`.
- **S3 text fetch**: set `AWS_*` and `S3_BUCKET`; for LocalStack/MinIO set `AWS_ENDPOINT_URL`.

## Future improvements

- Optional **SQS** job queue is implemented (`JOB_QUEUE_BACKEND=sqs`); extend with dead-letter queues or FIFO if needed.
- Add **OpenTelemetry** exporters when `OTEL_EXPORTER_OTLP_ENDPOINT` is set.
- Per-tenant rate limits and **JWT** auth.
- Separate read models for analytics and dashboards.

## License

See [LICENSE](LICENSE).
