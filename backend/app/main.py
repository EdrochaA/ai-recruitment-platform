import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.adapters.http.routers.job_offer_router import router as job_offer_router
from app.adapters.http.routers.application_router import router as application_router
from app.adapters.http.routers.auth_router import router as auth_router, set_auth_service
from app.adapters.persistence.mongodb_user_repository import MongoDBUserRepository
from app.application.services.authentication_service import AuthenticationService, JWTService

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

# Initialize MongoDB connection
mongodb_url = os.getenv("MONGODB_URL")
mongodb_database = os.getenv("MONGODB_DATABASE", "ai_recruitment")

if not mongodb_url:
    raise RuntimeError("MONGODB_URL environment variable is not set")

# Initialize repositories and services
user_repository = MongoDBUserRepository(mongodb_url, mongodb_database)

# Initialize JWT service
jwt_secret = os.getenv("JWT_SECRET", "your-secret-key-change-this")
jwt_algorithm = os.getenv("JWT_ALGORITHM", "HS256")
jwt_expiration = int(os.getenv("JWT_EXPIRATION_HOURS", "24"))

jwt_service = JWTService(
    secret_key=jwt_secret,
    algorithm=jwt_algorithm,
    expiration_hours=jwt_expiration
)

# Initialize authentication service
auth_service = AuthenticationService(user_repository, jwt_service)
set_auth_service(auth_service)

# Include routers
app.include_router(auth_router)
app.include_router(job_offer_router)
app.include_router(application_router)


@app.get("/")
def health_check():
    return {
        "message": "Backend funcionando correctamente",
        "version": "0.1.0",
        "services": ["auth", "job_offers", "applications"]
    }