"""Email composition and sending utilities (smtp)."""

from typing import Any

from services.base import BaseService


class EmailClient(BaseService):
    """
    Client for sending email via SMTP (Phase 3).

    Placeholder implementation that satisfies the BaseService ABC.
    All methods raise NotImplementedError until Phase 3 is implemented.
    """

    async def initialize(self) -> None:
        """Initialize the SMTP connection."""
        raise NotImplementedError("EmailClient.initialize() is not yet implemented")

    async def shutdown(self) -> None:
        """Close the SMTP connection."""
        raise NotImplementedError("EmailClient.shutdown() is not yet implemented")

    async def health_check(self) -> bool:
        """Check if the SMTP server is reachable."""
        raise NotImplementedError("EmailClient.health_check() is not yet implemented")

    async def get_status(self) -> dict[str, Any]:
        """Return email client status and metrics."""
        raise NotImplementedError("EmailClient.get_status() is not yet implemented")
