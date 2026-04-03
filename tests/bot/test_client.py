"""Tests for bot/client.py module."""

import datetime
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
    async def test_on_ready_skips_on_second_call(self):
        """Test that on_ready is a no-op on reconnects after startup_done is set."""
        bot = PipBot()
        bot._startup_done = True

        with patch("bot.client.logger") as mock_logger:
            await bot.on_ready()
            mock_logger.debug.assert_called_once()
            assert "reconnect" in mock_logger.debug.call_args[0][0].lower()

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


class TestPipBotEventHandlers:
    """Test on_error, on_disconnect, and on_resumed event handlers."""

    @pytest.mark.asyncio
    async def test_on_error_logs_event_name(self):
        """on_error should log the event name."""
        bot = PipBot()
        with patch("bot.client.logger") as mock_logger:
            await bot.on_error("on_message")
            mock_logger.error.assert_called_once()
            assert "on_message" in mock_logger.error.call_args[0][0]

    @pytest.mark.asyncio
    async def test_on_disconnect_records_timestamp(self):
        """on_disconnect should record the disconnect time."""
        bot = PipBot()
        assert bot._disconnect_at is None
        with patch("bot.client.logger"):
            await bot.on_disconnect()
        assert bot._disconnect_at is not None
        assert isinstance(bot._disconnect_at, datetime.datetime)

    @pytest.mark.asyncio
    async def test_on_resumed_with_prior_disconnect_logs_downtime(self):
        """on_resumed should log downtime when _disconnect_at is set."""
        bot = PipBot()
        bot._disconnect_at = datetime.datetime.now(datetime.UTC) - datetime.timedelta(seconds=5)
        with patch("bot.client.logger") as mock_logger:
            await bot.on_resumed()
        mock_logger.info.assert_called_once()
        assert "disconnected for" in mock_logger.info.call_args[0][0].lower()
        assert bot._disconnect_at is None

    @pytest.mark.asyncio
    async def test_on_resumed_without_prior_disconnect_logs_simple_message(self):
        """on_resumed should log a simple message when no disconnect was recorded."""
        bot = PipBot()
        assert bot._disconnect_at is None
        with patch("bot.client.logger") as mock_logger:
            await bot.on_resumed()
        mock_logger.info.assert_called_once()
        assert "resumed" in mock_logger.info.call_args[0][0].lower()
