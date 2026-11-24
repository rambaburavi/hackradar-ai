from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.enums import (
    EventLifecycleStatus,
    SourceHealth,
    VerificationStatus,
)

from app.models import (
    DiscoveryRun,
    DiscoverySource,
    Event,
)

from app.schemas.stats import DashboardStats


class StatsService:

    def __init__(self, db: Session):
        self.db = db

    def count(self, model, *conditions) -> int:
        statement = (
            select(func.count())
            .select_from(model)
            .where(*conditions)
        )

        return self.db.scalar(statement) or 0

    def get_stats(self) -> DashboardStats:
        now = datetime.now(timezone.utc)

        active_conditions = (
            Event.lifecycle_status.notin_([
                EventLifecycleStatus.CANCELLED,
                EventLifecycleStatus.COMPLETED,
                EventLifecycleStatus.ONGOING,
            ])
        )

        deadline_conditions = (
            active_conditions,
            Event.lifecycle_status
            != EventLifecycleStatus.REGISTRATION_CLOSED,
            Event.registration_deadline >= now,
        )

        last_discovery = self.db.scalar(
            select(func.max(DiscoveryRun.completed_at))
            .where(DiscoveryRun.dry_run.is_(False))
        )

        return DashboardStats(
            total_events=self.count(Event),

            upcoming_events=self.count(
                Event,
                Event.starts_at >= now,
                active_conditions,
            ),

            registration_open_events=self.count(
                Event,
                Event.lifecycle_status
                == EventLifecycleStatus.REGISTRATION_OPEN,
                Event.registration_deadline >= now,
            ),

            verified_events=self.count(
                Event,
                Event.verification_status
                == VerificationStatus.VERIFIED,
            ),

            partially_verified_events=self.count(
                Event,
                Event.verification_status
                == VerificationStatus.PARTIALLY_VERIFIED,
            ),

            deadlines_next_7_days=self.count(
                Event,
                *deadline_conditions,
                Event.registration_deadline
                <= now + timedelta(days=7),
            ),

            free_events=self.count(
                Event,
                Event.registration_fee == 0,
            ),

            total_sources=self.count(
                DiscoverySource
            ),

            active_sources=self.count(
                DiscoverySource,
                DiscoverySource.enabled.is_(True),
            ),

            healthy_sources=self.count(
                DiscoverySource,
                DiscoverySource.enabled.is_(True),
                DiscoverySource.health
                == SourceHealth.HEALTHY,
            ),

            total_discovery_runs=self.count(
                DiscoveryRun
            ),

            last_discovery_at=last_discovery,
        )