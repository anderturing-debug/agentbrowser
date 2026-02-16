"""BrowserAgent — the core API for AI agent browser control.

This is the main class that ties everything together. It provides a high-level,
LLM-friendly API for browsing the web.

Usage:
    async with BrowserAgent(headless=True) as agent:
        await agent.goto("https://example.com")
        await agent.click("Sign in")
        await agent.type("Email", "user@example.com")
        summary = await agent.page_summary()
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from . import actions as act
from .browser import BrowserManager
from .config import AgentConfig, BrowserConfig, RetryConfig, StealthConfig
from .exceptions import BrowserNotStartedError, NavigationError
from .extraction import Link, TableData, get_links, get_tables, get_visible_text, get_meta
from .forms import DetectedForm, detect_forms, fill_form as _fill_form
from .page_state import page_summary as _page_summary
from .profiles import load_context_profile, save_context_profile
from .recorder import ActionRecorder, RecordedAction
from .screenshot import take_screenshot
from .stealth import random_delay
from .storage import Storage


class BrowserAgent:
    """High-level browser agent for AI-driven web interaction.

    Args:
        headless: Run browser in headless mode (default: True).
        profile: Load a saved profile (cookies/storage) on start.
        browser_type: Browser engine — "chromium", "firefox", or "webkit".
        stealth: Enable anti-detection features (default: True).
        timeout_ms: Default timeout in milliseconds.
        viewport: Tuple of (width, height) for the viewport.
        data_dir: Directory for storing profiles, recordings, etc.
    """

    def __init__(
        self,
        *,
        headless: bool = True,
        profile: str | None = None,
        browser_type: str = "chromium",
        stealth: bool = True,
        timeout_ms: int = 30000,
        viewport: tuple[int, int] = (1920, 1080),
        data_dir: str | Path | None = None,
    ) -> None:
        bc = BrowserConfig(
            headless=headless,
            browser_type=browser_type,  # type: ignore[arg-type]
            viewport_width=viewport[0],
            viewport_height=viewport[1],
            timeout_ms=timeout_ms,
            stealth=stealth,
        )
        sc = StealthConfig(enabled=stealth)
        self._config = AgentConfig(
            browser=bc,
            stealth=sc,
            profile=profile,
        )
        if data_dir:
            self._config.data_dir = Path(data_dir)
        self._config.ensure_dirs()

        self._manager = BrowserManager(self._config)
        self._storage = Storage(self._config.data_dir / "agentbrowser.db")
        self._recorder = ActionRecorder()
        self._started = False

    # --- Lifecycle ---

    async def start(self) -> None:
        """Start the browser. Called automatically by async context manager."""
        await self._manager.start()
        self._started = True

        # Load profile if specified
        if self._config.profile:
            await load_context_profile(
                self._manager.context,
                self._manager.page,
                self._config.profile,
                self._storage,
            )

    async def close(self) -> None:
        """Close the browser and clean up."""
        self._storage.close()
        await self._manager.close()
        self._started = False

    async def __aenter__(self) -> BrowserAgent:
        await self.start()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    def _ensure_started(self) -> None:
        if not self._started:
            raise BrowserNotStartedError()

    @property
    def page(self):
        """The current Playwright page."""
        self._ensure_started()
        return self._manager.page

    @property
    def url(self) -> str:
        """Current page URL."""
        return self.page.url

    @property
    def title(self) -> str:
        """This is async — use await agent.get_title() instead."""
        raise AttributeError("Use 'await agent.get_title()' instead of 'agent.title'")

    async def get_title(self) -> str:
        """Get the current page title."""
        return await self.page.title()

    # --- Navigation ---

    async def goto(self, url: str, *, wait_until: str = "domcontentloaded") -> None:
        """Navigate to a URL.

        Args:
            url: The URL to navigate to.
            wait_until: When to consider navigation complete.
                Options: "domcontentloaded", "load", "networkidle", "commit".
        """
        self._ensure_started()
        self._recorder.record("goto", url=url)
        try:
            await self.page.goto(url, wait_until=wait_until, timeout=self._config.browser.timeout_ms)
        except Exception as e:
            raise NavigationError(url, str(e)) from e
        await random_delay(self._config.stealth)

    async def back(self) -> None:
        """Navigate back."""
        self._ensure_started()
        self._recorder.record("back")
        await self.page.go_back(timeout=self._config.browser.timeout_ms)

    async def forward(self) -> None:
        """Navigate forward."""
        self._ensure_started()
        self._recorder.record("forward")
        await self.page.go_forward(timeout=self._config.browser.timeout_ms)

    async def refresh(self) -> None:
        """Refresh the current page."""
        self._ensure_started()
        self._recorder.record("refresh")
        await self.page.reload(timeout=self._config.browser.timeout_ms)

    # --- Element Interaction ---

    async def click(self, query: str, *, timeout_ms: int | None = None) -> None:
        """Click an element by text, label, or CSS selector.

        Uses smart element finding — fuzzy text matching, ARIA roles, labels.

        Args:
            query: Text content, label, placeholder, or CSS selector.
            timeout_ms: Override default timeout.

        Raises:
            ElementNotFoundError: With list of available elements.
        """
        self._ensure_started()
        self._recorder.record("click", query=query)
        await act.click(
            self.page,
            query,
            retry=self._config.retry,
            stealth=self._config.stealth,
            timeout_ms=timeout_ms or self._config.retry.element_timeout_ms,
        )

    async def type(
        self,
        query: str,
        text: str,
        *,
        clear: bool = True,
        submit: bool = False,
    ) -> None:
        """Type text into an element found by query.

        Args:
            query: Label, placeholder, or selector of the input field.
            text: The text to type.
            clear: Clear the field before typing (default: True).
            submit: Press Enter after typing (default: False).
        """
        self._ensure_started()
        self._recorder.record("type", query=query, text=text)
        await act.type_text(
            self.page,
            query,
            text,
            clear=clear,
            submit=submit,
            retry=self._config.retry,
            stealth=self._config.stealth,
        )

    async def hover(self, query: str) -> None:
        """Hover over an element found by query."""
        self._ensure_started()
        self._recorder.record("hover", query=query)
        await act.hover(
            self.page,
            query,
            retry=self._config.retry,
            stealth=self._config.stealth,
        )

    async def select(self, query: str, value: str) -> None:
        """Select a dropdown option by label text.

        Args:
            query: The select element (by label/text).
            value: The option to select (by visible text).
        """
        self._ensure_started()
        self._recorder.record("select", query=query, value=value)
        await act.select_option(
            self.page,
            query,
            value,
            retry=self._config.retry,
            stealth=self._config.stealth,
        )

    # --- Scrolling ---

    async def scroll_down(self, pixels: int = 500) -> None:
        """Scroll down by pixels."""
        self._ensure_started()
        self._recorder.record("scroll_down", pixels=pixels)
        await act.scroll_down(self.page, pixels)

    async def scroll_up(self, pixels: int = 500) -> None:
        """Scroll up by pixels."""
        self._ensure_started()
        self._recorder.record("scroll_up", pixels=pixels)
        await act.scroll_up(self.page, pixels)

    async def scroll_to(self, query: str) -> None:
        """Scroll to an element found by query."""
        self._ensure_started()
        self._recorder.record("scroll_to", query=query)
        await act.scroll_to_element(
            self.page,
            query,
            retry=self._config.retry,
            stealth=self._config.stealth,
        )

    # --- Waiting ---

    async def wait_for(self, text: str, *, timeout_ms: int | None = None) -> None:
        """Wait for text to appear on the page.

        Args:
            text: The text to wait for.
            timeout_ms: Maximum wait time in milliseconds.
        """
        self._ensure_started()
        await act.wait_for_text(
            self.page,
            text,
            timeout_ms=timeout_ms or self._config.browser.timeout_ms,
        )

    async def wait(self, ms: int) -> None:
        """Wait for a fixed duration (use sparingly)."""
        await asyncio.sleep(ms / 1000.0)

    # --- Content Extraction ---

    async def get_text(self) -> str:
        """Get all visible text from the page."""
        self._ensure_started()
        return await get_visible_text(self.page)

    async def get_links(self) -> list[Link]:
        """Get all links from the page."""
        self._ensure_started()
        return await get_links(self.page)

    async def get_tables(self) -> list[TableData]:
        """Get all tables from the page."""
        self._ensure_started()
        return await get_tables(self.page)

    async def get_meta(self) -> dict[str, str]:
        """Get page metadata (title, description, URL, etc.)."""
        self._ensure_started()
        return await get_meta(self.page)

    # --- Page Summary ---

    async def page_summary(self, *, max_items: int = 20) -> str:
        """Get an LLM-friendly summary of the current page state.

        Returns a structured text description of the page including
        visible elements, forms, navigation, and content preview.
        Perfect for feeding to an AI agent to understand the page.
        """
        self._ensure_started()
        return await _page_summary(self.page, max_items=max_items)

    # --- Screenshots ---

    async def screenshot(
        self,
        path: str | Path | None = None,
        *,
        full_page: bool = False,
        element: str | None = None,
    ) -> str:
        """Take a screenshot.

        Args:
            path: File path to save (optional). Returns base64 either way.
            full_page: Capture full scrollable page.
            element: Screenshot only this element (by text/selector).

        Returns:
            Base64-encoded screenshot data.
        """
        self._ensure_started()
        self._recorder.record("screenshot", path=str(path) if path else None)
        return await take_screenshot(
            self.page,
            path=path,
            full_page=full_page,
            element_query=element,
            retry=self._config.retry,
        )

    # --- Forms ---

    async def fill_form(
        self,
        fields: dict[str, str],
        *,
        submit: bool = False,
    ) -> None:
        """Fill form fields by label name.

        Args:
            fields: Mapping of label text to value.
                Example: {"Email": "user@example.com", "Password": "secret"}
            submit: Click submit after filling (default: False).
        """
        self._ensure_started()
        self._recorder.record("fill_form", fields=fields, submit=submit)
        await _fill_form(
            self.page,
            fields,
            submit=submit,
            retry=self._config.retry,
            stealth=self._config.stealth,
        )

    async def detect_forms(self) -> list[DetectedForm]:
        """Detect all forms on the current page."""
        self._ensure_started()
        return await detect_forms(self.page)

    # --- Profiles ---

    async def save_profile(self, name: str) -> None:
        """Save the current browser state as a named profile.

        Captures cookies, localStorage, and sessionStorage.
        Can be reloaded later with BrowserAgent(profile="name").
        """
        self._ensure_started()
        await save_context_profile(
            self._manager.context,
            self.page,
            name,
            self._storage,
        )

    async def load_profile(self, name: str) -> bool:
        """Load a saved profile into the current session.

        Returns True if profile was found and loaded.
        """
        self._ensure_started()
        return await load_context_profile(
            self._manager.context,
            self.page,
            name,
            self._storage,
        )

    def list_profiles(self) -> list[dict[str, str]]:
        """List all saved profiles."""
        return self._storage.list_profiles()

    # --- Recording ---

    def start_recording(self) -> None:
        """Start recording actions for later replay."""
        self._recorder.start()

    def stop_recording(self) -> list[RecordedAction]:
        """Stop recording and return the recorded actions."""
        return self._recorder.stop()

    def save_recording(self, name: str, description: str = "") -> None:
        """Save the current recording."""
        self._recorder.save(name, self._storage, description)

    async def replay(self, name: str) -> None:
        """Replay a saved recording.

        Args:
            name: Name of the recording to replay.
        """
        self._ensure_started()
        actions = ActionRecorder.load(name, self._storage)
        for recorded in actions:
            method = getattr(self, recorded.action, None)
            if method is None:
                continue
            if asyncio.iscoroutinefunction(method):
                await method(**recorded.args)
            else:
                method(**recorded.args)

    # --- Keyboard & Mouse ---

    async def press(self, key: str) -> None:
        """Press a keyboard key (e.g., 'Enter', 'Tab', 'Escape')."""
        self._ensure_started()
        self._recorder.record("press", key=key)
        await self.page.keyboard.press(key)

    async def evaluate(self, expression: str) -> Any:
        """Evaluate JavaScript in the page context."""
        self._ensure_started()
        return await self.page.evaluate(expression)
