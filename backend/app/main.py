from fastapi import FastAPI

from app.infrastructure.http.routers.job_offer_router import router as job_offer_router
from app.infrastructure.http.routers.application_router import router as application_router

app = FastAPI()

app.include_router(job_offer_router)
app.include_router(application_router)


@app.get("/")
def health_check():
    return {"message": "Backend funcionando correctamente"}