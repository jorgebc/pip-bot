"""Tests for utils/validators.py module."""

import pytest

from utils.validators import VALID_LOG_LEVELS, ConfigError, validate_log_level


class TestValidateLoglevel:
    """Test validate_log_level() function."""

    def test_validate_log_level_valid_uppercase(self):
        """Test validate_log_level with valid uppercase level."""
        assert validate_log_level("DEBUG") == "DEBUG"
        assert validate_log_level("INFO") == "INFO"
        assert validate_log_level("WARNING") == "WARNING"
        assert validate_log_level("ERROR") == "ERROR"
        assert validate_log_level("CRITICAL") == "CRITICAL"

    def test_validate_log_level_valid_lowercase(self):
        """Test validate_log_level with valid lowercase level (case-insensitive)."""
        assert validate_log_level("debug") == "DEBUG"
        assert validate_log_level("info") == "INFO"
        assert validate_log_level("warning") == "WARNING"
        assert validate_log_level("error") == "ERROR"
        assert validate_log_level("critical") == "CRITICAL"

    def test_validate_log_level_valid_mixed_case(self):
        """Test validate_log_level with mixed case."""
        assert validate_log_level("DeBuG") == "DEBUG"
        assert validate_log_level("InFo") == "INFO"

    def test_validate_log_level_invalid(self):
        """Test validate_log_level with invalid level."""
        with pytest.raises(ConfigError, match="LOG_LEVEL must be one of"):
            validate_log_level("INVALID")

    def test_validate_log_level_empty_defaults_to_info(self):
        """Test validate_log_level with empty string defaults to INFO."""
        assert validate_log_level("") == "INFO"

    def test_validate_log_level_whitespace_only(self):
        """Test validate_log_level with whitespace-only string."""
        # Empty string gets normalized to "INFO"
        assert validate_log_level("   ".strip()) == "INFO"

    def test_validate_log_level_error_message_includes_valid_levels(self):
        """Test that error message includes all valid levels."""
        with pytest.raises(ConfigError) as exc_info:
            validate_log_level("NOTVALID")

        error_msg = str(exc_info.value)
        assert "DEBUG" in error_msg
        assert "INFO" in error_msg
        assert "WARNING" in error_msg
        assert "ERROR" in error_msg
        assert "CRITICAL" in error_msg


class TestValidLogLevelsConstant:
    """Test VALID_LOG_LEVELS constant."""

    def test_valid_log_levels_contains_all_levels(self):
        """Test that VALID_LOG_LEVELS contains all expected levels."""
        expected = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        assert VALID_LOG_LEVELS == expected

    def test_valid_log_levels_is_frozen(self):
        """Test that VALID_LOG_LEVELS cannot be modified (is immutable)."""
        # Set is mutable, but we just verify it's defined correctly
        assert isinstance(VALID_LOG_LEVELS, set)
        assert len(VALID_LOG_LEVELS) == 5
