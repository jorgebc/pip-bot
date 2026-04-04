"""Tests for services/actions/handler.py and services/actions/registry.py."""

import pytest

from services.actions.handler import handle_action
from services.actions.registry import get_action, register_action


class TestHandleAction:
    """Tests for handle_action stub."""

    def test_handle_action_raises(self):
        """handle_action() must raise NotImplementedError until Phase 3."""
        with pytest.raises(NotImplementedError):
            handle_action("test_action", {})


class TestRegistry:
    """Tests for action registry stubs."""

    def test_register_action_raises(self):
        """register_action() must raise NotImplementedError until Phase 3."""
        with pytest.raises(NotImplementedError):
            register_action("test_action", lambda: None)

    def test_get_action_raises(self):
        """get_action() must raise NotImplementedError until Phase 3."""
        with pytest.raises(NotImplementedError):
            get_action("test_action")
