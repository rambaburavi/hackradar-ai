import ipaddress

from urllib.parse import (
    parse_qsl,
    urlencode,
    urlsplit,
    urlunsplit,
)


TRACKING_PARAMETERS = {
    "fbclid",
    "gclid",
    "mc_cid",
    "mc_eid",
}


class UnsafeURL(ValueError):
    pass


def validate_source_url(
    url: str,
    allowed_hosts: set[str],
) -> str:

    parsed = urlsplit(url)

    if parsed.scheme != "https":
        raise UnsafeURL("Only HTTPS is allowed.")

    if parsed.username or parsed.password:
        raise UnsafeURL("Credentials in URLs are forbidden.")

    hostname = parsed.hostname

    if not hostname:
        raise UnsafeURL("Missing hostname.")

    hostname = hostname.lower()

    try:
        ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        raise UnsafeURL("IP address URLs are forbidden.")

    if hostname not in allowed_hosts:
        raise UnsafeURL("Hostname is not approved.")

    if parsed.port not in (None, 443):
        raise UnsafeURL("Non-standard ports are forbidden.")

    return url


def canonicalize_url(url: str) -> str:

    parsed = urlsplit(url)

    if parsed.scheme not in {"http", "https"}:
        raise UnsafeURL("Unsupported URL scheme.")

    if not parsed.hostname:
        raise UnsafeURL("Missing hostname.")

    if parsed.username or parsed.password:
        raise UnsafeURL("URL credentials are forbidden.")

    parameters = [
        (key, value)
        for key, value in parse_qsl(
            parsed.query,
            keep_blank_values=True,
        )
        if not key.lower().startswith("utm_")
        and key.lower() not in TRACKING_PARAMETERS
    ]

    result = urlunsplit((
        parsed.scheme.lower(),
        parsed.netloc.lower(),
        parsed.path or "/",
        urlencode(parameters),
        "",
    ))

    if len(result.encode("utf-8")) > 2000:
        raise UnsafeURL("Canonical URL is too long.")

    return result