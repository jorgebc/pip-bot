"""Tests for cogs/system.py module."""

from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from cogs.system import SystemCog
from services.system import SystemStatus


class TestSystemCogPing:
    """Test the /ping command via the callback method."""

    @pytest.mark.asyncio
    async def test_ping_command_callback(self):
        """Test ping callback responds with latency."""
        # Create mock bot
        bot = MagicMock(spec=discord.ext.commands.Bot)
        bot.latency = 0.05  # 50ms latency

        # Create mock interaction with proper response mocking
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response.send_message = AsyncMock()

        # Create cog and call the callback directly
        cog = SystemCog(bot)
        await cog.ping.callback(cog, interaction)

        # Verify response was sent
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        assert "Pong!" in call_args[0][0]
        assert "50ms" in call_args[0][0]
        assert call_args[1]["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_ping_command_high_latency(self):
        """Test ping command with high latency."""
        bot = MagicMock(spec=discord.ext.commands.Bot)
        bot.latency = 0.5  # 500ms latency

        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response.send_message = AsyncMock()

        cog = SystemCog(bot)
        await cog.ping.callback(cog, interaction)

        call_args = interaction.response.send_message.call_args
        assert "500ms" in call_args[0][0]

    @pytest.mark.asyncio
    async def test_ping_command_zero_latency(self):
        """Test ping command with minimal latency."""
        bot = MagicMock(spec=discord.ext.commands.Bot)
        bot.latency = 0.001  # 1ms latency

        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response.send_message = AsyncMock()

        cog = SystemCog(bot)
        await cog.ping.callback(cog, interaction)

        call_args = interaction.response.send_message.call_args
        assert "1ms" in call_args[0][0]


class TestSystemCogStatus:
    """Test the /status command via the callback method."""

    @pytest.mark.asyncio
    async def test_status_command_success_structure(self):
        """Test status callback returns system metrics in embed with correct structure."""
        bot = MagicMock(spec=discord.ext.commands.Bot)
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        mock_status = SystemStatus(
            uptime="5d 3h 42m",
            cpu_percent=35.5,
            ram_percent=60.0,
            ram_used_gb=2.0,
            ram_total_gb=4.0,
            disk_percent=45.0,
            disk_used_gb=450.0,
            disk_total_gb=1000.0,
        )

        cog = SystemCog(bot)
        with patch("cogs.system.get_system_status", return_value=mock_status):
            await cog.status.callback(cog, interaction)

        # Verify deferred response
        interaction.response.defer.assert_called_once_with(ephemeral=True)

        # Verify embed was sent
        interaction.followup.send.assert_called_once()
        call_args = interaction.followup.send.call_args
        embed = call_args.kwargs["embed"]

        assert isinstance(embed, discord.Embed)
        assert embed.title == "System Status"
        assert call_args.kwargs["ephemeral"] is True

        # Verify embed contains expected fields
        embed_dict = embed.to_dict()
        field_names = [field["name"] for field in embed_dict["fields"]]
        assert "⏱️ Uptime" in field_names
        assert "💻 CPU" in field_names
        assert "🧠 RAM" in field_names
        assert "💾 Disk" in field_names

    @pytest.mark.asyncio
    async def test_status_command_error_handling(self):
        """Test status callback error handling when system status fails."""
        bot = MagicMock(spec=discord.ext.commands.Bot)
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        cog = SystemCog(bot)
        with patch("cogs.system.get_system_status", side_effect=OSError("Permission denied")):
            await cog.status.callback(cog, interaction)

        # Verify deferred response
        interaction.response.defer.assert_called_once_with(ephemeral=True)

        # Verify error message was sent (at least once)
        assert interaction.followup.send.call_count >= 1

    @pytest.mark.asyncio
    async def test_status_command_error_on_followup(self):
        """Test status callback handles error when sending followup fails."""
        mock_status = SystemStatus(
            uptime="5d 3h 42m",
            cpu_percent=35.5,
            ram_percent=60.0,
            ram_used_gb=2.0,
            ram_total_gb=4.0,
            disk_percent=45.0,
            disk_used_gb=450.0,
            disk_total_gb=1000.0,
        )

        bot = MagicMock(spec=discord.ext.commands.Bot)
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock(side_effect=discord.DiscordException("Send failed"))

        cog = SystemCog(bot)
        with patch("cogs.system.get_system_status", return_value=mock_status):
            # Should not raise, just log the error
            await cog.status.callback(cog, interaction)

        interaction.response.defer.assert_called_once()
        # followup.send is called at least once
        assert interaction.followup.send.call_count >= 1


class TestSystemCogInitialization:
    """Test SystemCog initialization."""

    def test_system_cog_initialization(self):
        """Test that SystemCog initializes with bot instance."""
        bot = MagicMock(spec=discord.ext.commands.Bot)
        cog = SystemCog(bot)

        assert cog.bot is bot
        assert isinstance(cog, discord.ext.commands.Cog)


class TestSystemCogSetup:
    """Test the setup function for cog loading."""

    @pytest.mark.asyncio
    async def test_setup_function_loads_cog(self):
        """Test that setup function loads the SystemCog."""
        bot = AsyncMock(spec=discord.ext.commands.Bot)

        from cogs.system import setup

        await setup(bot)

        # Verify add_cog was called at least once
        assert bot.add_cog.call_count >= 1
