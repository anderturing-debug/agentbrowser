"""Page content extraction: text, links, tables, structured data."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from playwright.async_api import Page


@dataclass
class Link:
    """A link extracted from the page."""

    text: str
    href: str
    is_external: bool = False

    def __repr__(self) -> str:
        return f"Link({self.text!r}, {self.href!r})"


@dataclass
class TableData:
    """A table extracted from the page."""

    headers: list[str]
    rows: list[list[str]]


async def get_visible_text(page: Page) -> str:
    """Get all visible text content from the page.

    Excludes hidden elements, scripts, and styles.
    """
    return await page.evaluate("""() => {
        const walker = document.createTreeWalker(
            document.body,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: (node) => {
                    const el = node.parentElement;
                    if (!el) return NodeFilter.FILTER_REJECT;
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0')
                        return NodeFilter.FILTER_REJECT;
                    const tag = el.tagName.toLowerCase();
                    if (['script', 'style', 'noscript', 'template'].includes(tag))
                        return NodeFilter.FILTER_REJECT;
                    const text = node.textContent.trim();
                    if (!text) return NodeFilter.FILTER_REJECT;
                    return NodeFilter.FILTER_ACCEPT;
                }
            }
        );
        const texts = [];
        while (walker.nextNode()) {
            texts.push(walker.currentNode.textContent.trim());
        }
        return texts.join('\\n');
    }""")


async def get_links(page: Page) -> list[Link]:
    """Get all links from the page with their text and href."""
    raw: list[dict[str, str]] = await page.evaluate("""() => {
        const links = [];
        document.querySelectorAll('a[href]').forEach(a => {
            const text = a.innerText?.trim() || a.getAttribute('aria-label') || '';
            const href = a.href || '';
            if (text && href) {
                links.push({ text: text.slice(0, 200), href });
            }
        });
        return links;
    }""")
    current_origin = await page.evaluate("window.location.origin")
    return [
        Link(
            text=r["text"],
            href=r["href"],
            is_external=not r["href"].startswith(current_origin),
        )
        for r in raw
    ]


async def get_tables(page: Page) -> list[TableData]:
    """Extract all tables from the page."""
    raw: list[dict[str, Any]] = await page.evaluate("""() => {
        const tables = [];
        document.querySelectorAll('table').forEach(table => {
            const headers = [];
            table.querySelectorAll('thead th, thead td').forEach(th => {
                headers.push(th.innerText?.trim() || '');
            });
            const rows = [];
            table.querySelectorAll('tbody tr').forEach(tr => {
                const cells = [];
                tr.querySelectorAll('td, th').forEach(td => {
                    cells.push(td.innerText?.trim() || '');
                });
                if (cells.length) rows.push(cells);
            });
            tables.push({ headers, rows });
        });
        return tables;
    }""")
    return [TableData(headers=t["headers"], rows=t["rows"]) for t in raw]


async def get_meta(page: Page) -> dict[str, str]:
    """Get page metadata (title, description, url, etc.)."""
    return await page.evaluate("""() => {
        const meta = {};
        meta.title = document.title || '';
        meta.url = window.location.href;
        meta.origin = window.location.origin;
        const desc = document.querySelector('meta[name="description"]');
        if (desc) meta.description = desc.getAttribute('content') || '';
        const ogTitle = document.querySelector('meta[property="og:title"]');
        if (ogTitle) meta.og_title = ogTitle.getAttribute('content') || '';
        const ogDesc = document.querySelector('meta[property="og:description"]');
        if (ogDesc) meta.og_description = ogDesc.getAttribute('content') || '';
        return meta;
    }""")
