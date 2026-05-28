from app.application.use_cases.create_job_offer import CreateJobOffer
from app.application.use_cases.list_job_offers import ListJobOffers
from app.application.use_cases.create_application import CreateApplication
from app.application.use_cases.list_applications_by_job_offer import (
    ListApplicationsByJobOffer,
)
from app.application.use_cases.upload_application_cv import UploadApplicationCV
from app.application.use_cases.process_application_cv import ProcessApplicationCV
from app.application.use_cases.analyze_application_cv import AnalyzeApplicationCV

from app.adapters.persistence.in_memory.in_memory_job_offer_repository import (
    InMemoryJobOfferRepository,
)
from app.adapters.persistence.in_memory.in_memory_job_application_repository import (
    InMemoryJobApplicationRepository,
)
import os

from pymongo import MongoClient

from app.adapters.storage.local_file_storage import LocalFileStorage
from app.adapters.storage.mongodb_gridfs_file_storage import MongoGridFSFileStorage
from app.adapters.cv_processing.pdf_cv_text_extractor import PDFCVTextExtractor
from app.adapters.ai.simple_cv_analyzer import SimpleCVAnalyzer
from app.adapters.agent.agentcore_cv_analyzer import AgentCoreCVAnalyzer

from app.shared.config import get_cv_analyzer_config, CVAnalyzerProvider


job_offer_repository = InMemoryJobOfferRepository()
application_repository = InMemoryJobApplicationRepository()
mongodb_url = os.getenv("MONGODB_URL")
mongodb_database = os.getenv("MONGODB_DATABASE", "ai-recruitment-platform")

if mongodb_url:
    try:
        mongo_client = MongoClient(mongodb_url)
        file_storage = MongoGridFSFileStorage(mongo_client[mongodb_database])
    except Exception:
        file_storage = LocalFileStorage()
else:
    file_storage = LocalFileStorage()
cv_text_extractor = PDFCVTextExtractor()


def _get_cv_analyzer():
    """Factory function to create the appropriate CV Analyzer based on configuration.
    
    Returns either SimpleCVAnalyzer (default, no dependencies) or 
    AgentCoreCVAnalyzer (AWS Bedrock AgentCore integration).
    """
    config = get_cv_analyzer_config()
    
    if config.is_agentcore_enabled():
        return AgentCoreCVAnalyzer(
            runtime_id=config.agentcore_runtime_id,
            runtime_arn=config.agentcore_runtime_arn,
            agent_id=config.agentcore_agent_id,
            region=config.aws_region,
            model_id=config.bedrock_model_id,
        )
    else:
        return SimpleCVAnalyzer()


# Create the analyzer instance once (can be replaced by tests)
cv_analyzer = _get_cv_analyzer()


def get_create_job_offer_use_case() -> CreateJobOffer:
    return CreateJobOffer(job_offer_repository)


def get_list_job_offers_use_case() -> ListJobOffers:
    return ListJobOffers(job_offer_repository)


def get_create_application_use_case() -> CreateApplication:
    return CreateApplication(application_repository)


def get_list_applications_use_case() -> ListApplicationsByJobOffer:
    return ListApplicationsByJobOffer(application_repository)


def get_upload_application_cv_use_case() -> UploadApplicationCV:
    return UploadApplicationCV(application_repository, file_storage)


def get_process_application_cv_use_case() -> ProcessApplicationCV:
    return ProcessApplicationCV(application_repository, cv_text_extractor)


def get_analyze_application_cv_use_case() -> AnalyzeApplicationCV:
    return AnalyzeApplicationCV(
        application_repository, job_offer_repository, cv_analyzer
    )