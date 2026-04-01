# Architecture

## Request flow (API)

```mermaid
flowchart LR
  Client --> FastAPI
  FastAPI --> Services
  Services --> Repositories
  Repositories --> Postgres
```

HTTP handlers stay thin; **services** orchestrate validation and persistence; **repositories** encapsulate SQLAlchemy queries.

## Async job flow

1. Client creates a **score_jobs** row with status `queued`.
2. **Database queue**: worker calls `DatabaseJobQueue.dequeue_job_id()`, which **claims** one row (Postgres: `FOR UPDATE SKIP LOCKED`) and sets status `running`.
3. **SQS queue**: API commits the row, then sends `{"job_id": "..."}` to SQS; worker long-polls `SqsJobQueue`, marks the job `running` if still `queued`, then deletes the message after a successful run.
4. `run_scoring_pipeline` resolves text (inline, document, or S3), runs claim extraction, runs scorers concurrently, persists **score_results** and **score_spans**, updates job `completed` or `failed`.

## LLM interaction

- `OpenAICompatibleClient` uses **httpx** to call `/chat/completions` with `response_format: json_object`.
- Prompts require **JSON only**; `app/llm/parser.py` validates against Pydantic models.

## Data persistence

- **documents** — tenant-scoped content and metadata.
- **score_jobs** — async units of work.
- **score_results** — one row per dimension per job (`score_name`, `score_value`, `confidence`, `rationale_json`).
- **score_spans** — optional normalized issue rows linked to a result.
- **claims** — optional extracted claims for audit trails.

## Deployment model

- **Docker**: API and worker containers share the same image build pattern (PDM install prod).
- **AWS (CDK)**: VPC, S3, Secrets Manager, SQS job queue, ECR, IAM (inside Compute stack), ALB + Fargate API, Fargate worker, CloudWatch logs. Postgres is **self-managed** (e.g. Docker) or external — see [cdk-database.md](cdk-database.md).
