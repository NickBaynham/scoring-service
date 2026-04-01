"""SQS job notification queue (workers long-poll; API sends on enqueue)."""

from aws_cdk import Duration, Stack
from aws_cdk import aws_sqs as sqs
from constructs import Construct


class SqsStack(Stack):
    """FIFO not required; visibility timeout covers long LLM runs."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.queue = sqs.Queue(
            self,
            "ScoringJobQueue",
            visibility_timeout=Duration.minutes(15),
            retention_period=Duration.days(14),
        )
