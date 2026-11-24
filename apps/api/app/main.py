import logging

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.session import engine


logger = logging.getLogger(__name__)


app = FastAPI(
    title="HackRadar AI",
    description="Intelligent event discovery and recommendation platform",
    version="0.1.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["System"])
async def health():
    return {"status": "ok"}


@app.get("/ready", tags=["System"])
def readiness():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1")).scalar_one()

        return {
            "status": "ready",
            "database": "connected",
        }

    except SQLAlchemyError:
        logger.warning("Database readiness check failed")

        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "database": "unavailable",
            },
        ) from None
from app.api.v1.router import api_router

app.include_router(api_router, prefix="/api/v1")