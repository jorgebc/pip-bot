"""Transmission RPC and filesystem interaction for NAS operations."""

from typing import Any

from services.base import BaseService


class NASClient(BaseService):
    """
    Client for NAS operations (Phase 2).

    Placeholder implementation that satisfies the BaseService ABC.
    All methods raise NotImplementedError until Phase 2 is implemented.
    """

    async def initialize(self) -> None:
        """Initialize the NAS connection."""
        raise NotImplementedError("NASClient.initialize() is not yet implemented")

    async def shutdown(self) -> None:
        """Close the NAS connection."""
        raise NotImplementedError("NASClient.shutdown() is not yet implemented")

    async def health_check(self) -> bool:
        """Check if the NAS is reachable."""
        raise NotImplementedError("NASClient.health_check() is not yet implemented")

    async def get_status(self) -> dict[str, Any]:
        """Return NAS status and metrics."""
        raise NotImplementedError("NASClient.get_status() is not yet implemented")
