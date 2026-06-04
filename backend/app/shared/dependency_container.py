import logging
import os
from dataclasses import dataclass
from typing import Any

from app.adapters.cv_processing.pdf_cv_text_extractor import PDFCVTextExtractor
from app.adapters.persistence.in_memory.in_memory_job_application_repository import (
    InMemoryJobApplicationRepository,
)
from app.adapters.persistence.in_memory.in_memory_job_offer_repository import (
    InMemoryJobOfferRepository,
)
from app.adapters.persistence.mongodb_job_application_repository import (
    MongoDBJobApplicationRepository,
)
from app.adapters.persistence.mongodb_job_offer_repository import (
    MongoDBJobOfferRepository,
)
from app.adapters.persistence.mongodb_user_repository import MongoDBUserRepository
from app.adapters.storage.local_file_storage import LocalFileStorage
from app.adapters.storage.mongodb_gridfs_file_storage import MongoGridFSFileStorage
from app.shared.config import get_chatbot_config, get_cv_analyzer_config

logger = logging.getLogger(__name__)


@dataclass
class DependencyContainer:
    job_offer_repository: Any
    application_repository: Any
    file_storage: Any
    cv_text_extractor: PDFCVTextExtractor
    cv_analyzer: Any
    chatbot_service: Any
    user_repository: Any = None
    auth_service: Any = None
    job_offer_service: Any = None


def _build_cv_analyzer() -> Any:
    config = get_cv_analyzer_config()

    if config.is_agentcore_enabled():
        from app.adapters.agent.agentcore_cv_analyzer import AgentCoreCVAnalyzer

        return AgentCoreCVAnalyzer(
            runtime_id=config.agentcore_runtime_id,
            runtime_arn=config.agentcore_runtime_arn,
            agent_id=config.agentcore_agent_id,
            region=config.aws_region,
            model_id=config.bedrock_model_id,
        )

    from app.adapters.ai.simple_cv_analyzer import SimpleCVAnalyzer

    return SimpleCVAnalyzer()


def _build_chatbot_service() -> Any:
    from app.adapters.chatbot.rule_based_chatbot_service import RuleBasedChatbotService

    config = get_chatbot_config()
    fallback_service = RuleBasedChatbotService()

    if config.is_agentcore_enabled():
        from app.adapters.chatbot.agentcore_chatbot_service import (
            AgentCoreChatbotService,
        )

        return AgentCoreChatbotService(
            runtime_arn=config.agentcore_runtime_arn,
            region=config.aws_region,
            timeout_seconds=config.timeout_seconds,
            fallback_service=fallback_service,
        )

    return fallback_service


def build_dependency_container() -> DependencyContainer:
    mongodb_url = os.getenv("MONGODB_URL")
    mongodb_database = os.getenv("MONGODB_DATABASE", "ai-recruitment-platform")

    job_offer_repository = InMemoryJobOfferRepository()
    application_repository = InMemoryJobApplicationRepository()
    file_storage = LocalFileStorage()
    user_repository = None
    auth_service = None
    job_offer_service = None
    chatbot_service = _build_chatbot_service()

    if mongodb_url:
        try:
            from app.adapters.security.bcrypt_password_hasher import BcryptPasswordHasher
            from app.adapters.security.jwt_token_service import JWTTokenService
            from app.application.services.authentication_service import (
                AuthenticationService,
            )
            from app.application.services.job_offer_service import JobOfferService

            user_repository = MongoDBUserRepository(mongodb_url, mongodb_database)
            mongo_db = user_repository.db
            job_offer_repository = MongoDBJobOfferRepository(
                mongodb_url,
                mongodb_database,
            )
            application_repository = MongoDBJobApplicationRepository(mongo_db)
            file_storage = MongoGridFSFileStorage(mongo_db)

            password_hasher = BcryptPasswordHasher(rounds=12)
            jwt_secret = os.getenv("JWT_SECRET", "your-secret-key-change-this")
            jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
            jwt_expiration = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

            token_service = JWTTokenService(
                secret_key=jwt_secret,
                algorithm=jwt_algorithm,
                expiration_hours=jwt_expiration,
            )

            auth_service = AuthenticationService(
                user_repository=user_repository,
                password_hasher=password_hasher,
                token_service=token_service,
            )

            job_offer_service = JobOfferService(
                job_offer_repository=job_offer_repository,
                user_repository=user_repository,
            )

            logger.info("Dependency container initialized with MongoDB + GridFS")
        except Exception as exc:
            logger.exception(
                "MongoDB detected but initialization failed during startup"
            )
            raise RuntimeError(
                "MONGODB_URL is configured but MongoDB initialization failed. "
                "Fix MongoDB connectivity/configuration and restart the backend."
            ) from exc
    else:
        logger.warning(
            "MONGODB_URL not set. Using in-memory repositories and local file storage"
        )

    return DependencyContainer(
        job_offer_repository=job_offer_repository,
        application_repository=application_repository,
        file_storage=file_storage,
        cv_text_extractor=PDFCVTextExtractor(),
        cv_analyzer=_build_cv_analyzer(),
        chatbot_service=chatbot_service,
        user_repository=user_repository,
        auth_service=auth_service,
        job_offer_service=job_offer_service,
    )


_container: DependencyContainer | None = None


def get_container() -> DependencyContainer:
    global _container
    if _container is None:
        _container = build_dependency_container()
    return _container


def reset_container() -> None:
    global _container
    _container = None
