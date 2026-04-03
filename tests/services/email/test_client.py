"""Tests for services/email/client.py."""

import pytest

from services.email.client import EmailClient


class TestEmailClient:
    """Tests for EmailClient stub — verifies NotImplementedError on all methods."""

    @pytest.mark.asyncio
    async def test_initialize_raises(self):
        """initialize() must raise NotImplementedError until Phase 3."""
        with pytest.raises(NotImplementedError, match="initialize"):
            await EmailClient().initialize()

    @pytest.mark.asyncio
    async def test_shutdown_raises(self):
        """shutdown() must raise NotImplementedError until Phase 3."""
        with pytest.raises(NotImplementedError, match="shutdown"):
            await EmailClient().shutdown()

    @pytest.mark.asyncio
    async def test_health_check_raises(self):
        """health_check() must raise NotImplementedError until Phase 3."""
        with pytest.raises(NotImplementedError, match="health_check"):
            await EmailClient().health_check()

    @pytest.mark.asyncio
    async def test_get_status_raises(self):
        """get_status() must raise NotImplementedError until Phase 3."""
        with pytest.raises(NotImplementedError, match="get_status"):
            await EmailClient().get_status()
