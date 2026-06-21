from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routes import admin, questions

settings = get_settings()

app = FastAPI(
    title="ADITI API",
    description="JEE doubt-solving pilot backend — Phase 0",
    version="0.1.0",
)

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
