"""Smart element finding — by text, CSS selector, ARIA role, or fuzzy match."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from .config import RetryConfig
from .exceptions import ElementNotFoundError

if TYPE_CHECKING:
    from playwright.async_api import ElementHandle, Locator, Page


@dataclass
class FoundElement:
    """An element found on the page with metadata."""

    locator: Locator
    tag: str
    text: str
    role: str | None = None
    label: str | None = None

    def __repr__(self) -> str:
        return f"<FoundElement tag={self.tag!r} text={self.text[:40]!r}>"


def _normalize(text: str) -> str:
    """Normalize text for fuzzy matching."""
    return re.sub(r"\s+", " ", text.strip().lower())


def _fuzzy_match(query: str, text: str) -> bool:
    """Check if query fuzzy-matches text (case-insensitive, whitespace-normalized)."""
    q = _normalize(query)
    t = _normalize(text)
    return q == t or q in t


async def find_element(
    page: Page,
    query: str,
    config: RetryConfig | None = None,
) -> FoundElement:
    """Find a single element by text, label, placeholder, selector, or role.

    Search order:
    1. Exact CSS selector (if query looks like one)
    2. ARIA role + name
    3. Label text (for inputs)
    4. Button/link text
    5. Placeholder text
    6. Any visible text content (fuzzy)

    Raises ElementNotFoundError with helpful alternatives if not found.
    """
    # 1. Try as CSS selector first (if it has selector-like chars)
    if _looks_like_selector(query):
        loc = page.locator(query)
        if await loc.count() > 0:
            first = loc.first
            tag = await first.evaluate("el => el.tagName.toLowerCase()") or "unknown"
            text = (await first.inner_text()).strip()[:100] if tag not in ("input", "select", "textarea") else ""
            return FoundElement(locator=first, tag=tag, text=text)

    # 2. Try get_by_role for common interactive elements
    for role in ("button", "link", "menuitem", "tab", "option"):
        loc = page.get_by_role(role, name=re.compile(re.escape(query), re.IGNORECASE))
        if await loc.count() > 0:
            first = loc.first
            tag = await first.evaluate("el => el.tagName.toLowerCase()") or role
            text = (await first.inner_text()).strip()[:100]
            return FoundElement(locator=first, tag=tag, text=text, role=role)

    # 3. Try by label (for form inputs)
    loc = page.get_by_label(re.compile(re.escape(query), re.IGNORECASE))
    if await loc.count() > 0:
        first = loc.first
        tag = await first.evaluate("el => el.tagName.toLowerCase()") or "input"
        return FoundElement(locator=first, tag=tag, text="", label=query)

    # 4. Try by placeholder
    loc = page.get_by_placeholder(re.compile(re.escape(query), re.IGNORECASE))
    if await loc.count() > 0:
        first = loc.first
        tag = await first.evaluate("el => el.tagName.toLowerCase()") or "input"
        return FoundElement(locator=first, tag=tag, text="", label=query)

    # 5. Try by text content (any element)
    loc = page.get_by_text(re.compile(re.escape(query), re.IGNORECASE))
    if await loc.count() > 0:
        first = loc.first
        tag = await first.evaluate("el => el.tagName.toLowerCase()") or "unknown"
        text = (await first.inner_text()).strip()[:100]
        return FoundElement(locator=first, tag=tag, text=text)

    # 6. Try by title or aria-label attribute
    loc = page.locator(f'[title="{query}" i], [aria-label="{query}" i]')
    if await loc.count() > 0:
        first = loc.first
        tag = await first.evaluate("el => el.tagName.toLowerCase()") or "unknown"
        text_val = await first.inner_text() if tag not in ("input", "select", "textarea") else ""
        return FoundElement(locator=first, tag=tag, text=text_val.strip()[:100])

    # Not found — collect available elements for helpful error
    available = await _get_available_interactive(page)
    raise ElementNotFoundError(query, available)


async def find_all_by_role(page: Page, role: str) -> list[FoundElement]:
    """Find all elements with a given ARIA role."""
    loc = page.get_by_role(role)
    count = await loc.count()
    results: list[FoundElement] = []
    for i in range(min(count, 50)):
        el = loc.nth(i)
        tag = await el.evaluate("el => el.tagName.toLowerCase()") or role
        try:
            text = (await el.inner_text()).strip()[:100]
        except Exception:
            text = ""
        results.append(FoundElement(locator=el, tag=tag, text=text, role=role))
    return results


async def _get_available_interactive(page: Page, limit: int = 15) -> list[str]:
    """Get text of interactive elements for error messages."""
    items: list[str] = []
    for role in ("button", "link", "textbox", "menuitem"):
        loc = page.get_by_role(role)
        count = await loc.count()
        for i in range(min(count, 5)):
            el = loc.nth(i)
            try:
                name = (await el.inner_text()).strip()[:50]
                if name:
                    items.append(f"[{role}] {name}")
            except Exception:
                pass
        if len(items) >= limit:
            break
    return items[:limit]


def _looks_like_selector(query: str) -> bool:
    """Heuristic: does this look like a CSS/XPath selector rather than text?"""
    if query.startswith(("//", "xpath=")):
        return True
    if re.match(r"^[#.\[]", query):
        return True
    if "::" in query or " > " in query or " ~ " in query:
        return True
    return False
