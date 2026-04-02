"""System commands: /ping, /status, /help."""

import asyncio
import discord
from discord import app_commands
from discord.ext import commands

from services.system import get_cpu_temperature_async, get_system_status_async
from utils.logger import get_logger

logger = get_logger(__name__)


class SystemCog(commands.Cog):
    """System monitoring commands for Discord."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the SystemCog with bot instance."""
        self.bot = bot

    @app_commands.command(name="ping", description="Check bot latency and status")
    @app_commands.checks.cooldown(1, 60)
    async def ping(self, interaction: discord.Interaction) -> None:
        """
        Respond with 'Pong!' and current bot latency.

        Args:
            interaction: Discord interaction object.
        """
        try:
            async with asyncio.timeout(5):
                latency_ms = round(self.bot.latency * 1000)
                await interaction.response.send_message(
                    f"Pong! Latency: {latency_ms}ms",
                    ephemeral=True,
                )
                logger.debug(f"Responded to /ping command (latency: {latency_ms}ms)")
        except asyncio.TimeoutError:
            logger.error("Timeout sending /ping response")
            try:
                await interaction.response.send_message(
                    "❌ Request timed out",
                    ephemeral=True,
                )
            except Exception as e:
                logger.error(f"Failed to send timeout error: {e}")
        except Exception as e:
            logger.error(f"Error in /ping command: {e}", exc_info=True)
            try:
                await interaction.response.send_message(
                    f"❌ Error: {str(e)}",
                    ephemeral=True,
                )
            except Exception as followup_error:
                logger.error(f"Failed to send error response: {followup_error}")

    @app_commands.command(
        name="status", description="Get system health metrics (CPU, RAM, disk, uptime)"
    )
    @app_commands.checks.cooldown(1, 60)
    async def status(self, interaction: discord.Interaction) -> None:
        """
        Display system health metrics for the Raspberry Pi.

        Metrics include CPU usage, RAM usage, disk usage, and uptime.

        Args:
            interaction: Discord interaction object.
        """
        try:
            # Defer the response since metric collection may take a moment
            async with asyncio.timeout(15):
                await interaction.response.defer(ephemeral=True)

                # Collect system metrics asynchronously (non-blocking)
                status = await get_system_status_async()

                # Format response as an embed for better readability
                embed = discord.Embed(
                    title="System Status",
                    description="Current health metrics for the Raspberry Pi",
                    color=discord.Color.green(),
                )

                embed.add_field(
                    name="⏱️ Uptime",
                    value=status.uptime,
                    inline=False,
                )

                embed.add_field(
                    name="💻 CPU",
                    value=f"{status.cpu_percent:.1f}%",
                    inline=True,
                )

                embed.add_field(
                    name="🧠 RAM",
                    value=(
                        f"{status.ram_percent:.1f}% "
                        f"({status.ram_used_gb:.1f} / {status.ram_total_gb:.1f} GB)"
                    ),
                    inline=True,
                )

                embed.add_field(
                    name="💾 Disk",
                    value=(
                        f"{status.disk_percent:.1f}% "
                        f"({status.disk_used_gb:.1f} / {status.disk_total_gb:.1f} GB)"
                    ),
                    inline=True,
                )

                await interaction.followup.send(embed=embed, ephemeral=True)
                logger.debug("Responded to /status command")

        except asyncio.TimeoutError:
            logger.error("Timeout collecting system status")
            # Only try to respond if we haven't already deferred
            try:
                # Check if response was already deferred
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
                await interaction.followup.send(
                    "❌ Request timed out (took longer than 15 seconds)",
                    ephemeral=True,
                )
            except Exception as e:
                logger.error(f"Failed to send timeout error: {e}")

        except Exception as e:
            logger.error(f"Error in /status command: {e}", exc_info=True)
            try:
                # Try to defer if not already done
                if not interaction.response.is_done():
                    await interaction.response.defer(ephemeral=True)
                await interaction.followup.send(
                    f"❌ Error retrieving system status: {str(e)}",
                    ephemeral=True,
                )
            except Exception as followup_error:
                logger.error(
                    f"Failed to send error response: {followup_error}", exc_info=True
                )

    @app_commands.command(name="temp", description="Show current CPU temperature")
    @app_commands.checks.cooldown(1, 30)
    async def temp(self, interaction: discord.Interaction) -> None:
        """
        Display the current CPU temperature of the Raspberry Pi.

        Reads the temperature from the Linux thermal subsystem and shows it
        with a color-coded embed (green below 70°C, red at 70°C or above).

        Args:
            interaction: Discord interaction object.
        """
        try:
            async with asyncio.timeout(10):
                temp_c = await get_cpu_temperature_async()

                color = discord.Color.red() if temp_c >= 70.0 else discord.Color.green()
                status_label = "Hot" if temp_c >= 70.0 else "Normal"

                embed = discord.Embed(
                    title="CPU Temperature",
                    color=color,
                )
                embed.add_field(
                    name="🌡️ Temperature",
                    value=f"{temp_c:.1f}°C — {status_label}",
                    inline=False,
                )

                await interaction.response.send_message(embed=embed, ephemeral=True)
                logger.debug(f"Responded to /temp command ({temp_c:.1f}°C)")

        except FileNotFoundError:
            logger.error("Thermal zone file not found — not running on Linux/RPi?")
            try:
                await interaction.response.send_message(
                    "❌ CPU temperature is not available on this system.",
                    ephemeral=True,
                )
            except Exception as e:
                logger.error(f"Failed to send error response: {e}")

        except asyncio.TimeoutError:
            logger.error("Timeout reading CPU temperature")
            try:
                await interaction.response.send_message(
                    "❌ Request timed out",
                    ephemeral=True,
                )
            except Exception as e:
                logger.error(f"Failed to send timeout error: {e}")

        except Exception as e:
            logger.error(f"Error in /temp command: {e}", exc_info=True)
            try:
                await interaction.response.send_message(
                    f"❌ Error reading CPU temperature: {str(e)}",
                    ephemeral=True,
                )
            except Exception as followup_error:
                logger.error(f"Failed to send error response: {followup_error}")

    @app_commands.command(name="help", description="Show all available commands")
    @app_commands.checks.cooldown(1, 60)
    async def help(self, interaction: discord.Interaction) -> None:
        """
        Display a comprehensive list of all available bot commands.

        Shows all slash commands with their descriptions in a formatted embed.

        Args:
            interaction: Discord interaction object.
        """
        try:
            async with asyncio.timeout(10):
                # Create embed for command listing
                embed = discord.Embed(
                    title="📚 Bot Commands",
                    description="All available commands:",
                    color=discord.Color.blue(),
                )

                # Collect commands by iterating through all cogs
                cogs_with_commands = {}

                for cog_name, cog in self.bot.cogs.items():
                    cog_commands = cog.get_app_commands()
                    if cog_commands:
                        cogs_with_commands[cog_name] = cog_commands

                # Format commands by cog
                if cogs_with_commands:
                    for cog_name, cog_commands in cogs_with_commands.items():
                        command_lines = []
                        for cmd in cog_commands:
                            description = cmd.description or "No description available"
                            # Truncate long descriptions at 80 chars
                            if len(description) > 80:
                                description = description[:77] + "..."
                            command_lines.append(f"`/{cmd.name}` — {description}")

                        if command_lines:
                            embed.add_field(
                                name=cog_name,
                                value="\n".join(command_lines),
                                inline=False,
                            )
                else:
                    # Fallback: show basic built-in commands
                    embed.add_field(
                        name="System",
                        value=(
                            "`/ping` — Check bot latency and status\n"
                            "`/status` — Get system health metrics (CPU, RAM, disk, uptime)\n"
                            "`/help` — Show all available commands"
                        ),
                        inline=False,
                    )

                await interaction.response.send_message(embed=embed, ephemeral=True)
                logger.debug("Responded to /help command")

        except asyncio.TimeoutError:
            logger.error("Timeout in /help command")
            try:
                await interaction.response.send_message(
                    "❌ Request timed out",
                    ephemeral=True,
                )
            except Exception as e:
                logger.error(f"Failed to send timeout error: {e}")

        except Exception as e:
            logger.error(f"Error in /help command: {e}", exc_info=True)
            try:
                await interaction.response.send_message(
                    f"❌ Error retrieving help: {str(e)}",
                    ephemeral=True,
                )
            except Exception as followup_error:
                logger.error(
                    f"Failed to send error response: {followup_error}", exc_info=True
                )


async def setup(bot: commands.Bot) -> None:
    """Load the SystemCog into the bot.

    Args:
        bot: The Discord bot instance.
    """
    await bot.add_cog(SystemCog(bot))
    logger.debug("SystemCog loaded")

