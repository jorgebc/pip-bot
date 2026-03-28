"""Reads .env and exposes a typed Settings object."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

from utils.validators import ConfigError, validate_log_level


@dataclass
class Settings:
    """Typed configuration loaded from .env file."""

    # Phase 1 - Required
    discord_token: str
    discord_guild_id: int

    # Phase 1 - Optional
    log_level: str = "INFO"

    # Phase 2+ - Optional (NAS integration)
    nas_host: str | None = None
    nas_port: int | None = None
    nas_user: str | None = None
    nas_password: str | None = None


_settings: Settings | None = None


def get_settings() -> Settings:
    """
    Load and cache settings from .env file.

    This function is called once and caches the result. Subsequent calls
    return the cached Settings object.

    Returns:
        Settings object with validated configuration.

    Raises:
        ConfigError: If required variables are missing or invalid.
    """
    global _settings

    if _settings is not None:
        return _settings

    # Load .env file
    env_path = Path(".env")
    if env_path.exists():
        load_dotenv(env_path)
    else:
        load_dotenv()

    # Validate and extract Phase 1 required variables
    discord_token = os.getenv("DISCORD_TOKEN")
    if not discord_token or discord_token.strip() == "":
        raise ConfigError("DISCORD_TOKEN is required but not set in .env")

    discord_guild_id_str = os.getenv("DISCORD_GUILD_ID")
    if not discord_guild_id_str or discord_guild_id_str.strip() == "":
        raise ConfigError("DISCORD_GUILD_ID is required but not set in .env")

    try:
        discord_guild_id = int(discord_guild_id_str)
    except ValueError:
        raise ConfigError(
            f"DISCORD_GUILD_ID must be an integer, got: {discord_guild_id_str}"
        )

    # Optional Phase 1 variables - validate log level
    log_level_str = os.getenv("LOG_LEVEL", "INFO")
    log_level = validate_log_level(log_level_str)

    # Optional Phase 2+ variables
    nas_host = os.getenv("NAS_HOST")
    nas_port_str = os.getenv("NAS_PORT")
    nas_port = None
    if nas_port_str:
        try:
            nas_port = int(nas_port_str)
        except ValueError:
            raise ConfigError(f"NAS_PORT must be an integer, got: {nas_port_str}")

    nas_user = os.getenv("NAS_USER")
    nas_password = os.getenv("NAS_PASSWORD")

    # Validate NAS configuration: if one is set, all must be set
    nas_values = [nas_host, nas_port, nas_user, nas_password]
    nas_values_set = sum(1 for v in nas_values if v is not None)
    
    if nas_values_set > 0 and nas_values_set < 4:
        raise ConfigError(
            "NAS configuration is incomplete: all of NAS_HOST, NAS_PORT, "
            "NAS_USER, and NAS_PASSWORD must be set, or none of them should be set"
        )

    _settings = Settings(
        discord_token=discord_token,
        discord_guild_id=discord_guild_id,
        log_level=log_level,
        nas_host=nas_host,
        nas_port=nas_port,
        nas_user=nas_user,
        nas_password=nas_password,
    )

    return _settings


def reset_settings() -> None:
    """Reset cached settings. Useful for testing."""
    global _settings
    _settings = None

