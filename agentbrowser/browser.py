"""Playwright browser lifecycle and context management."""

from __future__ import annotations

from typing import TYPE_CHECKING

from playwright.async_api import async_playwright, Playwright, Browser, BrowserContext, Page

from .config import AgentConfig
from .stealth import apply_stealth, random_user_agent


class BrowserManager:
    """Manages Playwright browser lifecycle: launch, contexts, pages."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None

    @property
    def page(self) -> Page:
        if self._page is None:
            from .exceptions import BrowserNotStartedError
            raise BrowserNotStartedError()
        return self._page

    @property
    def context(self) -> BrowserContext:
        if self._context is None:
            from .exceptions import BrowserNotStartedError
            raise BrowserNotStartedError()
        return self._context

    async def start(self) -> Page:
        """Launch browser and return the active page."""
        self._playwright = await async_playwright().start()

        bc = self.config.browser
        launcher = getattr(self._playwright, bc.browser_type)

        self._browser = await launcher.launch(
            headless=bc.headless,
            slow_mo=bc.slow_mo,
        )

        ua = random_user_agent() if self.config.stealth.enabled else None
        self._context = await self._browser.new_context(
            viewport={"width": bc.viewport_width, "height": bc.viewport_height},
            locale=bc.locale,
            timezone_id=bc.timezone,
            user_agent=ua,
        )

        self._page = await self._context.new_page()

        # Apply stealth if enabled
        if self.config.stealth.enabled:
            await apply_stealth(self._page)

        return self._page

    async def new_page(self) -> Page:
        """Open a new page/tab in the current context."""
        if self._context is None:
            from .exceptions import BrowserNotStartedError
            raise BrowserNotStartedError()
        page = await self._context.new_page()
        if self.config.stealth.enabled:
            await apply_stealth(page)
        self._page = page
        return page

    async def close(self) -> None:
        """Clean up: close browser and playwright."""
        if self._context:
            try:
                await self._context.close()
            except Exception:
                pass
            self._context = None
        if self._browser:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None
        if self._playwright:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            self._playwright = None
        self._page = None
