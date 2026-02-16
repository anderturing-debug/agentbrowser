"""LLM-friendly page state summarization — the killer feature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .extraction import get_links, get_meta
from .forms import detect_forms

if TYPE_CHECKING:
    from playwright.async_api import Page


async def page_summary(page: Page, *, max_items: int = 20) -> str:
    """Generate an LLM-friendly summary of the current page state.

    Returns a structured text summary including:
    - URL and title
    - Visible interactive elements (buttons, links, inputs)
    - Forms and their fields
    - Navigation elements
    - Key content snippets

    Args:
        page: The Playwright page.
        max_items: Maximum number of items per category.

    Returns:
        A formatted string suitable for LLM consumption.
    """
    meta = await get_meta(page)
    lines: list[str] = []

    # Header
    lines.append(f"URL: {meta.get('url', 'unknown')}")
    lines.append(f"Title: {meta.get('title', 'untitled')}")
    lines.append("")

    # Interactive elements by role
    lines.append("VISIBLE ELEMENTS:")
    for role in ("button", "link", "textbox", "combobox", "checkbox", "radio", "tab", "menuitem"):
        loc = page.get_by_role(role)
        count = await loc.count()
        for i in range(min(count, max_items)):
            el = loc.nth(i)
            try:
                visible = await el.is_visible()
                if not visible:
                    continue
                # Get display text
                if role in ("textbox", "combobox"):
                    name = await el.get_attribute("placeholder") or await el.get_attribute("aria-label") or ""
                    value = await el.input_value() if role == "textbox" else ""
                    entry = f'- [{role}] "{name}"'
                    if value:
                        entry += f' (value: "{value[:50]}")'
                else:
                    try:
                        name = (await el.inner_text()).strip()[:80]
                    except Exception:
                        name = await el.get_attribute("aria-label") or ""
                    if not name:
                        continue
                    entry = f'- [{role}] "{name}"'

                # Check state
                if role in ("checkbox", "radio"):
                    checked = await el.is_checked()
                    entry += f" ({'checked' if checked else 'unchecked'})"
                elif role == "tab":
                    selected = await el.get_attribute("aria-selected")
                    if selected == "true":
                        entry += " (active)"

                lines.append(entry)
            except Exception:
                continue

    lines.append("")

    # Forms
    forms = await detect_forms(page)
    if forms:
        lines.append("FORMS:")
        for j, form in enumerate(forms[:3]):
            lines.append(f"  Form {j + 1} (action: {form.action or 'N/A'}, method: {form.method}):")
            for ff in form.fields[:10]:
                req = " *required" if ff.required else ""
                if ff.options:
                    lines.append(f'    - [{ff.field_type}] "{ff.label}" options: {ff.options[:5]}{req}')
                else:
                    placeholder = f' (placeholder: "{ff.placeholder}")' if ff.placeholder else ""
                    lines.append(f'    - [{ff.field_type}] "{ff.label}"{placeholder}{req}')
            lines.append(f'    Submit: "{form.submit_text}"')
    else:
        lines.append("FORMS: None visible")
    lines.append("")

    # Links summary (navigation-like)
    all_links = await get_links(page)
    nav_links = [l for l in all_links if not l.is_external and len(l.text) < 30][:max_items]
    if nav_links:
        lines.append("NAVIGATION: " + " | ".join(l.text for l in nav_links[:10]))
    lines.append("")

    # Content snippet
    text_content = await page.evaluate("""() => {
        const main = document.querySelector('main, [role="main"], article, .content, #content');
        const target = main || document.body;
        return target.innerText?.slice(0, 500) || '';
    }""")
    if text_content.strip():
        lines.append("PAGE CONTENT (preview):")
        for line in text_content.strip().split("\n")[:8]:
            cleaned = line.strip()
            if cleaned:
                lines.append(f"  {cleaned}")

    return "\n".join(lines)
