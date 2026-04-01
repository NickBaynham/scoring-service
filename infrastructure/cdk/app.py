#!/usr/bin/env python3
"""CDK application entrypoint for VerifiedSignal scoring-service AWS resources."""

import os

import aws_cdk as cdk

from stacks.compute_stack import ComputeStack
from stacks.database_stack import DatabaseStack
from stacks.iam_stack import IamStack
from stacks.network_stack import NetworkStack
from stacks.storage_stack import StorageStack

app = cdk.App()

account = os.environ.get("CDK_DEFAULT_ACCOUNT")
region = os.environ.get("CDK_DEFAULT_REGION", "us-east-1")
env = cdk.Environment(account=account, region=region)

network = NetworkStack(app, "ScoringNetwork", env=env)
storage = StorageStack(app, "ScoringStorage", env=env)
DatabaseStack(app, "ScoringDatabase", vpc=network.vpc, env=env)
IamStack(app, "ScoringIam", document_bucket=storage.bucket, env=env)
ComputeStack(
    app,
    "ScoringCompute",
    vpc=network.vpc,
    ecr_repository_name="verifiedsignal/scoring-service",
    env=env,
)

app.synth()
