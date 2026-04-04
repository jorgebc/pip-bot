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
        with patch(
            "cogs.system.get_system_status_async", new_callable=AsyncMock, return_value=mock_status
        ):
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
        with patch(
            "cogs.system.get_system_status_async",
            new_callable=AsyncMock,
            side_effect=OSError("Permission denied"),
        ):
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
        with patch(
            "cogs.system.get_system_status_async", new_callable=AsyncMock, return_value=mock_status
        ):
            # Should not raise, just log the error
            await cog.status.callback(cog, interaction)

        interaction.response.defer.assert_called_once()
        # followup.send is called at least once
        assert interaction.followup.send.call_count >= 1


class TestSystemCogHelp:
    """Test the /help command via the callback method."""

    @pytest.mark.asyncio
    async def test_help_command_success(self):
        """Test help callback returns commands in embed."""
        bot = MagicMock(spec=discord.ext.commands.Bot)
        bot.cogs = {}

        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response.send_message = AsyncMock()

        cog = SystemCog(bot)
        await cog.help.callback(cog, interaction)

        # Verify response was sent
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        embed = call_args.kwargs.get("embed")

        assert isinstance(embed, discord.Embed)
        assert embed.title == "📚 Bot Commands"
        assert call_args.kwargs["ephemeral"] is True

    @pytest.mark.asyncio
    async def test_help_command_with_cogs(self):
        """Test help command displays commands from cogs."""
        bot = MagicMock(spec=discord.ext.commands.Bot)

        # Create mock cog with commands
        mock_cmd1 = MagicMock()
        mock_cmd1.name = "ping"
        mock_cmd1.description = "Check bot latency"

        mock_cmd2 = MagicMock()
        mock_cmd2.name = "status"
        mock_cmd2.description = "Get system health metrics"

        mock_cog = MagicMock()
        mock_cog.get_app_commands.return_value = [mock_cmd1, mock_cmd2]

        bot.cogs = {"System": mock_cog}

        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response.send_message = AsyncMock()

        cog = SystemCog(bot)
        await cog.help.callback(cog, interaction)

        # Verify response was sent
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        embed = call_args.kwargs.get("embed")

        assert isinstance(embed, discord.Embed)
        # Verify command names appear in embed
        embed_dict = embed.to_dict()
        embed_str = str(embed_dict)
        assert "ping" in embed_str
        assert "status" in embed_str

    @pytest.mark.asyncio
    async def test_help_command_fallback(self):
        """Test help command fallback when no cogs found."""
        bot = MagicMock(spec=discord.ext.commands.Bot)
        bot.cogs = {}

        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response.send_message = AsyncMock()

        cog = SystemCog(bot)
        await cog.help.callback(cog, interaction)

        # Verify response was sent with fallback content
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        embed = call_args.kwargs.get("embed")

        assert isinstance(embed, discord.Embed)
        embed_dict = embed.to_dict()
        # Fallback should include basic commands
        assert any("ping" in str(field.get("value", "")).lower()
                   for field in embed_dict.get("fields", []))

    @pytest.mark.asyncio
    async def test_help_command_error_handling(self):
        """Test help command error handling."""
        bot = MagicMock(spec=discord.ext.commands.Bot)
        bot.cogs = {"BadCog": MagicMock(get_app_commands=MagicMock(
            side_effect=RuntimeError("Cog error")
        ))}

        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response.send_message = AsyncMock()

        cog = SystemCog(bot)
        await cog.help.callback(cog, interaction)

        # Verify response was sent (either help or error message)
        assert interaction.response.send_message.call_count >= 1

    @pytest.mark.asyncio
    async def test_help_command_long_description_truncation(self):
        """Test that long command descriptions are truncated."""
        bot = MagicMock(spec=discord.ext.commands.Bot)

        # Create mock command with very long description
        mock_cmd = MagicMock()
        mock_cmd.name = "test"
        mock_cmd.description = (
            "This is a very long description that should be truncated "
            "because it exceeds the maximum length of eighty characters"
        )

        mock_cog = MagicMock()
        mock_cog.get_app_commands.return_value = [mock_cmd]

        bot.cogs = {"Test": mock_cog}

        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response.send_message = AsyncMock()

        cog = SystemCog(bot)
        await cog.help.callback(cog, interaction)

        # Verify response was sent
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args
        embed = call_args.kwargs.get("embed")

        # Verify truncation occurred
        embed_dict = embed.to_dict()
        field_value = embed_dict["fields"][0]["value"]
        assert "..." in field_value  # Should have ellipsis from truncation


