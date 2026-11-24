import asyncio
import ipaddress
import socket

import httpx

from app.discovery.config import discovery_settings
from app.discovery.urls import (
    UnsafeURL,
    validate_source_url,
)

from urllib.parse import urlsplit


class DiscoveryHTTPError(RuntimeError):
    pass


class DiscoveryHTTPClient:

    def __init__(
        self,
        allowed_hosts: set[str],
    ):

        self.allowed_hosts = allowed_hosts

        self.request_count = 0
        self.retry_count = 0

        self.client = httpx.AsyncClient(
            timeout=discovery_settings.DISCOVERY_TIMEOUT_SECONDS,
            follow_redirects=False,
            trust_env=False,
            headers={
                "User-Agent": (
                    discovery_settings.DISCOVERY_USER_AGENT
                ),
                "Accept": (
                    "application/json, text/html, "
                    "application/xml, text/xml"
                ),
            },
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    async def validate_dns(self, url: str):

        hostname = urlsplit(url).hostname

        addresses = await asyncio.get_running_loop().getaddrinfo(
            hostname,
            443,
            type=socket.SOCK_STREAM,
        )

        if not addresses:
            raise UnsafeURL("Hostname could not be resolved.")

        for address in addresses:

            ip = ipaddress.ip_address(
                address[4][0]
            )

            if not ip.is_global:
                raise UnsafeURL(
                    "Non-public network address rejected."
                )

    async def get(self, url: str) -> str:

        validate_source_url(
            url,
            self.allowed_hosts,
        )

        max_retries = (
            discovery_settings.DISCOVERY_MAX_RETRIES
        )

        for attempt in range(max_retries + 1):

            try:
                await asyncio.wait_for(
                    self.validate_dns(url),
                    timeout=5,
                )

                self.request_count += 1

                async with self.client.stream(
                    "GET",
                    url,
                ) as response:

                    if 300 <= response.status_code < 400:
                        raise DiscoveryHTTPError(
                            "Redirect requires explicit approval."
                        )

                    if response.status_code in {
                        429, 500, 502, 503, 504
                    }:

                        if attempt < max_retries:

                            self.retry_count += 1

                            retry_after = response.headers.get(
                                "Retry-After"
                            )

                            if retry_after is not None:
                                if not retry_after.isdigit():
                                    raise DiscoveryHTTPError(
                                        "Server requested delayed retry."
                                    )

                                delay = int(retry_after)

                                if delay > 30:
                                    raise DiscoveryHTTPError(
                                        "Server requested delayed retry."
                                    )
                            else:
                                delay = 2 ** attempt

                            await asyncio.sleep(delay)
                            continue

                    response.raise_for_status()

                    chunks = []
                    size = 0

                    async for chunk in response.aiter_bytes():

                        size += len(chunk)

                        if size > (
                            discovery_settings
                            .DISCOVERY_MAX_RESPONSE_BYTES
                        ):
                            raise DiscoveryHTTPError(
                                "Response exceeds size limit."
                            )

                        chunks.append(chunk)

                    return b"".join(chunks).decode(
                        response.encoding or "utf-8",
                        errors="replace",
                    )

            except (
                httpx.TimeoutException,
                httpx.NetworkError,
            ):

                if attempt >= max_retries:
                    raise DiscoveryHTTPError(
                        "Network request failed."
                    ) from None

                self.retry_count += 1

                await asyncio.sleep(2 ** attempt)

        raise DiscoveryHTTPError(
            "Request attempts exhausted."
        )