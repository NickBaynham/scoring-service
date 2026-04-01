"""No RDS — reference outputs for self-hosted Postgres (Docker) to control cost."""

from aws_cdk import CfnOutput, Stack
from constructs import Construct

_DOCKER_COMPOSE = """version: "3.8"
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: scoring
      POSTGRES_PASSWORD: changeme
      POSTGRES_DB: scoring
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
volumes:
  pgdata: {}
"""


class PostgresDockerReferenceStack(Stack):
    """Emits a docker-compose snippet and connection hints (no billable RDS)."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        CfnOutput(
            self,
            "DockerComposePostgres",
            description="Run Postgres locally or on an EC2/ECS host with Docker.",
            value=_DOCKER_COMPOSE,
        )
        CfnOutput(
            self,
            "AsyncDatabaseUrlExample",
            description="Use this shape in Secrets Manager (DATABASE_URL secret).",
            value="postgresql+asyncpg://scoring:changeme@<postgres-host>:5432/scoring",
        )
