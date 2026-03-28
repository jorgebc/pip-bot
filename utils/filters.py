"""Logging filters for sanitizing sensitive data."""

import logging
import re


class TokenSanitizationFilter(logging.Filter):
    """Filter that sanitizes Discord tokens and other sensitive data from log records."""

    # Pattern to match Discord tokens (typical format)
    TOKEN_PATTERN = re.compile(r"([A-Za-z0-9._-]{24,})(\.[A-Za-z0-9._-]{6,})?(\.[A-Za-z0-9_-]{27,})?")

    # Common sensitive environment variable names
    SENSITIVE_KEYS = {
        "token", "password", "secret", "key", "api_key",
        "discord_token", "nas_password"
    }

    def filter(self, record: logging.LogRecord) -> bool:
        """Sanitize the log record message and exc_text."""
        if record.msg:
            # Handle different message types
            if isinstance(record.msg, str):
                record.msg = self._sanitize_message(record.msg)
            if record.args and isinstance(record.args, dict):
                record.args = self._sanitize_dict(record.args)
            elif record.args and isinstance(record.args, (tuple, list)):
                record.args = tuple(self._sanitize_value(v) for v in record.args)

        # Sanitize exception text if present
        if record.exc_text:
            record.exc_text = self._sanitize_message(record.exc_text)

        return True

    def _sanitize_message(self, message: str) -> str:
        """Replace tokens and sensitive values in message."""
        # Replace Discord-like tokens
        message = self.TOKEN_PATTERN.sub(r"\1.****", message)

        # Replace values in key=value patterns for sensitive keys
        for key in self.SENSITIVE_KEYS:
            pattern = rf"({re.escape(key)})=(['\"])([^'\"]+)(['\"])"
            message = re.sub(pattern, rf"\1=\2***\4", message, flags=re.IGNORECASE)

        return message

    def _sanitize_dict(self, d: dict) -> dict:
        """Sanitize values in a dictionary."""
        return {
            k: self._sanitize_value(v) if any(
                sensitive in k.lower() for sensitive in self.SENSITIVE_KEYS
            ) else v
            for k, v in d.items()
        }

    def _sanitize_value(self, value) -> str:
        """Sanitize a value if it looks like a token or password."""
        if isinstance(value, str) and len(value) > 8:
            # Check if value looks like a token (long string with specific format)
            if self.TOKEN_PATTERN.match(value):
                return "***"
            # Check if it looks like base64 or hash
            if re.match(r"^[A-Za-z0-9._-]{20,}$", value):
                return "***"
        return value
