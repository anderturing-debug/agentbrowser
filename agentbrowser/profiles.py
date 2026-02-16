"""Browser profile management — cookies, localStorage, session persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .storage import Storage

if TYPE_CHECKING:
    from playwright.async_api import BrowserContext, Page


async def save_context_profile(
    context: BrowserContext,
    page: Page,
    name: str,
    storage: Storage,
) -> None:
    """Save the current browser context as a named profile.

    Captures cookies, localStorage, and sessionStorage.
    """
    cookies = await context.cookies()

    # Extract storage from the page
    storages = await page.evaluate("""() => {
        const ls = {};
        for (let i = 0; i < localStorage.length; i++) {
            const key = localStorage.key(i);
            ls[key] = localStorage.getItem(key);
        }
        const ss = {};
        for (let i = 0; i < sessionStorage.length; i++) {
            const key = sessionStorage.key(i);
            ss[key] = sessionStorage.getItem(key);
        }
        return { localStorage: ls, sessionStorage: ss };
    }""")

    storage.save_profile(
        name=name,
        cookies=cookies,
        local_storage=storages.get("localStorage", {}),
        session_storage=storages.get("sessionStorage", {}),
    )


async def load_context_profile(
    context: BrowserContext,
    page: Page,
    name: str,
    storage: Storage,
) -> bool:
    """Load a saved profile into the browser context.

    Returns True if profile was found and loaded, False otherwise.
    """
    profile = storage.load_profile(name)
    if profile is None:
        return False

    # Restore cookies
    cookies = profile.get("cookies", [])
    if cookies:
        await context.add_cookies(cookies)

    # Restore localStorage (requires a page)
    local_storage: dict[str, str] = profile.get("local_storage", {})
    if local_storage:
        for key, value in local_storage.items():
            await page.evaluate(
                f"localStorage.setItem({key!r}, {value!r})"
            )

    return True
