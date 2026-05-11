import logging


logging.basicConfig(
    level="INFO",
    format="%(levelname)s | %(message)s",
)
logger = logging.getLogger("agentcore-runtime")


def main() -> None:
    logger.info(
        "Deployment entrypoint placeholder. Configure AgentCore deployment when AWS permissions are stable."
    )


if __name__ == "__main__":
    main()
