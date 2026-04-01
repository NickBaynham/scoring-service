# Database strategy for AWS (CDK)

This project **does not** provision **RDS** by default to avoid fixed monthly cost. Postgres is expected to run where you control cost and networking:

## Recommended: Docker Postgres

1. **Local / CI**: use root `docker-compose.yml` (same as the main README).
2. **AWS**: run Postgres in **Docker** on an **EC2** instance or on a **self-managed** host in the VPC, or use an external managed Postgres you already own.
3. **CDK**: stack `ScoringPostgresDocker` outputs a **docker-compose** snippet you can adapt. Copy the `AsyncDatabaseUrlExample` output value shape for `DATABASE_URL` (async URL with `postgresql+asyncpg://`).

## Wiring Secrets Manager

The `ScoringSecrets` stack creates two secrets (CDK construct IDs `DatabaseUrlSecret` and `OpenAiApiKeySecret`):

- **Database URL** — set the secret string to your full async SQLAlchemy URL (e.g. `postgresql+asyncpg://user:pass@host:5432/dbname`).
- **OpenAI API key** — set the secret string to your OpenAI-compatible API key.

The placeholder values in the synthesized template are **not** production-safe; **replace** them in the AWS Console or via CLI after deploy, then rotate regularly.

## Security groups

Allow ECS tasks (private subnets) to reach Postgres on **TCP 5432** from the worker and API **security groups** (or a shared Postgres SG). The CDK does not open RDS because no RDS is created.

## When you want RDS

Add a separate stack or enable a **context flag** that provisions `rds.DatabaseInstance` — tune instance class, Multi-AZ, and backups for production. Keep `DATABASE_URL` in Secrets Manager pointing at the RDS endpoint after creation.
