"""Tests for services/nas/client.py."""

import pytest

from services.nas.client import NASClient


class TestNASClient:
    """Tests for NASClient stub — verifies NotImplementedError on all methods."""

    @pytest.mark.asyncio
    async def test_initialize_raises(self):
        """initialize() must raise NotImplementedError until Phase 2."""
        with pytest.raises(NotImplementedError, match="initialize"):
            await NASClient().initialize()

    @pytest.mark.asyncio
    async def test_shutdown_raises(self):
        """shutdown() must raise NotImplementedError until Phase 2."""
        with pytest.raises(NotImplementedError, match="shutdown"):
            await NASClient().shutdown()

    @pytest.mark.asyncio
    async def test_health_check_raises(self):
        """health_check() must raise NotImplementedError until Phase 2."""
        with pytest.raises(NotImplementedError, match="health_check"):
            await NASClient().health_check()

    @pytest.mark.asyncio
    async def test_get_status_raises(self):
        """get_status() must raise NotImplementedError until Phase 2."""
        with pytest.raises(NotImplementedError, match="get_status"):
            await NASClient().get_status()
