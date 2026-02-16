"""Custom exception hierarchy for agentbrowser."""

from __future__ import annotations


class AgentBrowserError(Exception):
    """Base exception for all agentbrowser errors."""


class BrowserNotStartedError(AgentBrowserError):
    """Raised when trying to use the browser before it's started."""

    def __init__(self) -> None:
        super().__init__(
            "Browser not started. Use 'async with BrowserAgent() as agent:' "
            "or call 'await agent.start()' first."
        )


class ElementNotFoundError(AgentBrowserError):
    """Raised when an element cannot be found on the page."""

    def __init__(self, query: str, available: list[str] | None = None) -> None:
        self.query = query
        self.available = available or []
        msg = f"Element '{query}' not found."
        if self.available:
            msg += f" Available: {self.available[:10]}"
        super().__init__(msg)


class NavigationError(AgentBrowserError):
    """Raised when navigation fails."""

    def __init__(self, url: str, reason: str = "") -> None:
        self.url = url
        msg = f"Failed to navigate to '{url}'"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class TimeoutError(AgentBrowserError):
    """Raised when an operation times out."""

    def __init__(self, operation: str, timeout_ms: int) -> None:
        self.operation = operation
        self.timeout_ms = timeout_ms
        super().__init__(f"Operation '{operation}' timed out after {timeout_ms}ms")


class ProfileError(AgentBrowserError):
    """Raised for profile-related errors."""


class RecordingError(AgentBrowserError):
    """Raised for recording/replay errors."""


class PageError(AgentBrowserError):
    """Raised when a page-level error occurs."""
