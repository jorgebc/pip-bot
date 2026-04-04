"""Tests for utils/filters.py — TokenSanitizationFilter branches not covered by logger tests."""

import logging

from utils.filters import TokenSanitizationFilter


def _make_record(msg: str, args=None) -> logging.LogRecord:
    """Create a minimal LogRecord for filter testing.

    args is set after construction to bypass LogRecord.__init__'s Mapping
    detection logic, which performs args[0] and raises KeyError on dicts
    with non-integer keys (Python 3.12+).
    """
    record = logging.LogRecord(
        name="test", level=logging.INFO, pathname="", lineno=0,
        msg=msg, args=None, exc_info=None,
    )
    if args is not None:
        record.args = args
    return record


class TestFilterArgs:
    """Cover the dict-args and tuple-args branches of TokenSanitizationFilter.filter()."""

    def test_filter_sanitizes_dict_args_with_sensitive_key(self):
        """Dict args containing a sensitive key should have their value redacted."""
        f = TokenSanitizationFilter()
        record = _make_record("msg", args={"token": "supersecretvalue12345"})
        result = f.filter(record)
        assert result is True
        assert record.args["token"] == "***"  # type: ignore[index]

    def test_filter_passes_dict_args_with_non_sensitive_key(self):
        """Dict args with non-sensitive keys should be left unchanged."""
        f = TokenSanitizationFilter()
        record = _make_record("msg", args={"username": "jorge"})
        result = f.filter(record)
        assert result is True
        assert record.args["username"] == "jorge"  # type: ignore[index]

    def test_filter_sanitizes_tuple_args(self):
        """Tuple args are processed by _sanitize_value for each element."""
        f = TokenSanitizationFilter()
        record = _make_record("msg %s %s", args=("short", "normal"))
        result = f.filter(record)
        assert result is True
        assert isinstance(record.args, tuple)

    def test_filter_sanitizes_list_args(self):
        """List args (edge case) are processed the same as tuple args."""
        f = TokenSanitizationFilter()
        record = _make_record("msg %s", args=["value"])
        result = f.filter(record)
        assert result is True
        assert isinstance(record.args, tuple)


class TestSanitizeValue:
    """Cover the _sanitize_value branches."""

    def test_returns_star_for_token_pattern_match(self):
        """A value matching the three-segment Discord token pattern is redacted."""
        f = TokenSanitizationFilter()
        # 25 chars . 6 chars . 27 chars — matches TOKEN_PATTERN
        token = "A" * 25 + "." + "B" * 6 + "." + "C" * 27
        assert f._sanitize_value(token) == "***"

    def test_returns_star_for_long_alphanumeric(self):
        """A long alphanumeric string (20+ chars) that doesn't match the token
        pattern but looks like a hash or base64 is still redacted."""
        f = TokenSanitizationFilter()
        assert f._sanitize_value("A" * 20) == "***"

    def test_returns_value_unchanged_for_short_string(self):
        """Strings of 8 characters or fewer are not considered sensitive."""
        f = TokenSanitizationFilter()
        assert f._sanitize_value("short") == "short"

    def test_returns_value_unchanged_for_non_string(self):
        """Non-string values are passed through as-is."""
        f = TokenSanitizationFilter()
        assert f._sanitize_value(42) == 42  # type: ignore[arg-type]
