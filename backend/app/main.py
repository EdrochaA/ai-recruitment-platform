from fastapi import FastAPI

from app.infrastructure.http.routers.job_offer_router import router as job_offer_router

app = FastAPI(
    title="TFG Recruitment Backend",
    version="0.1.0",
    description="Backend inicial para gestión de ofertas y candidaturas.",
)

app.include_router(job_offer_router)


@app.get("/")
def health_check():
    return {"message": "Backend funcionando correctamente"}