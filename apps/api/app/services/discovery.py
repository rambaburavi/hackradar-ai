from datetime import datetime, timezone
from time import perf_counter

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.enums import (
    DiscoveryRunStatus,
    SourceHealth,
)

from app.discovery.registry import get_adapter
from app.discovery.config import discovery_settings
from app.discovery.schemas import DiscoveryResult

from app.models import (
    DiscoverySource,
    DiscoveryRun,
)

from app.services.ingestion import IngestionService


class DiscoveryService:

    def __init__(self, db: Session):

        self.db = db

    def get_enabled_source(
        self,
        identifier: str,
    ) -> DiscoverySource:

        source = self.db.scalar(
            select(DiscoverySource).where(
                DiscoverySource.source_identifier
                == identifier.strip().lower()
            )
        )

        if source is None:
            raise ValueError(
                "Source is not registered."
            )

        if not source.enabled:
            raise ValueError(
                "Source is disabled."
            )

        return source

    def process_result(
        self,
        source: DiscoverySource,
        result: DiscoveryResult,
        run: DiscoveryRun,
    ) -> None:

        run.request_count = result.request_count
        run.retry_count = result.retry_count

        run.discovered_count = len(
            result.candidates
        )

        now = datetime.now(timezone.utc)

        if not result.success:

            run.status = DiscoveryRunStatus.FAILED

            run.error_code = result.error_code
            run.error_summary = result.error_message

            source.health = SourceHealth.UNAVAILABLE

            source.last_failure_at = now

            source.consecutive_failures += 1

            source.last_error_summary = (
                result.error_message
            )

            return

        ingestion = IngestionService(self.db)

        for candidate in result.candidates:

            try:

                with self.db.begin_nested():

                    if (
                        candidate.source_identifier
                        != source.source_identifier
                    ):
                        raise ValueError(
                            "Candidate source mismatch."
                        )

                    outcome = ingestion.ingest(
                    candidate,
                    discovery_run_id=run.id,
                        )

                    action = outcome["action"]

                run.extracted_count += 1

                if action == "inserted":
                    run.inserted_count += 1

                elif action == "duplicate":
                    run.duplicate_count += 1

                elif action == "changed":
                    run.skipped_count += 1

                else:
                    run.skipped_count += 1

            except Exception:

                run.failed_count += 1

        if run.failed_count:

            run.status = (
                DiscoveryRunStatus.PARTIAL
                if run.extracted_count
                else DiscoveryRunStatus.FAILED
            )

            source.health = SourceHealth.DEGRADED

            source.last_failure_at = now

            source.consecutive_failures += 1

            run.error_summary = (
                "One or more candidates failed ingestion."
            )

            source.last_error_summary = (
                run.error_summary
            )

        else:

            run.status = DiscoveryRunStatus.COMPLETED

            source.health = SourceHealth.HEALTHY

            source.last_success_at = now

            source.consecutive_failures = 0

            source.last_error_summary = None

    async def run_source(
        self,
        identifier: str,
        limit: int = 20,
    ) -> dict:

        limit = max(
            1,
            min(
                limit,
                discovery_settings
                .DISCOVERY_MAX_EVENTS_PER_SOURCE,
            ),
        )

        adapter = get_adapter(identifier)

        source = self.get_enabled_source(
            adapter.source_identifier
        )

        started = datetime.now(timezone.utc)

        timer = perf_counter()

        run = DiscoveryRun(
            source_id=source.id,
            trigger_type="manual",
            dry_run=False,
            requested_limit=limit,
            status=DiscoveryRunStatus.RUNNING,
            started_at=started,
        )

        source.last_attempt_at = started

        self.db.add(run)

        self.db.commit()

        run_id = run.id
        source_id = source.id

        try:

            result = await adapter.run(limit)

            source = self.db.scalar(
                select(DiscoverySource)
                .where(
                    DiscoverySource.id == source_id
                )
                .with_for_update()
            )

            run = self.db.get(
                DiscoveryRun,
                run_id,
            )

            if source is None or run is None:
                raise RuntimeError(
                    "Discovery records unavailable."
                )

            if not source.enabled:
                raise ValueError(
                    "Source disabled during discovery."
                )

            self.process_result(
                source,
                result,
                run,
            )

            run.completed_at = datetime.now(
                timezone.utc
            )

            run.duration_ms = int(
                (perf_counter() - timer) * 1000
            )

            self.db.commit()

            return self.serialize_run(run)

        except Exception as error:

            self.db.rollback()

            run = self.db.get(
                DiscoveryRun,
                run_id,
            )

            if run is None:
                raise

            run.status = DiscoveryRunStatus.FAILED

            run.completed_at = datetime.now(
                timezone.utc
            )

            run.duration_ms = int(
                (perf_counter() - timer) * 1000
            )

            run.error_code = type(error).__name__

            run.error_summary = (
                "Discovery execution failed."
            )

            self.db.commit()

            return self.serialize_run(run)

    @staticmethod
    def serialize_run(run: DiscoveryRun) -> dict:

        return {
            "run_id": str(run.id),
            "source_id": str(run.source_id),
            "status": run.status.value,
            "discovered_count": run.discovered_count,
            "extracted_count": run.extracted_count,
            "inserted_count": run.inserted_count,
            "updated_count": run.updated_count,
            "duplicate_count": run.duplicate_count,
            "skipped_count": run.skipped_count,
            "failed_count": run.failed_count,
            "request_count": run.request_count,
            "retry_count": run.retry_count,
            "duration_ms": run.duration_ms,
            "error_code": run.error_code,
            "error_summary": run.error_summary,
        }