"""Application secrets in Secrets Manager (replace placeholders after deploy)."""

from aws_cdk import SecretValue, Stack
from aws_cdk import aws_secretsmanager as secretsmanager
from constructs import Construct


class SecretsStack(Stack):
    """DATABASE_URL and OPENAI_API_KEY as secrets (scoped IAM in ComputeStack)."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.database_url_secret = secretsmanager.Secret(
            self,
            "DatabaseUrlSecret",
            description="Async SQLAlchemy URL to Postgres (e.g. Docker Postgres in VPC).",
            secret_string_value=SecretValue.unsafe_plain_text(
                "postgresql+asyncpg://scoring:changeme@postgres.internal:5432/scoring",
            ),
        )

        self.openai_api_key_secret = secretsmanager.Secret(
            self,
            "OpenAiApiKeySecret",
            description="OpenAI-compatible API key (rotate after deploy).",
            secret_string_value=SecretValue.unsafe_plain_text("REPLACE_ME"),
        )
