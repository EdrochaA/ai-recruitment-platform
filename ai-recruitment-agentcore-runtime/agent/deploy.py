import logging
import os
import sys
import traceback
from pathlib import Path

from bedrock_agentcore_starter_toolkit import Runtime


logging.basicConfig(
    format="%(levelname)s | %(message)s",
)
logger = logging.getLogger("agentcore-runtime")
logger.setLevel(logging.INFO)


def _remove_agentcore_config(project_root: Path) -> None:
    config_path = project_root / ".bedrock_agentcore.yaml"
    if config_path.exists():
        config_path.unlink()
        logger.info("Removed existing .bedrock_agentcore.yaml to avoid conflicts")


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    os.chdir(project_root)
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    _remove_agentcore_config(project_root)

    agent_name = os.getenv("AGENTCORE_RUNTIME_NAME", "ai_recruitment_cv_analyzer_runtime")
    entrypoint = os.getenv("AGENTCORE_ENTRYPOINT", "agent/main.py")
    region = os.getenv("AWS_REGION", "eu-west-1")
    requirements_file = os.getenv("AGENTCORE_REQUIREMENTS_FILE")
    if not requirements_file:
        candidate = project_root / "requirements.txt"
        requirements_file = str(candidate) if candidate.exists() else None
    auto_create_execution_role = os.getenv("AGENTCORE_AUTO_CREATE_EXECUTION_ROLE", "true").lower() == "true"
    auto_create_ecr = os.getenv("AGENTCORE_AUTO_CREATE_ECR", "true").lower() == "true"
    memory_mode = os.getenv("AGENTCORE_MEMORY_MODE", "NO_MEMORY")

    logger.info(
        "Deploy config: name=%s, entrypoint=%s, region=%s, requirements=%s",
        agent_name,
        entrypoint,
        region,
        requirements_file,
    )

    try:
        runtime = Runtime()
        configure_kwargs = {
            "agent_name": agent_name,
            "entrypoint": entrypoint,
            "region": region,
            "auto_create_execution_role": auto_create_execution_role,
            "auto_create_ecr": auto_create_ecr,
            "memory_mode": memory_mode,
        }
        if requirements_file:
            configure_kwargs["requirements_file"] = requirements_file

        runtime.configure(**configure_kwargs)

        runtime_arn = runtime.launch()
        logger.info("Runtime launched. ARN=%s", runtime_arn)
        print(runtime_arn)
    except Exception as exc:
        logger.error("Runtime deployment failed: %s", exc)
        logger.error(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
