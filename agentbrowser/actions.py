"""High-level browser actions: click, type, select, scroll, hover with retries."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from .config import RetryConfig, StealthConfig
from .elements import FoundElement, find_element
from .exceptions import ElementNotFoundError, TimeoutError
from .stealth import random_delay

if TYPE_CHECKING:
    from playwright.async_api import Page


async def _with_retry(
    page: Page,
    query: str,
    config: RetryConfig,
) -> FoundElement:
    """Find an element with retries."""
    last_err: Exception | None = None
    for attempt in range(config.max_retries):
        try:
            return await find_element(page, query, config)
        except ElementNotFoundError as e:
            last_err = e
            if attempt < config.max_retries - 1:
                await asyncio.sleep(config.retry_delay_ms / 1000.0)
    raise last_err  # type: ignore[misc]


async def click(
    page: Page,
    query: str,
    *,
    retry: RetryConfig,
    stealth: StealthConfig,
    timeout_ms: int = 10000,
) -> FoundElement:
    """Click an element found by query (text, selector, role).

    Args:
        page: The Playwright page.
        query: Text, label, or CSS selector to find the element.
        retry: Retry configuration.
        stealth: Stealth configuration for delays.
        timeout_ms: Click timeout in milliseconds.

    Returns:
        The element that was clicked.
    """
    el = await _with_retry(page, query, retry)
    await el.locator.click(timeout=timeout_ms)
    await random_delay(stealth)
    return el


async def type_text(
    page: Page,
    query: str,
    text: str,
    *,
    clear: bool = True,
    submit: bool = False,
    retry: RetryConfig,
    stealth: StealthConfig,
    timeout_ms: int = 10000,
) -> FoundElement:
    """Type text into an element found by query.

    Args:
        page: The Playwright page.
        query: Text, label, or CSS selector to find the input.
        text: The text to type.
        clear: Whether to clear the field first.
        submit: Whether to press Enter after typing.
        retry: Retry configuration.
        stealth: Stealth configuration for typing delays.
        timeout_ms: Timeout in milliseconds.

    Returns:
        The element that was typed into.
    """
    el = await _with_retry(page, query, retry)
    if clear:
        await el.locator.clear(timeout=timeout_ms)
    if stealth.realistic_typing:
        await el.locator.press_sequentially(
            text,
            delay=stealth.typing_delay_min_ms,
            timeout=timeout_ms,
        )
    else:
        await el.locator.fill(text, timeout=timeout_ms)
    if submit:
        await el.locator.press("Enter")
    await random_delay(stealth)
    return el


async def hover(
    page: Page,
    query: str,
    *,
    retry: RetryConfig,
    stealth: StealthConfig,
    timeout_ms: int = 10000,
) -> FoundElement:
    """Hover over an element found by query."""
    el = await _with_retry(page, query, retry)
    await el.locator.hover(timeout=timeout_ms)
    await random_delay(stealth)
    return el


async def select_option(
    page: Page,
    query: str,
    value: str,
    *,
    retry: RetryConfig,
    stealth: StealthConfig,
    timeout_ms: int = 10000,
) -> FoundElement:
    """Select a dropdown option by visible text or value."""
    el = await _with_retry(page, query, retry)
    await el.locator.select_option(label=value, timeout=timeout_ms)
    await random_delay(stealth)
    return el


async def scroll_down(page: Page, pixels: int = 500) -> None:
    """Scroll down by a number of pixels."""
    await page.evaluate(f"window.scrollBy(0, {pixels})")


async def scroll_up(page: Page, pixels: int = 500) -> None:
    """Scroll up by a number of pixels."""
    await page.evaluate(f"window.scrollBy(0, -{pixels})")


async def scroll_to_element(
    page: Page,
    query: str,
    *,
    retry: RetryConfig,
    stealth: StealthConfig,
) -> FoundElement:
    """Scroll to an element found by query."""
    el = await _with_retry(page, query, retry)
    await el.locator.scroll_into_view_if_needed()
    await random_delay(stealth)
    return el


async def wait_for_text(
    page: Page,
    text: str,
    *,
    timeout_ms: int = 30000,
) -> None:
    """Wait for specific text to appear on the page."""
    try:
        await page.get_by_text(text).first.wait_for(
            state="visible", timeout=timeout_ms
        )
    except Exception as e:
        raise TimeoutError(f"wait_for_text('{text}')", timeout_ms) from e
