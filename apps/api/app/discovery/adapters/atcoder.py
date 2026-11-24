from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from app.discovery.adapters.base import BaseDiscoveryAdapter
from app.discovery.http_client import DiscoveryHTTPClient
from app.discovery.schemas import RawEventCandidate
from app.discovery.urls import canonicalize_url


class AtCoderAdapter(BaseDiscoveryAdapter):

    source_identifier = "atcoder"

    source_name = "AtCoder"

    base_url = "https://atcoder.jp"

    allowed_hosts = {
        "atcoder.jp",
    }

    CONTESTS_URL = "https://atcoder.jp/contests/"

    async def discover(
        self,
        client: DiscoveryHTTPClient,
        limit: int,
    ) -> list[RawEventCandidate]:

        response = await client.get(
            self.CONTESTS_URL
        )

        return self.parse_response(
            response,
            limit,
        )

    def parse_start_time(
        self,
        value: str,
    ) -> datetime | None:

        try:
            parsed = datetime.strptime(
                value.strip(),
                "%Y-%m-%d %H:%M:%S%z",
            )

            return parsed.astimezone(
                timezone.utc
            )

        except ValueError:
            return None

    def parse_duration(
        self,
        value: str,
    ) -> int | None:

        try:
            hours, minutes = map(
                int,
                value.strip().split(":"),
            )

            if hours < 0 or not 0 <= minutes < 60:
                return None

            return hours * 3600 + minutes * 60

        except ValueError:
            return None

    def parse_response(
        self,
        response: str,
        limit: int,
    ) -> list[RawEventCandidate]:

        soup = BeautifulSoup(
            response,
            "html.parser",
        )

        section = soup.select_one(
            "#contest-table-upcoming"
        )

        if section is None:
            raise ValueError(
                "Upcoming contest section not found."
            )

        candidates = []

        seen_ids = set()

        for row in section.select("tbody tr"):

            columns = row.find_all("td")

            if len(columns) < 3:
                continue

            link = columns[1].select_one(
                'a[href^="/contests/"]'
            )

            if link is None:
                continue

            title = link.get_text(
                " ",
                strip=True,
            )

            href = link.get("href")

            if not title or not href:
                continue

            source_url = canonicalize_url(
                urljoin(self.base_url, href)
            )

            parsed_url = urlsplit(source_url)

            if (
                parsed_url.scheme != "https"
                or parsed_url.hostname != "atcoder.jp"
            ):
                continue

            path_parts = (
                parsed_url.path.strip("/").split("/")
            )

            if (
                len(path_parts) != 2
                or path_parts[0] != "contests"
            ):
                continue

            external_id = path_parts[1]

            if external_id in seen_ids:
                continue

            seen_ids.add(external_id)

            start_text = columns[0].get_text(
                " ",
                strip=True,
            )

            duration_text = columns[2].get_text(
                " ",
                strip=True,
            )

            starts_at = self.parse_start_time(
                start_text
            )

            duration = self.parse_duration(
                duration_text
            )

            raw_data = {
                "contest_id": external_id,
                "name": title,
                "phase": "upcoming",
                "start_time_text": start_text,
                "duration_text": duration_text,
            }

            if starts_at is not None:
                raw_data["starts_at"] = (
                    starts_at.isoformat()
                )

            if duration is not None:
                raw_data["duration_seconds"] = (
                    duration
                )

            if len(columns) >= 4:
                raw_data["rated_range"] = (
                    columns[3].get_text(
                        " ",
                        strip=True,
                    )
                )

            candidates.append(
                RawEventCandidate(
                    source_identifier=(
                        self.source_identifier
                    ),
                    external_id=external_id,
                    title=title,
                    source_url=source_url,
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