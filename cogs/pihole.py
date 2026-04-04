"""Pi-hole commands: /pihole status, /pihole enable, /pihole disable, /pihole top."""

import asyncio
import urllib.error

import discord
from discord import app_commands
from discord.ext import commands

from config import get_settings
from services.pihole.client import (
    disable_pihole_async,
    enable_pihole_async,
    get_pihole_status_async,
    get_pihole_top_async,
)
from utils.logger import get_logger

logger = get_logger(__name__)


class PiholeCog(commands.GroupCog, name="pihole"):
    """Pi-hole ad-blocker control commands."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize PiholeCog with bot instance."""
        self.bot = bot

    # ------------------------------------------------------------------
    # /pihole status
    # ------------------------------------------------------------------

    @app_commands.command(name="status", description="Show Pi-hole status and today's stats")
    @app_commands.checks.cooldown(1, 30)
    async def status(self, interaction: discord.Interaction) -> None:
        """
        Display current Pi-hole status and today's DNS query summary.

        Shows enabled/disabled state, total queries, blocked queries, and
        the size of the block list. No authentication required.

        Args:
            interaction: Discord interaction object.
        """
        settings = get_settings()
        try:
            async with asyncio.timeout(15):
                await interaction.response.defer(ephemeral=True)
                pihole_status = await get_pihole_status_async(
                    settings.pihole_host, settings.pihole_port, settings.pihole_password
                )

            enabled_label = "Enabled" if pihole_status.enabled else "Disabled"
            color = discord.Color.green() if pihole_status.enabled else discord.Color.red()

            embed = discord.Embed(
                title="Pi-hole Status",
                color=color,
            )
            embed.add_field(
                name="🛡️ Blocking",
                value=enabled_label,
                inline=False,
            )
            embed.add_field(
                name="📊 Queries today",
                value=f"{pihole_status.total_queries:,}",
                inline=True,
            )
            embed.add_field(
                name="🚫 Blocked today",
                value=(
                    f"{pihole_status.blocked_queries:,} "
                    f"({pihole_status.blocked_percent:.1f}%)"
                ),
                inline=True,
            )
            embed.add_field(
                name="📋 Block list",
                value=f"{pihole_status.domains_blocked:,} domains",
                inline=True,
            )

            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.debug("Responded to /pihole status command")

        except urllib.error.HTTPError as e:
            logger.error(f"Pi-hole HTTP error in /pihole status: {e.code} {e.reason}")
            if e.code == 401:
                await self._send_followup_error(
                    interaction, "Authentication failed — check `PIHOLE_PASSWORD` in `.env`."
                )
            else:
                await self._send_followup_error(interaction, f"Pi-hole API error (HTTP {e.code}).")
        except urllib.error.URLError as e:
            logger.error(f"Pi-hole unreachable in /pihole status: {e}")
            await self._send_followup_error(
                interaction, "Pi-hole is unreachable. Is it running on the RPi?"
            )
        except TimeoutError:
            logger.error("Timeout in /pihole status")
            await self._send_followup_error(interaction, "Request timed out.")
        except Exception as e:
            logger.error(f"Error in /pihole status: {e}", exc_info=True)
            await self._send_followup_error(interaction, f"Unexpected error: {e}")

    # ------------------------------------------------------------------
    # /pihole enable
    # ------------------------------------------------------------------

    @app_commands.command(name="enable", description="Enable Pi-hole ad blocking")
    @app_commands.checks.cooldown(1, 30)
    async def enable(self, interaction: discord.Interaction) -> None:
        """
        Re-enable Pi-hole ad blocking.

        Requires ``PIHOLE_PASSWORD`` to be set in ``.env``.

        Args:
            interaction: Discord interaction object.
        """
        settings = get_settings()
        if not settings.pihole_password:
            await interaction.response.send_message(
                "❌ `PIHOLE_PASSWORD` is not configured. Set it in `.env` to use this command.",
                ephemeral=True,
            )
            return

        try:
            async with asyncio.timeout(15):
                await interaction.response.defer(ephemeral=True)
                await enable_pihole_async(
                    settings.pihole_host, settings.pihole_port, settings.pihole_password
                )

            embed = discord.Embed(
                title="Pi-hole",
                description="✅ Ad blocking **enabled**.",
                color=discord.Color.green(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.debug("Responded to /pihole enable command")

        except urllib.error.HTTPError as e:
            logger.error(f"Pi-hole HTTP error in /pihole enable: {e.code} {e.reason}")
            if e.code == 401:
                await self._send_followup_error(
                    interaction, "Authentication failed — check `PIHOLE_PASSWORD` in `.env`."
                )
            else:
                await self._send_followup_error(interaction, f"Pi-hole API error (HTTP {e.code}).")
        except urllib.error.URLError as e:
            logger.error(f"Pi-hole unreachable in /pihole enable: {e}")
            await self._send_followup_error(
                interaction, "Pi-hole is unreachable. Is it running on the RPi?"
            )
        except ValueError as e:
            logger.error(f"Pi-hole enable returned unexpected response: {e}")
            await self._send_followup_error(
                interaction, f"Pi-hole returned an unexpected response: {e}"
            )
        except TimeoutError:
            logger.error("Timeout in /pihole enable")
            await self._send_followup_error(interaction, "Request timed out.")
        except Exception as e:
            logger.error(f"Error in /pihole enable: {e}", exc_info=True)
            await self._send_followup_error(interaction, f"Unexpected error: {e}")

    # ------------------------------------------------------------------
    # /pihole disable
    # ------------------------------------------------------------------

    @app_commands.command(
        name="disable",
        description="Disable Pi-hole ad blocking (optionally for N seconds)",
    )
    @app_commands.describe(seconds="Duration in seconds (0 or omit = indefinite)")
    @app_commands.checks.cooldown(1, 30)
    async def disable(self, interaction: discord.Interaction, seconds: int = 0) -> None:
        """
        Disable Pi-hole ad blocking, optionally for a limited duration.

        Requires ``PIHOLE_PASSWORD`` to be set in ``.env``.

        Args:
            interaction: Discord interaction object.
            seconds: How long to disable blocking. ``0`` means indefinitely.
        """
        settings = get_settings()
        if not settings.pihole_password:
            await interaction.response.send_message(
                "❌ `PIHOLE_PASSWORD` is not configured. Set it in `.env` to use this command.",
                ephemeral=True,
            )
            return

        if seconds < 0:
            await interaction.response.send_message(
                "❌ `seconds` must be 0 (indefinite) or a positive number.",
                ephemeral=True,
            )
            return

        try:
            async with asyncio.timeout(15):
                await interaction.response.defer(ephemeral=True)
                await disable_pihole_async(
                    settings.pihole_host,
                    settings.pihole_port,
                    settings.pihole_password,
                    seconds,
                )

            duration_label = f"for {seconds}s" if seconds > 0 else "indefinitely"
            embed = discord.Embed(
                title="Pi-hole",
                description=f"⛔ Ad blocking **disabled** {duration_label}.",
                color=discord.Color.red(),
            )
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.debug(f"Responded to /pihole disable command (seconds={seconds})")

        except urllib.error.HTTPError as e:
            logger.error(f"Pi-hole HTTP error in /pihole disable: {e.code} {e.reason}")
            if e.code == 401:
                await self._send_followup_error(
                    interaction, "Authentication failed — check `PIHOLE_PASSWORD` in `.env`."
                )
            else:
                await self._send_followup_error(interaction, f"Pi-hole API error (HTTP {e.code}).")
        except urllib.error.URLError as e:
            logger.error(f"Pi-hole unreachable in /pihole disable: {e}")
            await self._send_followup_error(
                interaction, "Pi-hole is unreachable. Is it running on the RPi?"
            )
        except ValueError as e:
            logger.error(f"Pi-hole disable returned unexpected response: {e}")
            await self._send_followup_error(
                interaction, f"Pi-hole returned an unexpected response: {e}"
            )
        except TimeoutError:
            logger.error("Timeout in /pihole disable")
            await self._send_followup_error(interaction, "Request timed out.")
        except Exception as e:
            logger.error(f"Error in /pihole disable: {e}", exc_info=True)
            await self._send_followup_error(interaction, f"Unexpected error: {e}")

    # ------------------------------------------------------------------
    # /pihole top
    # ------------------------------------------------------------------

    @app_commands.command(
        name="top",
        description="Show top 5 queried and top 5 blocked domains",
    )
    @app_commands.checks.cooldown(1, 30)
    async def top(self, interaction: discord.Interaction) -> None:
        """
        Display the top 5 queried domains and top 5 blocked domains.

        Requires ``PIHOLE_PASSWORD`` to be set in ``.env``.

        Args:
            interaction: Discord interaction object.
        """
        settings = get_settings()
        if not settings.pihole_password:
            await interaction.response.send_message(
                "❌ `PIHOLE_PASSWORD` is not configured. Set it in `.env` to use this command.",
                ephemeral=True,
            )
            return

        try:
            async with asyncio.timeout(15):
                await interaction.response.defer(ephemeral=True)
                top_data = await get_pihole_top_async(
                    settings.pihole_host,
                    settings.pihole_port,
                    settings.pihole_password,
                )

            embed = discord.Embed(
                title="Pi-hole Top Domains",
                color=discord.Color.blue(),
            )

            if top_data.top_queries:
                lines = [
                    f"`{domain}` — {count:,}"
                    for domain, count in top_data.top_queries.items()
                ]
                embed.add_field(
                    name="🔍 Top Queries",
                    value="\n".join(lines) or "No data",
                    inline=False,
                )
            else:
                embed.add_field(name="🔍 Top Queries", value="No data", inline=False)

            if top_data.top_ads:
                lines = [
                    f"`{domain}` — {count:,}"
                    for domain, count in top_data.top_ads.items()
                ]
                embed.add_field(
                    name="🚫 Top Blocked",
                    value="\n".join(lines) or "No data",
                    inline=False,
                )
            else:
                embed.add_field(name="🚫 Top Blocked", value="No data", inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.debug("Responded to /pihole top command")

        except urllib.error.HTTPError as e:
            logger.error(f"Pi-hole HTTP error in /pihole top: {e.code} {e.reason}")
            if e.code == 401:
                await self._send_followup_error(
                    interaction, "Authentication failed — check `PIHOLE_PASSWORD` in `.env`."
                )
            else:
                await self._send_followup_error(interaction, f"Pi-hole API error (HTTP {e.code}).")
        except urllib.error.URLError as e:
            logger.error(f"Pi-hole unreachable in /pihole top: {e}")
            await self._send_followup_error(
                interaction, "Pi-hole is unreachable. Is it running on the RPi?"
            )
        except ValueError as e:
            logger.error(f"Pi-hole top returned unexpected response: {e}")
            await self._send_followup_error(interaction, str(e))
        except TimeoutError:
            logger.error("Timeout in /pihole top")
            await self._send_followup_error(interaction, "Request timed out.")
        except Exception as e:
            logger.error(f"Error in /pihole top: {e}", exc_info=True)
            await self._send_followup_error(interaction, f"Unexpected error: {e}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    async def _send_followup_error(self, interaction: discord.Interaction, message: str) -> None:
        """
        Send an ephemeral error followup, swallowing any secondary Discord errors.

        Args:
            interaction: Discord interaction object.
            message: Error message to display.
        """
        try:
            if interaction.response.is_done():
                await interaction.followup.send(f"❌ {message}", ephemeral=True)
            else:
                await interaction.response.send_message(f"❌ {message}", ephemeral=True)
        except Exception as e:
            logger.error(f"Failed to send error response: {e}")


async def setup(bot: commands.Bot) -> None:
    """Load PiholeCog into the bot.

    Args:
        bot: The Discord bot instance.
    """
    await bot.add_cog(PiholeCog(bot))
    logger.debug("PiholeCog loaded")
