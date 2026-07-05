from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import admin, questions

settings = get_settings()

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aditi.backend")

app = FastAPI(title="ADITI API", version="0.1.0")

@app.on_event("startup")
async def on_startup():
    logger.info("Starting ADITI backend")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Shutting down ADITI backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(questions.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "service": "aditi-backend"}
