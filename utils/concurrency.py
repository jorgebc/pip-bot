"""Async concurrency helpers."""

import asyncio
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


async def run_blocking(fn: Callable[..., T], *args: object) -> T:
    """
    Run a blocking callable in the default thread-pool executor.

    Wraps ``loop.run_in_executor(None, fn, *args)`` so callers don't
    repeat the same three-line boilerplate in every service module.

    Args:
        fn: Synchronous callable to execute off the event loop.
        *args: Positional arguments forwarded to ``fn``.

    Returns:
        The return value of ``fn(*args)``.
    """
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, fn, *args)
