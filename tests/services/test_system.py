"""Tests for services/system.py module."""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from services.system import (
    SystemStatus,
    _format_timedelta,
    get_cpu_temperature,
    get_system_status,
)


class TestFormatTimedelta:
    """Test the _format_timedelta helper function."""

    def test_format_timedelta_days_hours_minutes(self):
        """Test formatting with days, hours, and minutes."""
        delta = timedelta(days=5, hours=3, minutes=42)
        result = _format_timedelta(delta)
        assert result == "5d 3h 42m"

    def test_format_timedelta_hours_minutes(self):
        """Test formatting with only hours and minutes."""
        delta = timedelta(hours=2, minutes=30)
        result = _format_timedelta(delta)
        assert result == "2h 30m"

    def test_format_timedelta_minutes_only(self):
        """Test formatting with only minutes."""
        delta = timedelta(minutes=15)
        result = _format_timedelta(delta)
        assert result == "15m"

    def test_format_timedelta_zero(self):
        """Test formatting with zero time."""
        delta = timedelta(seconds=0)
        result = _format_timedelta(delta)
        assert result == "0m"

    def test_format_timedelta_seconds_only(self):
        """Test formatting with less than a minute."""
        delta = timedelta(seconds=45)
        result = _format_timedelta(delta)
        assert result == "0m"

    def test_format_timedelta_days_only(self):
        """Test formatting with days only."""
        delta = timedelta(days=10)
        result = _format_timedelta(delta)
        assert result == "10d"


class TestGetSystemStatus:
    """Test the get_system_status function."""

    @patch("services.system.psutil.boot_time")
    @patch("services.system.psutil.cpu_percent")
    @patch("services.system.psutil.virtual_memory")
    @patch("services.system.psutil.disk_usage")
    @patch("services.system.datetime")
    def test_get_system_status_success(
        self,
        mock_datetime,
        mock_disk_usage,
        mock_virtual_memory,
        mock_cpu_percent,
        mock_boot_time,
    ):
        """Test successful system status collection."""
        # Setup mocks
        now = datetime(2026, 3, 26, 12, 0, 0)
        boot_time = datetime(2026, 3, 20, 12, 0, 0)  # 6 days ago

        mock_datetime.now.return_value = now
        mock_datetime.fromtimestamp.return_value = boot_time
        mock_boot_time.return_value = boot_time.timestamp()
        mock_cpu_percent.return_value = 35.5
        mock_virtual_memory.return_value = MagicMock(
            percent=60.0,
            used=2 * 1024**3,  # 2 GB
            total=4 * 1024**3,  # 4 GB
        )
        mock_disk_usage.return_value = MagicMock(
            percent=45.0,
            used=450 * 1024**3,  # 450 GB
            total=1000 * 1024**3,  # 1 TB
        )

        # Call function
        status = get_system_status()

        # Verify result is SystemStatus object
        assert isinstance(status, SystemStatus)

        # Verify values
        assert "6d" in status.uptime
        assert status.cpu_percent == 35.5
        assert status.ram_percent == 60.0
        assert status.ram_used_gb == 2.0
        assert status.ram_total_gb == 4.0
        assert status.disk_percent == 45.0
        assert status.disk_used_gb == 450.0
        assert status.disk_total_gb == 1000.0

        # Verify method calls
        mock_cpu_percent.assert_called_once_with(interval=None)
        mock_virtual_memory.assert_called_once()
        mock_disk_usage.assert_called_once_with("/")

    @patch("services.system.psutil.boot_time")
    @patch("services.system.psutil.cpu_percent")
    def test_get_system_status_psutil_error(self, mock_cpu_percent, mock_boot_time):
        """Test error handling when psutil fails."""
        mock_boot_time.side_effect = OSError("Permission denied")

        with pytest.raises(Exception):
            get_system_status()

    @patch("services.system.psutil.boot_time")
    @patch("services.system.psutil.cpu_percent")
    @patch("services.system.psutil.virtual_memory")
    @patch("services.system.psutil.disk_usage")
    @patch("services.system.datetime")
    def test_get_system_status_zero_uptime(
        self,
        mock_datetime,
        mock_disk_usage,
        mock_virtual_memory,
        mock_cpu_percent,
        mock_boot_time,
    ):
        """Test system status with zero uptime (just booted)."""
        now = datetime(2026, 3, 26, 12, 0, 0)
        boot_time = datetime(2026, 3, 26, 11, 59, 30)  # 30 seconds ago

        mock_datetime.now.return_value = now
        mock_datetime.fromtimestamp.return_value = boot_time
        mock_boot_time.return_value = boot_time.timestamp()
        mock_cpu_percent.return_value = 10.0
        mock_virtual_memory.return_value = MagicMock(
            percent=40.0,
            used=1.6 * 1024**3,
            total=4 * 1024**3,
        )
        mock_disk_usage.return_value = MagicMock(
            percent=30.0,
            used=300 * 1024**3,
            total=1000 * 1024**3,
        )

        status = get_system_status()

        assert "0m" in status.uptime
        assert status.cpu_percent == 10.0


class TestGetCpuTemperature:
    """Test the get_cpu_temperature function."""

    @patch("services.system._THERMAL_PATH")
    def test_returns_celsius_value(self, mock_path):
        """Test that millidegree value is correctly converted to Celsius."""
        mock_path.read_text.return_value = "51234\n"
        result = get_cpu_temperature()
        assert result == pytest.approx(51.234)

    @patch("services.system._THERMAL_PATH")
    def test_strips_whitespace(self, mock_path):
        """Test that leading/trailing whitespace is handled."""
        mock_path.read_text.return_value = "  48000  "
        result = get_cpu_temperature()
        assert result == pytest.approx(48.0)

    @patch("services.system._THERMAL_PATH")
    def test_file_not_found_raises(self, mock_path):
        """Test that FileNotFoundError is raised when thermal file is absent."""
        mock_path.read_text.side_effect = FileNotFoundError("no such file")
        with pytest.raises(FileNotFoundError):
            get_cpu_temperature()

    @patch("services.system._THERMAL_PATH")
    def test_os_error_raises(self, mock_path):
        """Test that OSError is propagated on read failure."""
        mock_path.read_text.side_effect = OSError("permission denied")
        with pytest.raises(OSError):
            get_cpu_temperature()

    @patch("services.system._THERMAL_PATH")
    def test_invalid_content_raises_value_error(self, mock_path):
        """Test that non-numeric file content raises ValueError."""
        mock_path.read_text.return_value = "not_a_number"
        with pytest.raises(ValueError):
            get_cpu_temperature()

    @patch("services.system._THERMAL_PATH")
    def test_high_temperature(self, mock_path):
        """Test temperature reading at a high value (>=70°C)."""
        mock_path.read_text.return_value = "75000"
        result = get_cpu_temperature()
        assert result >= 70.0


class TestSystemStatusDataclass:
    """Test the SystemStatus dataclass."""

    def test_system_status_creation(self):
        """Test creating a SystemStatus object."""
        status = SystemStatus(
            uptime="5d 3h 42m",
            cpu_percent=35.5,
            ram_percent=60.0,
            ram_used_gb=2.0,
            ram_total_gb=4.0,
            disk_percent=45.0,
            disk_used_gb=450.0,
            disk_total_gb=1000.0,
        )

        assert status.uptime == "5d 3h 42m"
        assert status.cpu_percent == 35.5
        assert status.ram_percent == 60.0
        assert status.ram_used_gb == 2.0
        assert status.ram_total_gb == 4.0
        assert status.disk_percent == 45.0
        assert status.disk_used_gb == 450.0
        assert status.disk_total_gb == 1000.0
