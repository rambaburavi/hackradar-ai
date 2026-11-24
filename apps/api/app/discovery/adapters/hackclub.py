from urllib.parse import urlsplit

from app.discovery.adapters.base import BaseDiscoveryAdapter
from app.discovery.parsers.rss import parse_rss
from app.discovery.schemas import RawEventCandidate


class HackClubAdapter(BaseDiscoveryAdapter):

    identifier = "hackclub"
    name = "Hack Club"

    base_url = "https://hackclub.com"

    allowed_hosts = {
        "hackclub.com",
    }

    FEED_URL = (
        "https://hackclub.com/api/v1/events/rss"
    )

    @staticmethod
    def parse(
        content: str | bytes,
        limit: int = 100,
    ) -> list[RawEventCandidate]:

        candidates = []

        for item in parse_rss(content, limit=limit):

            hostname = urlsplit(
                item["link"]
            ).hostname

            if not hostname:
                continue

            if not (
                hostname == "hackclub.com"
                or hostname.endswith(".hackclub.com")
            ):
                continue

            external_id = item["guid"]

            if external_id and len(external_id) > 255:
                external_id = None

            candidates.append(
                RawEventCandidate(
                    source_identifier="hackclub",
                    external_id=external_id,
                    title=item["title"],
                    source_url=item["link"],
                    description=item["description"],
                    raw_data={
                        "published_at": item["published_at"],
                        "categories": item["categories"],
                        "feed_url": HackClubAdapter.FEED_URL,
                        "extraction_method": "rss",
                    },
                )
            )

        return candidates

    async def discover(
        self,
        client,
        limit: int = 100,
    ) -> list[RawEventCandidate]:

        content = await client.get_text(
            self.FEED_URL
        )

        return self.parse(
            content,
            limit=limit,
        )