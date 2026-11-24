import asyncio

from app.discovery.config import discovery_settings

from app.discovery.registry import (
    get_adapter,
    list_adapters,
)

from app.discovery.schemas import DiscoverySummary


class DiscoveryOrchestrator:

    async def run(
        self,
        sources: list[str] | None = None,
        limit: int = 100,
    ) -> DiscoverySummary:

        selected_sources = (
            list_adapters()
            if sources is None
            else list(dict.fromkeys(sources))
        )

        limit = max(
            1,
            min(
                limit,
                discovery_settings
                .DISCOVERY_MAX_EVENTS_PER_SOURCE,
            ),
        )

        adapters = [
            get_adapter(identifier)
            for identifier in selected_sources
        ]

        semaphore = asyncio.Semaphore(
            discovery_settings
            .DISCOVERY_MAX_CONCURRENCY
        )

        async def execute(adapter):

            async with semaphore:
                return await adapter.run(limit)

        results = await asyncio.gather(
            *[
                execute(adapter)
                for adapter in adapters
            ]
        )

        successful = sum(
            result.success
            for result in results
        )

        return DiscoverySummary(
            total_sources=len(results),
            successful_sources=successful,
            failed_sources=len(results) - successful,
            total_candidates=sum(
                len(result.candidates)
                for result in results
            ),
            results=results,
        )