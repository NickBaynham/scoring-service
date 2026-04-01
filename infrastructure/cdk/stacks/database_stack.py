"""RDS Postgres (small default; tune for production)."""

from aws_cdk import Duration, RemovalPolicy, Stack
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_rds as rds
from constructs import Construct


class DatabaseStack(Stack):
    """Postgres instance in private subnets; credentials in Secrets Manager."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        vpc: ec2.IVpc,
        **kwargs: object,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        sg = ec2.SecurityGroup(
            self,
            "RdsSg",
            vpc=vpc,
            description="Scoring service Postgres",
            allow_all_outbound=True,
        )

        creds = rds.Credentials.from_generated_secret("scoring_admin")

        self.database = rds.DatabaseInstance(
            self,
            "ScoringPostgres",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16_4,
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.T4G, ec2.InstanceSize.MICRO),
            allocated_storage=20,
            max_allocated_storage=100,
            credentials=creds,
            database_name="scoring",
            removal_policy=RemovalPolicy.SNAPSHOT,
            backup_retention=Duration.days(7),
            security_groups=[sg],
            publicly_accessible=False,
        )
