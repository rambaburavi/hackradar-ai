from fastapi import APIRouter

from app.api.v1.endpoints import (
    discovery,
    events,
    sources,
    stats,
)


api_router = APIRouter()

api_router.include_router(events.router)
api_router.include_router(sources.router)
api_router.include_router(discovery.router)
api_router.include_router(stats.router)