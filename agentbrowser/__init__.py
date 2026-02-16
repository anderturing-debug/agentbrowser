"""agentbrowser — Give your AI agents a real browser.

Playwright-based, stealth-mode, with smart element finding
and LLM-friendly page summaries.

Usage:
    from agentbrowser import BrowserAgent

    async with BrowserAgent() as agent:
        await agent.goto("https://example.com")
        await agent.click("More information")
        summary = await agent.page_summary()
        print(summary)
"""

from .agent import BrowserAgent
from .exceptions import (
    AgentBrowserError,
    BrowserNotStartedError,
    ElementNotFoundError,
    NavigationError,
    PageError,
    ProfileError,
    RecordingError,
    TimeoutError,
)

__version__ = "0.1.0"
__all__ = [
    "BrowserAgent",
    "AgentBrowserError",
    "BrowserNotStartedError",
    "ElementNotFoundError",
    "NavigationError",
    "PageError",
    "ProfileError",
    "RecordingError",
    "TimeoutError",
]
