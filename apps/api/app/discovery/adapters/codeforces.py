import json

from datetime import datetime, timezone

from app.discovery.adapters.base import (
    BaseDiscoveryAdapter,
)

from app.discovery.http_client import (
    DiscoveryHTTPClient,
)

from app.discovery.schemas import RawEventCandidate


class CodeforcesAdapter(BaseDiscoveryAdapter):

    source_identifier = "codeforces"

    source_name = "Codeforces"

    base_url = "https://codeforces.com"

    allowed_hosts = {
        "codeforces.com",
    }

    API_URL = (
        "https://codeforces.com/api/contest.list"
        "?gym=false"
    )

    async def discover(
        self,
        client: DiscoveryHTTPClient,
        limit: int,
    ) -> list[RawEventCandidate]:

        response = await client.get(self.API_URL)

        return self.parse_response(
            response,
            limit,
        )

    def parse_response(
        self,
        response: str,
        limit: int,
    ) -> list[RawEventCandidate]:

        payload = json.loads(response)

        if payload.get("status") != "OK":
            raise ValueError(
                "Codeforces returned an unsuccessful response."
            )

        candidates = []

        for contest in payload.get("result", []):

            if contest.get("phase") != "BEFORE":
                continue

            contest_id = contest.get("id")
            title = contest.get("name")

            if not contest_id or not title:
                continue

            raw_data = {
                "contest_id": contest_id,
                "name": title,
                "phase": contest.get("phase"),
                "type": contest.get("type"),
                "duration_seconds": contest.get(
                    "durationSeconds"
                ),
            }

            timestamp = contest.get(
                "startTimeSeconds"
            )

            if timestamp is not None:

                raw_data["starts_at"] = (
                    datetime.fromtimestamp(
                        timestamp,
                        tz=timezone.utc,
                    ).isoformat()
                )

            candidates.append(
                RawEventCandidate(
                    source_identifier=self.source_identifier,
                    external_id=str(contest_id),
                    title=title,
                    source_url=(
                        f"https://codeforces.com/"
                        f"contest/{contest_id}"
                    ),
                    raw_data=raw_data,
                )
            )

        candidates.sort(
            key=lambda item: (
                item.raw_data.get("starts_at") is None,
                item.raw_data.get("starts_at") or "",
            )
        )

        return candidates[:limit]