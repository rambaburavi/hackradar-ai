from datetime import datetime

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_events: int
    upcoming_events: int
    registration_open_events: int
    verified_events: int
    partially_verified_events: int
    deadlines_next_7_days: int
    free_events: int
    total_sources: int
    active_sources: int
    healthy_sources: int
    total_discovery_runs: int
    last_discovery_at: datetime | None