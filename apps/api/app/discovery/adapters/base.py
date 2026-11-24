from abc import ABC, abstractmethod
from time import perf_counter

from app.discovery.http_client import (
    DiscoveryHTTPClient,
)

from app.discovery.schemas import (
    DiscoveryResult,
    RawEventCandidate,
)


class BaseDiscoveryAdapter(ABC):

    source_identifier: str

    source_name: str

    base_url: str

    allowed_hosts: set[str]

    @abstractmethod
    async def discover(
        self,
        client: DiscoveryHTTPClient,
        limit: int,
    ) -> list[RawEventCandidate]:

        raise NotImplementedError

    async def run(
        self,
        limit: int = 100,
    ) -> DiscoveryResult:

        started = perf_counter()

        async with DiscoveryHTTPClient(
            self.allowed_hosts
        ) as client:

            try:

                candidates = await self.discover(
                    client,
                    limit,
                )

                return DiscoveryResult(
                    source_identifier=self.source_identifier,
                    success=True,
                    candidates=candidates[:limit],
                    request_count=client.request_count,
                    retry_count=client.retry_count,
                    duration_ms=int(
                        (perf_counter() - started) * 1000
                    ),
                )

            except Exception as error:

                return DiscoveryResult(
                    source_identifier=self.source_identifier,
                    success=False,
                    request_count=client.request_count,
                    retry_count=client.retry_count,
                    duration_ms=int(
                        (perf_counter() - started) * 1000
                    ),
                    error_code=type(error).__name__,
                    error_message="Source discovery failed.",
                )