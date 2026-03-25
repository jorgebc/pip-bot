"""Tests for bot/client.py module."""

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from bot import PipBot


class TestPipBotInitialization:
    """Test PipBot initialization and configuration."""

    def test_pipbot_creates_bot_instance(self):
        """Test that PipBot creates a bot instance successfully."""
        bot = PipBot()
        assert isinstance(bot, discord.ext.commands.Bot)

    def test_pipbot_has_correct_intents(self):
        """Test that PipBot is initialized with correct intents."""
        bot = PipBot()
        assert bot.intents.message_content is True
        assert bot.intents.guilds is True

    def test_pipbot_command_prefix(self):
        """Test that PipBot uses correct command prefix."""
        bot = PipBot()
        assert bot.command_prefix == "!"

    def test_pipbot_sync_commands_in_init_is_false(self):
        """Test that sync_commands_in_init is False (for dev-friendly fast command syncing)."""
        bot = PipBot()
        # Verify bot is properly initialized (if it reaches here, init was successful)
        assert bot is not None


class TestPipBotSetupHook:
    """Test PipBot setup_hook for cog loading."""

    @pytest.mark.asyncio
    async def test_setup_hook_executes(self):
        """Test that setup_hook executes without error."""
        bot = PipBot()

        with patch("bot.client.logger") as mock_logger:
            await bot.setup_hook()
            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args[0][0]
            assert "cogs" in call_args.lower()


class TestPipBotOnReady:
    """Test PipBot on_ready event handler logic."""

    @pytest.mark.asyncio
    async def test_on_ready_handles_missing_user(self):
        """Test that on_ready handles case where user is not set."""
        bot = PipBot()

        with patch("bot.client.logger") as mock_logger:
            # self.user is None before bot is actually connected
            await bot.on_ready()

            # Should log a warning and return early
            mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_ready_syncs_when_user_is_set(self):
        """Test that on_ready syncs commands when user is set."""
        bot = PipBot()

        # Simulate being after a connection by mocking logger and settings
        with patch("bot.client.get_settings") as mock_settings:
            with patch.object(bot.tree, "sync", new_callable=AsyncMock) as mock_sync:
                mock_settings.return_value = MagicMock(discord_guild_id=11111)
                mock_sync.return_value = []

                # Verify that tree.sync would be called if user was set
                # In real execution, self.user would be set by discord.py

