"""IAM roles, ECR, ALB, Fargate API + worker (single stack avoids IAM↔ECR cycles)."""

from aws_cdk import CfnOutput, Duration, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr as ecr
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_ecs_patterns as ecs_patterns
from aws_cdk import aws_iam as iam
from aws_cdk import aws_logs as logs
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_secretsmanager as secretsmanager
from aws_cdk import aws_sqs as sqs
from constructs import Construct


class ComputeStack(Stack):
    """ECR, public ALB → API tasks, private worker tasks, CloudWatch logs."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc: ec2.IVpc,
        ecr_repository_name: str,
        document_bucket: s3.IBucket,
        database_secret: secretsmanager.ISecret,
        openai_secret: secretsmanager.ISecret,
        job_queue: sqs.IQueue,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.task_execution_role = iam.Role(
            self,
            "EcsTaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AmazonECSTaskExecutionRolePolicy",
                ),
            ],
        )

        self.task_role = iam.Role(
            self,
            "EcsTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

        document_bucket.grant_read_write(self.task_role)

        self.task_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "sqs:SendMessage",
                    "sqs:ReceiveMessage",
                    "sqs:DeleteMessage",
                    "sqs:GetQueueAttributes",
                    "sqs:GetQueueUrl",
                    "sqs:ChangeMessageVisibility",
                ],
                resources=[job_queue.queue_arn],
            ),
        )

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

        database_secret.grant_read(self.task_execution_role)
        openai_secret.grant_read(self.task_execution_role)

        region = Stack.of(self).region
        common_env = {
            "APP_ENV": "prod",
            "AWS_REGION": region,
            "S3_BUCKET": document_bucket.bucket_name,
            "OPENAI_BASE_URL": "https://api.openai.com/v1",
            "MODEL_NAME": "gpt-4o-mini",
            "JOB_QUEUE_BACKEND": "sqs",
            "SQS_QUEUE_URL": job_queue.queue_url,
            "LOG_LEVEL": "INFO",
        }

        common_secrets = {
            "DATABASE_URL": ecs.Secret.from_secrets_manager(database_secret),
            "OPENAI_API_KEY": ecs.Secret.from_secrets_manager(openai_secret),
        }

        api_task = ecs.FargateTaskDefinition(
            self,
            "ApiTaskDef",
            cpu=512,
            memory_limit_mib=1024,
            execution_role=self.task_execution_role,
            task_role=self.task_role,
        )

        api_task.add_container(
            "api",
            image=ecs.ContainerImage.from_ecr_repository(self.repository, tag="api-latest"),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="api",
                log_group=self.api_log_group,
            ),
            environment={
                **common_env,
                "APP_PORT": "8000",
            },
            secrets=common_secrets,
        ).add_port_mappings(ecs.PortMapping(container_port=8000, protocol=ecs.Protocol.TCP))

        self.api_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "ApiService",
            cluster=self.cluster,
            task_definition=api_task,
            desired_count=1,
            public_load_balancer=True,
            listener_port=80,
            assign_public_ip=False,
            task_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
        )

        self.api_service.target_group.configure_health_check(
            path="/health",
            healthy_http_codes="200",
            interval=Duration.seconds(30),
            timeout=Duration.seconds(5),
        )

        worker_task = ecs.FargateTaskDefinition(
            self,
            "WorkerTaskDef",
            cpu=512,
            memory_limit_mib=1024,
            execution_role=self.task_execution_role,
            task_role=self.task_role,
        )

        worker_task.add_container(
            "worker",
            image=ecs.ContainerImage.from_ecr_repository(self.repository, tag="worker-latest"),
            logging=ecs.LogDrivers.aws_logs(
                stream_prefix="worker",
                log_group=self.worker_log_group,
            ),
            environment=common_env,
            secrets=common_secrets,
        )

        self.worker_service = ecs.FargateService(
            self,
            "WorkerService",
            cluster=self.cluster,
            task_definition=worker_task,
            desired_count=1,
            assign_public_ip=False,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
        )

        CfnOutput(
            self,
            "LoadBalancerDns",
            value=self.api_service.load_balancer.load_balancer_dns_name,
            description="HTTP endpoint for the API (port 80).",
        )
