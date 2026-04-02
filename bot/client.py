"""Bot subclass, on_ready, on_error, and global error handler."""

import datetime

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
        self._disconnect_at: datetime.datetime | None = None

    async def on_ready(self) -> None:
        """Log bot startup status, sync commands to guild, and notify startup channel."""
        if not self.user:
            logger.warning("on_ready called but user not set yet")
            return

        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info(f"Connected to {len(self.guilds)} guild(s)")

        settings = get_settings()
        guild = discord.Object(id=settings.discord_guild_id)

        # Copy global app commands to the guild so guild sync picks them up
        try:
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            logger.info(f"Synced {len(synced)} command(s) to guild {settings.discord_guild_id}")
            for cmd in synced:
                logger.debug(f"  Registered command: /{cmd.name}")
        except discord.Forbidden as e:
            logger.error(
                f"Missing permissions to sync commands (check bot scope 'applications.commands'): {e}"
            )
        except discord.HTTPException as e:
            logger.error(f"HTTP error while syncing commands: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}", exc_info=True)

        # Send startup notification to the configured channel
        if settings.startup_channel_id:
            try:
                channel = self.get_channel(settings.startup_channel_id)
                if channel and isinstance(channel, discord.TextChannel):
                    await channel.send(
                        f"Bot online — {self.user} | {len(synced)} command(s) synced"
                    )
                else:
                    logger.warning(
                        f"Startup channel {settings.startup_channel_id} not found or not a text channel"
                    )
            except discord.Forbidden:
                logger.error(
                    f"Missing send permission in startup channel {settings.startup_channel_id}"
                )
            except Exception as e:
                logger.error(f"Failed to send startup notification: {e}", exc_info=True)

    async def setup_hook(self) -> None:
        """Load cogs when bot is initialized."""
        logger.debug("Setting up bot cogs...")
        try:
            await self.load_extension("cogs.system")
            logger.info("Successfully loaded all cogs")
        except Exception as e:
            logger.error(f"Failed to load cogs: {e}", exc_info=True)
            raise

    async def on_error(self, event: str, *args, **kwargs) -> None:
        """Global error handler for all events."""
        logger.error(f"Error in event '{event}':", exc_info=True)

    async def on_disconnect(self) -> None:
        """Log when bot disconnects from Discord."""
        self._disconnect_at = datetime.datetime.now(datetime.UTC)
        logger.warning(f"Bot disconnected from Discord at {self._disconnect_at.isoformat()}")

    async def on_resumed(self) -> None:
        """Log when bot resumes connection after disconnect."""
        now = datetime.datetime.now(datetime.UTC)
        if self._disconnect_at:
            downtime = now - self._disconnect_at
            logger.info(f"Bot resumed connection to Discord (disconnected for {downtime.total_seconds():.1f}s)")
            self._disconnect_at = None
        else:
            logger.info("Bot resumed connection to Discord")

