from fastapi import APIRouter

from app.api.dependencies import DatabaseSession
from app.schemas.stats import DashboardStats
from app.services.stats import StatsService


router = APIRouter(
    prefix="/stats",
    tags=["Dashboard"],
)


@router.get(
    "",
    response_model=DashboardStats,
)
def get_dashboard_stats(
    db: DatabaseSession,
):
    return StatsService(db).get_stats()