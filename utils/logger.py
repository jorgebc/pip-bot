"""Centralized logger factory and logging configuration."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger with console and file handlers.
    
    Logger is configured with:
    - Console handler for development
    - RotatingFileHandler for production (5MB max, 3 backups)
    - Formatter: [timestamp] [level] [module_name] message
    
    Args:
        name: Logger name, typically __name__ from the calling module.
    
    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    
    # Only configure if not already configured (avoid duplicate handlers)
    if logger.handlers:
        return logger
    
    # Determine log level from environment (will be set by config module)
    log_level = getattr(logging, _get_log_level_from_env(), "INFO")
    logger.setLevel(log_level)
    
    # Common formatter
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)-8s] [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    
    # Console handler (stdout) - always active
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation (logs/pip-bot.log)
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    file_handler = RotatingFileHandler(
        filename=log_dir / "pip-bot.log",
        maxBytes=5 * 1024 * 1024,  # 5 MB
        backupCount=3,  # Keep 3 backup files (.log.1, .log.2, .log.3)
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


def _get_log_level_from_env() -> str:
    """
    Read LOG_LEVEL from environment. Used to configure loggers.
    
    Falls back to INFO if not set or invalid.
    """
    import os
    
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
    
    if level not in valid_levels:
        return "INFO"
    
    return level
