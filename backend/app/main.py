import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.adapters.http.routers.job_offer_router import router as job_offer_router, set_job_offer_service
from app.adapters.http.routers.application_router import router as application_router
from app.adapters.http.routers.auth_router import router as auth_router, set_auth_service
from app.shared.dependency_container import get_container

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Recruitment Platform API",
    description="Backend for AI-powered recruitment platform",
    version="0.1.0"
)

# Setup CORS
allowed_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5173,http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize container and route-level services
container = get_container()
auth_service = container.auth_service
job_offer_service = container.job_offer_service

if auth_service and job_offer_service:
    set_auth_service(auth_service)
    set_job_offer_service(job_offer_service)
    logger.info("Authentication and JobOffer services initialized successfully")
else:
    logger.warning("Auth and JobOffer services not initialized (using fallback dependencies)")

# Include routers
app.include_router(auth_router)
app.include_router(job_offer_router)
app.include_router(application_router)


@app.get("/")
def health_check():
    """Health check endpoint"""
    auth_status = "connected" if auth_service else "not initialized"
    job_offers_status = "ready" if job_offer_service else "not initialized"
    return {
        "message": "Backend funcionando correctamente",
        "version": "0.1.0",
        "services": {
            "auth": auth_status,
            "job_offers": job_offers_status,
            "applications": "ready"
        }
    }