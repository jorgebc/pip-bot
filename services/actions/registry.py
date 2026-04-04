"""Maps action names to handler functions for external agent actions."""

from collections.abc import Callable


def register_action(name: str, handler: Callable) -> None:
    """
    Register a named action handler (Phase 3).

    Args:
        name: Unique action name.
        handler: Callable that executes the action.

    Raises:
        NotImplementedError: Until Phase 3 is implemented.
    """
    raise NotImplementedError("register_action() is not yet implemented")


def get_action(name: str) -> Callable:
    """
    Retrieve a registered action handler by name (Phase 3).

    Args:
        name: Action name to look up.

    Returns:
        The registered handler callable.

    Raises:
        NotImplementedError: Until Phase 3 is implemented.
    """
    raise NotImplementedError("get_action() is not yet implemented")
