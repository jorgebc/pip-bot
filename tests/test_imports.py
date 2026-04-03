"""Test that all modules can be imported without circular dependencies."""

import pytest


class TestImports:
    """Test module import correctness."""

    def test_import_config(self):
        """Test that config module can be imported."""
        import config
        assert config is not None

    def test_import_utils(self):
        """Test that utils module can be imported."""
        import utils
        assert utils is not None

    def test_import_bot(self):
        """Test that bot module can be imported."""
        import bot
        assert bot is not None

    def test_import_services(self):
        """Test that services module can be imported."""
        import services
        assert services is not None

    def test_import_cogs(self):
        """Test that cogs module can be imported."""
        import cogs
        assert cogs is not None

    def test_no_circular_imports(self):
        """Test that importing main modules doesn't cause circular import errors."""
        # This is a smoke test - if circular imports exist, this will raise ImportError
        try:
            import config.settings  # noqa: F401
            import utils.logger  # noqa: F401
            import utils.filters  # noqa: F401
            import bot.client  # noqa: F401
            import services.system  # noqa: F401
            import services.base  # noqa: F401
            assert True
        except ImportError as e:
            pytest.fail(f"Circular import detected: {e}")
