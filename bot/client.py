"""Bot subclass, on_ready, and global error handler."""

import discord
from discord.ext import commands

from config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)


class PipBot(commands.Bot):
    """
    Subclass of discord.py Bot with pip-bot-specific configuration.

    Handles initialization with guild sync, command prefix, and intents.
    Implements on_ready hook to log bot startup status.
    """

    def __init__(self) -> None:
        """Initialize the bot with appropriate intents and settings."""
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            sync_commands_in_init=False,
        )

    async def on_ready(self) -> None:
        """Log bot startup status and sync commands to guild."""
        if not self.user:
            logger.warning("on_ready called but user not set yet")
            return

        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")

        # Sync commands to guild (fast, dev-friendly)
        settings = get_settings()
        try:
            guild = discord.Object(id=settings.discord_guild_id)
            synced = await self.tree.sync(guild=guild)
            logger.info(f"Synced {len(synced)} command(s) to guild")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}", exc_info=True)

    async def setup_hook(self) -> None:
        """Load cogs when bot is initialized."""
        logger.debug("Setting up bot cogs...")
        try:
            await self.load_extension("cogs.system")
            logger.info("Successfully loaded all cogs")
        except Exception as e:
            logger.error(f"Failed to load cogs: {e}", exc_info=True)
            raise

