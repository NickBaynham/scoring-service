"""ECR, ECS cluster, CloudWatch logs — Fargate-ready compute."""

from aws_cdk import Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_logs as logs
from constructs import Construct


class ComputeStack(Stack):
    """Container registry and ECS cluster for API and worker services."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc: ec2.IVpc,
        ecr_repository_name: str,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.repository = ecr.Repository(
            self,
            "ScoringServiceRepo",
            repository_name=ecr_repository_name,
            image_scan_on_push=True,
        )

        self.cluster = ecs.Cluster(
            self,
            "ScoringCluster",
            vpc=vpc,
            container_insights=True,
        )

        self.api_log_group = logs.LogGroup(
            self,
            "ScoringApiLogs",
            retention=logs.RetentionDays.ONE_MONTH,
        )

        self.worker_log_group = logs.LogGroup(
            self,
            "ScoringWorkerLogs",
            retention=logs.RetentionDays.ONE_MONTH,
        )
