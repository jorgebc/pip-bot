"""Shared validation functions for configuration and logging."""


class ConfigError(Exception):
    """Raised when configuration is invalid or incomplete."""

    pass


# Valid log levels as constant
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


def validate_log_level(level: str) -> str:
    """
    Validate and normalize a log level string.

    Args:
        level: The log level string to validate (case-insensitive).

    Returns:
        The validated log level in uppercase.

    Raises:
        ConfigError: If the level is not valid.
    """
    normalized = level.upper() if level else "INFO"

    if normalized not in VALID_LOG_LEVELS:
        raise ConfigError(
            f"LOG_LEVEL must be one of {VALID_LOG_LEVELS}, got: {normalized}"
        )

    return normalized

