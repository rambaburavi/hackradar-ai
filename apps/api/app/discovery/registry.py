from app.discovery.adapters.base import (
    BaseDiscoveryAdapter,
)

from app.discovery.adapters.codeforces import (
    CodeforcesAdapter,
)

from app.discovery.adapters.atcoder import (
    AtCoderAdapter,
)


ADAPTER_REGISTRY = {
    "codeforces": CodeforcesAdapter,
    "atcoder": AtCoderAdapter,
}


def get_adapter(
    identifier: str,
) -> BaseDiscoveryAdapter:

    identifier = identifier.strip().lower()

    adapter_class = ADAPTER_REGISTRY.get(
        identifier
    )

    if adapter_class is None:
        raise ValueError(
            f"Unsupported source: {identifier}"
        )

    return adapter_class()


def list_adapters() -> list[str]:

    return sorted(
        ADAPTER_REGISTRY.keys()
    )