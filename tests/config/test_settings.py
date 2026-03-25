"""Tests for config/settings.py module."""

import os
from unittest.mock import patch

import pytest

from config import ConfigError, Settings, get_settings, reset_settings


@pytest.fixture(autouse=True)
def reset_settings_cache():
    """Reset settings cache before and after each test."""
    reset_settings()
    yield
    reset_settings()


@pytest.fixture(autouse=True)
def isolate_env():
    """Isolate environment variables for each test."""
    # Save original environ
    original_env = os.environ.copy()
    yield
    # Restore original environ
    os.environ.clear()
    os.environ.update(original_env)


class TestSettingsDataclass:
    """Test Settings dataclass structure and defaults."""

    def test_settings_with_all_fields(self):
        """Test Settings instantiation with all fields."""
        settings = Settings(
            discord_token="test-token",
            discord_guild_id=12345,
            log_level="DEBUG",
            nas_host="192.168.1.100",
            nas_port=9091,
            nas_user="user",
            nas_password="pass",
        )

        assert settings.discord_token == "test-token"
        assert settings.discord_guild_id == 12345
        assert settings.log_level == "DEBUG"
        assert settings.nas_host == "192.168.1.100"
        assert settings.nas_port == 9091
        assert settings.nas_user == "user"
        assert settings.nas_password == "pass"

    def test_settings_with_required_fields_only(self):
        """Test Settings with only required fields."""
        settings = Settings(
            discord_token="test-token",
            discord_guild_id=12345,
        )

        assert settings.discord_token == "test-token"
        assert settings.discord_guild_id == 12345
        assert settings.log_level == "INFO"
        assert settings.nas_host is None
        assert settings.nas_port is None
        assert settings.nas_user is None
        assert settings.nas_password is None


class TestGetSettings:
    """Test get_settings() function."""

    @patch("config.settings.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "DISCORD_TOKEN": "test-token",
            "DISCORD_GUILD_ID": "12345",
        },
        clear=True,
    )
    def test_get_settings_with_required_env(self, mock_load_dotenv):
        """Test get_settings with only required env variables."""
        settings = get_settings()

        assert settings.discord_token == "test-token"
        assert settings.discord_guild_id == 12345
        assert settings.log_level == "INFO"  # Default

    @patch("config.settings.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "DISCORD_TOKEN": "test-token",
            "DISCORD_GUILD_ID": "99999",
            "LOG_LEVEL": "DEBUG",
            "NAS_HOST": "192.168.1.1",
            "NAS_PORT": "9091",
            "NAS_USER": "admin",
            "NAS_PASSWORD": "secret",
        },
        clear=True,
    )
    def test_get_settings_with_all_env(self, mock_load_dotenv):
        """Test get_settings with all environment variables."""
        settings = get_settings()

        assert settings.discord_token == "test-token"
        assert settings.discord_guild_id == 99999
        assert settings.log_level == "DEBUG"
        assert settings.nas_host == "192.168.1.1"
        assert settings.nas_port == 9091
        assert settings.nas_user == "admin"
        assert settings.nas_password == "secret"

    @patch("config.settings.load_dotenv")
    @patch.dict(os.environ, {"DISCORD_GUILD_ID": "12345"}, clear=True)
    def test_get_settings_missing_discord_token(self, mock_load_dotenv):
        """Test get_settings raises error when DISCORD_TOKEN is missing."""
        with pytest.raises(ConfigError, match="DISCORD_TOKEN is required"):
            get_settings()

    @patch("config.settings.load_dotenv")
    @patch.dict(os.environ, {"DISCORD_TOKEN": "test-token"}, clear=True)
    def test_get_settings_missing_discord_guild_id(self, mock_load_dotenv):
        """Test get_settings raises error when DISCORD_GUILD_ID is missing."""
        with pytest.raises(ConfigError, match="DISCORD_GUILD_ID is required"):
            get_settings()

    @patch("config.settings.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "DISCORD_TOKEN": "",
            "DISCORD_GUILD_ID": "12345",
        },
        clear=True,
    )
    def test_get_settings_empty_discord_token(self, mock_load_dotenv):
        """Test get_settings raises error when DISCORD_TOKEN is empty."""
        with pytest.raises(ConfigError, match="DISCORD_TOKEN is required"):
            get_settings()

    @patch("config.settings.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "DISCORD_TOKEN": "test-token",
            "DISCORD_GUILD_ID": "not-a-number",
        },
        clear=True,
    )
    def test_get_settings_invalid_guild_id_format(self, mock_load_dotenv):
        """Test get_settings raises error when DISCORD_GUILD_ID is not an integer."""
        with pytest.raises(ConfigError, match="DISCORD_GUILD_ID must be an integer"):
            get_settings()

    @patch("config.settings.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "DISCORD_TOKEN": "test-token",
            "DISCORD_GUILD_ID": "12345",
            "LOG_LEVEL": "INVALID",
        },
        clear=True,
    )
    def test_get_settings_invalid_log_level(self, mock_load_dotenv):
        """Test get_settings raises error with invalid LOG_LEVEL."""
        with pytest.raises(ConfigError, match="LOG_LEVEL must be one of"):
            get_settings()

    @patch("config.settings.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "DISCORD_TOKEN": "test-token",
            "DISCORD_GUILD_ID": "12345",
            "NAS_PORT": "not-a-number",
        },
        clear=True,
    )
    def test_get_settings_invalid_nas_port(self, mock_load_dotenv):
        """Test get_settings raises error when NAS_PORT is not an integer."""
        with pytest.raises(ConfigError, match="NAS_PORT must be an integer"):
            get_settings()

    @patch("config.settings.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "DISCORD_TOKEN": "test-token",
            "DISCORD_GUILD_ID": "12345",
            "LOG_LEVEL": "debug",  # lowercase
        },
        clear=True,
    )
    def test_get_settings_log_level_case_insensitive(self, mock_load_dotenv):
        """Test that LOG_LEVEL is case-insensitive."""
        settings = get_settings()
        assert settings.log_level == "DEBUG"

    @patch("config.settings.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "DISCORD_TOKEN": "test-token",
            "DISCORD_GUILD_ID": "12345",
        },
        clear=True,
    )
    def test_get_settings_caches_result(self, mock_load_dotenv):
        """Test that get_settings caches the result on subsequent calls."""
        settings1 = get_settings()

        # Modify environment (won't affect cached result)
        os.environ["LOG_LEVEL"] = "DEBUG"

        settings2 = get_settings()

        assert settings1 is settings2
        assert settings2.log_level == "INFO"  # Still original value


class TestResetSettings:
    """Test reset_settings() function."""

    @patch("config.settings.load_dotenv")
    @patch.dict(
        os.environ,
        {
            "DISCORD_TOKEN": "test-token",
            "DISCORD_GUILD_ID": "12345",
        },
        clear=True,
    )
    def test_reset_settings_clears_cache(self, mock_load_dotenv):
        """Test that reset_settings clears the cached settings."""
        settings1 = get_settings()
        reset_settings()

        # Modify environment and get new settings
        os.environ["LOG_LEVEL"] = "DEBUG"
        settings2 = get_settings()

        assert settings1 is not settings2
        assert settings1.log_level == "INFO"
        assert settings2.log_level == "DEBUG"


class TestConfigError:
    """Test ConfigError exception."""

    def test_config_error_is_exception(self):
        """Test that ConfigError is an Exception."""
        error = ConfigError("test error")
        assert isinstance(error, Exception)
        assert str(error) == "test error"

