import os
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.adapters.http.routers.job_offer_router import router as job_offer_router, set_job_offer_service
from app.adapters.http.routers.application_router import router as application_router
from app.adapters.http.routers.auth_router import router as auth_router, set_auth_service
from app.adapters.persistence.mongodb_user_repository import MongoDBUserRepository
from app.adapters.persistence.mongodb_job_offer_repository import MongoDBJobOfferRepository
from app.adapters.security.bcrypt_password_hasher import BcryptPasswordHasher
from app.adapters.security.jwt_token_service import JWTTokenService
from app.application.services.authentication_service import AuthenticationService
from app.application.services.job_offer_service import JobOfferService

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

# Initialize repositories and services
mongodb_url = os.getenv("MONGODB_URL")
mongodb_database = os.getenv("MONGODB_DATABASE", "ai-recruitment-platform")

if not mongodb_url:
    logger.warning("MONGODB_URL not set. Auth and JobOffer endpoints will not work.")
    auth_service = None
    job_offer_service = None
else:
    try:
        # Initialize repositories
        user_repository = MongoDBUserRepository(mongodb_url, mongodb_database)
        job_offer_repository = MongoDBJobOfferRepository(mongodb_url, mongodb_database)
        
        # Initialize security services
        password_hasher = BcryptPasswordHasher(rounds=12)
        
        jwt_secret = os.getenv("JWT_SECRET", "your-secret-key-change-this")
        jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
        jwt_expiration = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))
        
        token_service = JWTTokenService(
            secret_key=jwt_secret,
            algorithm=jwt_algorithm,
            expiration_hours=jwt_expiration
        )
        
        # Initialize authentication service
        auth_service = AuthenticationService(
            user_repository=user_repository,
            password_hasher=password_hasher,
            token_service=token_service
        )
        
        # Initialize job offer service
        job_offer_service = JobOfferService(
            job_offer_repository=job_offer_repository,
            user_repository=user_repository
        )
        
        set_auth_service(auth_service)
        set_job_offer_service(job_offer_service)
        logger.info("Authentication and JobOffer services initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        auth_service = None
        job_offer_service = None

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