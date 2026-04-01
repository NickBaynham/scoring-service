#!/usr/bin/env python3
"""CDK application entrypoint for VerifiedSignal scoring-service AWS resources."""

import os

from aws_cdk import App, Environment

from stacks.compute_stack import ComputeStack
from stacks.database_stack import PostgresDockerReferenceStack
from stacks.network_stack import NetworkStack
from stacks.secrets_stack import SecretsStack
from stacks.sqs_stack import SqsStack
from stacks.storage_stack import StorageStack

app = App()

account = os.environ.get("CDK_DEFAULT_ACCOUNT")
region = os.environ.get("CDK_DEFAULT_REGION", "us-east-1")
env = Environment(account=account, region=region)

network = NetworkStack(app, "ScoringNetwork", env=env)
storage = StorageStack(app, "ScoringStorage", env=env)
PostgresDockerReferenceStack(app, "ScoringPostgresDocker", env=env)
secrets = SecretsStack(app, "ScoringSecrets", env=env)
sqs_stack = SqsStack(app, "ScoringJobs", env=env)

ComputeStack(
    app,
    "ScoringCompute",
    vpc=network.vpc,
    ecr_repository_name="verifiedsignal/scoring-service",
    document_bucket=storage.bucket,
    database_secret=secrets.database_url_secret,
    openai_secret=secrets.openai_api_key_secret,
    job_queue=sqs_stack.queue,
    env=env,
)

app.synth()
