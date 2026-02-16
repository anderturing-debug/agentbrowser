"""Anti-detection: random delays, mouse jitter, UA rotation, stealth patches."""

from __future__ import annotations

import asyncio
import random
from typing import TYPE_CHECKING

from playwright_stealth import stealth_async  # type: ignore[import-untyped]

from .config import StealthConfig

if TYPE_CHECKING:
    from playwright.async_api import BrowserContext, Page

# Realistic user agents (Chrome on various platforms)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


def random_user_agent() -> str:
    """Pick a random realistic user agent string."""
    return random.choice(USER_AGENTS)


async def apply_stealth(page: Page) -> None:
    """Apply playwright-stealth patches to a page."""
    await stealth_async(page)


async def apply_context_stealth(context: BrowserContext) -> None:
    """Hook into context to apply stealth to every new page."""

    async def _on_page(page: Page) -> None:
        await apply_stealth(page)

    context.on("page", _on_page)


async def random_delay(config: StealthConfig) -> None:
    """Wait a random human-like delay between actions."""
    if not config.enabled:
        return
    delay_ms = random.randint(config.random_delay_min_ms, config.random_delay_max_ms)
    await asyncio.sleep(delay_ms / 1000.0)


async def human_type(page: Page, selector: str, text: str, config: StealthConfig) -> None:
    """Type text with realistic per-keystroke delays."""
    for char in text:
        await page.type(selector, char, delay=0)
        if config.realistic_typing:
            delay = random.randint(config.typing_delay_min_ms, config.typing_delay_max_ms)
            await asyncio.sleep(delay / 1000.0)


async def jitter_mouse(page: Page, x: int, y: int, config: StealthConfig) -> None:
    """Move mouse to position with slight random jitter."""
    if config.mouse_jitter:
        jitter = config.mouse_jitter_px
        x += random.randint(-jitter, jitter)
        y += random.randint(-jitter, jitter)
    await page.mouse.move(x, y, steps=random.randint(5, 15))
