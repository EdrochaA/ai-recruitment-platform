import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.http.routers.job_offer_router import router as job_offer_router
from app.adapters.http.routers.application_router import router as application_router

app = FastAPI()

allowed_origins = os.getenv(
    "FRONTEND_ORIGINS",
    "http://localhost:5173,http://localhost:5500,http://127.0.0.1:5500,http://localhost:8000",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in allowed_origins if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"] ,
    allow_headers=["*"],
)

app.include_router(job_offer_router)
app.include_router(application_router)


@app.get("/")
def health_check():
    return {"message": "Backend funcionando correctamente"}