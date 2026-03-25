"""Tests for utils/logger.py module."""

import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from utils.logger import get_logger


@pytest.fixture
def temp_logs_dir(tmp_path, monkeypatch):
    """Fixture that creates a temporary logs directory and changes cwd to it."""
    # Create logs directory in temp location
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()

    # Change working directory to temp directory
    monkeypatch.chdir(tmp_path)

    return logs_dir


@pytest.fixture(autouse=True)
def clear_logger_cache():
    """Clear logger cache before each test."""
    # Get root logger and remove all handlers
    logging.root.handlers.clear()
    # Clear all loggers
    for logger in logging.Logger.manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            logger.handlers.clear()
    yield


class TestGetLogger:
    """Test get_logger() function."""

    @patch.dict(os.environ, {"LOG_LEVEL": "INFO"}, clear=True)
    def test_get_logger_returns_logger(self, temp_logs_dir):
        """Test that get_logger returns a Logger instance."""
        logger = get_logger("test_module")
        assert isinstance(logger, logging.Logger)

    @patch.dict(os.environ, {"LOG_LEVEL": "INFO"}, clear=True)
    def test_get_logger_has_handlers(self, temp_logs_dir):
        """Test that logger has both console and file handlers."""
        logger = get_logger("test_module")
        assert len(logger.handlers) == 2
        handler_types = {type(h).__name__ for h in logger.handlers}
        assert "StreamHandler" in handler_types
        assert "RotatingFileHandler" in handler_types

    @patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}, clear=True)
    def test_get_logger_respects_log_level(self, temp_logs_dir):
        """Test that logger level is set from LOG_LEVEL env var."""
        logger = get_logger("test_module")
        assert logger.level == logging.DEBUG

    @patch.dict(os.environ, {"LOG_LEVEL": "WARNING"}, clear=True)
    def test_get_logger_different_levels(self, temp_logs_dir):
        """Test different LOG_LEVEL values."""
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        for level_name, level_value in levels.items():
            logging.root.handlers.clear()
            for logger in logging.Logger.manager.loggerDict.values():
                if isinstance(logger, logging.Logger):
                    logger.handlers.clear()

            with patch.dict(os.environ, {"LOG_LEVEL": level_name}, clear=True):
                logger = get_logger(f"test_module_{level_name}")
                assert logger.level == level_value

    @patch.dict(os.environ, {"LOG_LEVEL": "INFO"}, clear=True)
    def test_get_logger_creates_logs_directory(self, temp_logs_dir):
        """Test that get_logger creates logs directory if it doesn't exist."""
        logs_path = Path("logs")
        # Remove the directory that was created by fixture
        if logs_path.exists():
            import shutil

            shutil.rmtree(logs_path)

        get_logger("test_module")
        assert logs_path.exists()
        assert logs_path.is_dir()

    @patch.dict(os.environ, {"LOG_LEVEL": "INFO"}, clear=True)
    def test_get_logger_returns_cached_logger(self, temp_logs_dir):
        """Test that subsequent calls return the same logger instance."""
        logger1 = get_logger("test_module")
        logger2 = get_logger("test_module")

        assert logger1 is logger2
        # Should not have duplicate handlers
        assert len(logger1.handlers) == 2

    @patch.dict(os.environ, {"LOG_LEVEL": "INFO"}, clear=True)
    def test_get_logger_different_modules(self, temp_logs_dir):
        """Test that different module names create different loggers."""
        logger1 = get_logger("module_a")
        logger2 = get_logger("module_b")

        assert logger1 is not logger2
        assert logger1.name == "module_a"
        assert logger2.name == "module_b"

    @patch.dict(os.environ, {"LOG_LEVEL": "INFO"}, clear=True)
    def test_get_logger_formatter_structure(self, temp_logs_dir):
        """Test that formatter is correct."""
        logger = get_logger("test_module")

        for handler in logger.handlers:
            assert handler.formatter is not None
            # Check format contains expected parts
            fmt = handler.formatter._fmt
            assert "%(asctime)s" in fmt
            assert "levelname" in fmt
            assert "%(name)s" in fmt
            assert "%(message)s" in fmt

    @patch.dict(os.environ, {"LOG_LEVEL": "INFO"}, clear=True)
    def test_get_logger_rotating_file_handler_config(self, temp_logs_dir):
        """Test RotatingFileHandler configuration."""
        logger = get_logger("test_module")

        rotating_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.handlers.RotatingFileHandler):
                rotating_handler = handler
                break

        assert rotating_handler is not None
        assert rotating_handler.maxBytes == 5 * 1024 * 1024  # 5 MB
        assert rotating_handler.backupCount == 3

    @patch.dict(os.environ, {"LOG_LEVEL": "INFO"}, clear=True)
    def test_get_logger_logs_to_console(self, temp_logs_dir, capsys):
        """Test that logger outputs to console."""
        logger = get_logger("test_module")
        logger.info("test message")

        captured = capsys.readouterr()
        assert "test message" in captured.err  # logging goes to stderr by default

    @patch.dict(os.environ, {"LOG_LEVEL": "INFO"}, clear=True)
    def test_get_logger_logs_to_file(self, temp_logs_dir):
        """Test that logger outputs to file."""
        logger = get_logger("test_module")
        logger.info("test message")

        log_file = Path("logs") / "pip-bot.log"
        assert log_file.exists()

        content = log_file.read_text()
        assert "test message" in content

    @patch.dict(os.environ, {"LOG_LEVEL": "INVALID"}, clear=True)
    def test_get_logger_invalid_log_level_raises_error(self, temp_logs_dir):
        """Test that invalid LOG_LEVEL raises ConfigError."""
        from utils.validators import ConfigError
        
        with pytest.raises(ConfigError, match="LOG_LEVEL must be one of"):
            get_logger("test_module")

    @patch.dict(os.environ, {}, clear=True)
    def test_get_logger_missing_log_level_defaults_to_info(self, temp_logs_dir):
        """Test that missing LOG_LEVEL defaults to INFO."""
        logger = get_logger("test_module")
        assert logger.level == logging.INFO


class TestLogFormatting:
    """Test log message formatting."""

    @patch.dict(os.environ, {"LOG_LEVEL": "INFO"}, clear=True)
    def test_log_message_format(self, temp_logs_dir):
        """Test that log messages are formatted correctly."""
        logger = get_logger("my_module")
        logger.info("Test message")

        log_file = Path("logs") / "pip-bot.log"
        content = log_file.read_text()

        # Check format: [timestamp] [level] [name] message
        assert "[INFO" in content  # May have padding like [INFO    ]
        assert "[my_module]" in content
        assert "Test message" in content

    @patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}, clear=True)
    def test_log_levels_in_file(self, temp_logs_dir):
        """Test different log levels are recorded in file."""
        logger = get_logger("test_module")

        logger.debug("debug message")
        logger.info("info message")
        logger.warning("warning message")
        logger.error("error message")
        logger.critical("critical message")

        log_file = Path("logs") / "pip-bot.log"
        content = log_file.read_text()

        assert "debug message" in content
        assert "info message" in content
        assert "warning message" in content
        assert "error message" in content
        assert "critical message" in content
