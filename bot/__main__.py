"""Entry point for running the bot: python -m bot"""

import asyncio

import discord

from bot import PipBot
from config import get_settings
from utils.logger import get_logger

logger = get_logger(__name__)


async def main() -> None:
    """Initialize settings, create bot, and run it."""
    try:
        settings = get_settings()
    except Exception as e:
        logger.error(f"Failed to load settings: {e}", exc_info=True)
        raise

    logger.info("Starting pip-bot...")
    bot = PipBot()

    try:
        await bot.start(settings.discord_token)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except discord.LoginFailure:
        logger.error("Failed to login: Invalid token or authentication failed")
        raise
    except discord.HTTPException as e:
        logger.error(f"Discord API error during startup: {e}")
        raise
    except Exception as e:
        logger.error(f"Bot crashed: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
