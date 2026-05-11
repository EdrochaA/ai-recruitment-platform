import logging
import os

import boto3
from botocore.exceptions import BotoCoreError, ClientError


logging.basicConfig(
    format="%(levelname)s | %(message)s",
)
logger = logging.getLogger("agentcore-runtime")
logger.setLevel(logging.INFO)


REGION = os.getenv("AWS_REGION", "eu-west-1")
RUNTIME_NAME = os.getenv("AGENTCORE_RUNTIME_NAME")
EXECUTION_ROLE_ARN = os.getenv("AGENTCORE_EXECUTION_ROLE_ARN")
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID")
CDK_STACK_NAME = os.getenv("AGENTCORE_CDK_STACK_NAME")


def _require(value: str | None, name: str) -> str:
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


def _check_identity() -> None:
    try:
        sts = boto3.client("sts", region_name=REGION)
        identity = sts.get_caller_identity()
        logger.info("AWS identity OK. account=%s", identity.get("Account"))
    except (ClientError, BotoCoreError) as exc:
        logger.error("AWS identity check failed: %s", exc)
        raise


def _check_cdk_stack() -> None:
    if not CDK_STACK_NAME:
        return

    try:
        cfn = boto3.client("cloudformation", region_name=REGION)
        resp = cfn.describe_stacks(StackName=CDK_STACK_NAME)
        stacks = resp.get("Stacks", [])
        if stacks:
            logger.info("CDK stack status: %s", stacks[0].get("StackStatus"))
    except (ClientError, BotoCoreError) as exc:
        logger.error("CloudFormation describe stack failed: %s", exc)
        raise


def main() -> None:
    logger.info("Starting AgentCore runtime deploy preflight")

    try:
        _require(REGION, "AWS_REGION")
        _require(RUNTIME_NAME, "AGENTCORE_RUNTIME_NAME")
        _require(EXECUTION_ROLE_ARN, "AGENTCORE_EXECUTION_ROLE_ARN")
        _require(BEDROCK_MODEL_ID, "BEDROCK_MODEL_ID")

        logger.info(
            "Config ok. region=%s, runtime_name=%s, execution_role_arn=%s, model_id=%s",
            REGION,
            RUNTIME_NAME,
            EXECUTION_ROLE_ARN,
            BEDROCK_MODEL_ID,
        )

        _check_identity()
        _check_cdk_stack()

        logger.info("Deploy preflight complete. Ready for manual AgentCore deployment.")
    except Exception as exc:
        logger.error("Deploy preflight failed: %s", exc)
        raise


if __name__ == "__main__":
    main()
