"""Base service class defining interface for all pip-bot services."""

from abc import ABC, abstractmethod
from typing import Any


class BaseService(ABC):
    """
    Abstract base class for all pip-bot services.

    Defines common interface and lifecycle for services (Phase 1+).
    Implementations should inherit from this and implement all abstract methods.
    """

    @abstractmethod
    async def initialize(self) -> None:
        """
        Initialize the service (connect, authenticate, setup state).

        Called once when bot starts. Should raise exception if initialization fails.
        """
        pass

    @abstractmethod
    async def shutdown(self) -> None:
        """
        Clean up service resources (close connections, save state).

        Called when bot shuts down. Should be idempotent (safe to call twice).
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if service is healthy and operational.

        Returns:
            True if service is healthy, False otherwise.
        """
        pass

    @abstractmethod
    async def get_status(self) -> dict[str, Any]:
        """
        Get current service status and metrics.

        Returns:
            Dictionary with service status, metrics, and any relevant information.
        """
        pass
