"""Screenshot capture: full page, viewport, or element."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import TYPE_CHECKING

from .elements import find_element
from .config import RetryConfig

if TYPE_CHECKING:
    from playwright.async_api import Page


async def take_screenshot(
    page: Page,
    path: str | Path | None = None,
    *,
    full_page: bool = False,
    element_query: str | None = None,
    quality: int | None = None,
    retry: RetryConfig | None = None,
) -> str:
    """Take a screenshot and return as base64 string.

    Args:
        page: The Playwright page.
        path: Optional file path to save the screenshot.
        full_page: Capture the full scrollable page.
        element_query: If provided, screenshot only this element.
        quality: JPEG quality (1-100). Only applies to JPEG format.
        retry: Retry config for element finding.

    Returns:
        Base64-encoded screenshot data.
    """
    kwargs: dict = {}
    if quality is not None:
        kwargs["quality"] = quality
        kwargs["type"] = "jpeg"

    if element_query and retry:
        el = await find_element(page, element_query, retry)
        raw = await el.locator.screenshot(**kwargs)
    elif full_page:
        raw = await page.screenshot(full_page=True, **kwargs)
    else:
        raw = await page.screenshot(**kwargs)

    if path:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(raw)

    return base64.b64encode(raw).decode("ascii")