class TestSystemCogLogs:
    """Test the /logs command via the callback method."""

    # Patch the dict that the callback actually resolves globals from.
    # discord.py's load_extension can replace sys.modules["cogs.system"] with a fresh
    # module object, so patch("cogs.system…") may target a different namespace than the
    # one the callback uses.  Patching the callback's own __globals__ dict is robust
    # regardless of extension-loading order.
    _LOGS_GLOBALS = SystemCog.logs.callback.__globals__

    @pytest.mark.asyncio
    async def test_logs_short_output(self):
        """Test /logs sends output unchanged when it fits in one Discord message."""
        bot = MagicMock(spec=discord.ext.commands.Bot)
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        short_output = "Apr 04 10:00:00 pip-bot[1]: started\n"
        cog = SystemCog(bot)
        mock_fn = AsyncMock(return_value=short_output)
        with patch.dict(self._LOGS_GLOBALS, {"get_journal_logs_async": mock_fn}):
            await cog.logs.callback(cog, interaction, lines=5)

        interaction.followup.send.assert_called_once()
        sent_msg = interaction.followup.send.call_args[0][0]
        assert short_output.strip() in sent_msg
        assert "truncated" not in sent_msg
        assert len(sent_msg) <= 2000

    @pytest.mark.asyncio
    async def test_logs_long_output_truncated_within_limit(self):
        """Test /logs truncates long output and the final message is ≤2000 chars."""
        bot = MagicMock(spec=discord.ext.commands.Bot)
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        long_output = "X" * 3000
        cog = SystemCog(bot)
        mock_fn = AsyncMock(return_value=long_output)
        with patch.dict(self._LOGS_GLOBALS, {"get_journal_logs_async": mock_fn}):
            await cog.logs.callback(cog, interaction, lines=20)

        interaction.followup.send.assert_called_once()
        sent_msg = interaction.followup.send.call_args[0][0]
        assert len(sent_msg) <= 2000
        assert "truncated" in sent_msg

    @pytest.mark.asyncio
    async def test_logs_empty_output(self):
        """Test /logs handles empty journal output."""
        bot = MagicMock(spec=discord.ext.commands.Bot)
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        cog = SystemCog(bot)
        mock_fn = AsyncMock(return_value="")
        with patch.dict(self._LOGS_GLOBALS, {"get_journal_logs_async": mock_fn}):
            await cog.logs.callback(cog, interaction, lines=5)

        interaction.followup.send.assert_called_once()
        sent_msg = interaction.followup.send.call_args[0][0]
        assert "No log output" in sent_msg

    @pytest.mark.asyncio
    async def test_logs_journalctl_not_found(self):
        """Test /logs handles missing journalctl gracefully."""
        bot = MagicMock(spec=discord.ext.commands.Bot)
        interaction = AsyncMock(spec=discord.Interaction)
        interaction.response.defer = AsyncMock()
        interaction.followup.send = AsyncMock()

        cog = SystemCog(bot)
        mock_fn = AsyncMock(side_effect=FileNotFoundError)
        with patch.dict(self._LOGS_GLOBALS, {"get_journal_logs_async": mock_fn}):
            await cog.logs.callback(cog, interaction, lines=5)

        interaction.followup.send.assert_called_once()
        sent_msg = interaction.followup.send.call_args[0][0]
        assert "journalctl" in sent_msg


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
