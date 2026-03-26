"""System commands: /ping, /status."""

import discord
from discord import app_commands
from discord.ext import commands

from services.system import get_system_status
from utils.logger import get_logger

logger = get_logger(__name__)


class SystemCog(commands.Cog):
    """System monitoring commands for Discord."""

    def __init__(self, bot: commands.Bot) -> None:
        """Initialize the SystemCog with bot instance."""
        self.bot = bot

    @app_commands.command(name="ping", description="Check bot latency and status")
    async def ping(self, interaction: discord.Interaction) -> None:
        """
        Respond with 'Pong!' and current bot latency.

        Args:
            interaction: Discord interaction object.
        """
        latency_ms = round(self.bot.latency * 1000)
        await interaction.response.send_message(
            f"Pong! Latency: {latency_ms}ms",
            ephemeral=True,
        )
        logger.debug(f"Responded to /ping command (latency: {latency_ms}ms)")

    @app_commands.command(
        name="status", description="Get system health metrics (CPU, RAM, disk, uptime)"
    )
    async def status(self, interaction: discord.Interaction) -> None:
        """
        Display system health metrics for the Raspberry Pi.

        Metrics include CPU usage, RAM usage, disk usage, and uptime.

        Args:
            interaction: Discord interaction object.
        """
        try:
            # Defer the response since metric collection may take a moment
            await interaction.response.defer(ephemeral=True)

            # Collect system metrics
            status = get_system_status()

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

        except Exception as e:
            logger.error(f"Error in /status command: {e}", exc_info=True)
            try:
                await interaction.followup.send(
                    f"❌ Error retrieving system status: {str(e)}",
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

