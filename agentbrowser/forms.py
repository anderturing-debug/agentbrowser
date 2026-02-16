"""Form detection, filling by label, and submission."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .elements import find_element
from .config import RetryConfig, StealthConfig
from .stealth import random_delay

if TYPE_CHECKING:
    from playwright.async_api import Page


@dataclass
class FormField:
    """A detected form field."""

    label: str
    field_type: str  # text, password, email, select, textarea, checkbox, radio, etc.
    name: str
    placeholder: str = ""
    required: bool = False
    options: list[str] = field(default_factory=list)  # for select/radio


@dataclass
class DetectedForm:
    """A form detected on the page."""

    action: str
    method: str
    fields: list[FormField]
    submit_text: str = "Submit"


async def detect_forms(page: Page) -> list[DetectedForm]:
    """Detect all forms on the page with their fields."""
    raw = await page.evaluate("""() => {
        const forms = [];
        document.querySelectorAll('form').forEach(form => {
            const fields = [];
            form.querySelectorAll('input, select, textarea').forEach(el => {
                const tag = el.tagName.toLowerCase();
                const type = el.type || (tag === 'textarea' ? 'textarea' : tag === 'select' ? 'select' : 'text');
                if (['hidden', 'submit', 'button'].includes(type)) return;

                // Find label
                let label = '';
                const id = el.id;
                if (id) {
                    const labelEl = form.querySelector(`label[for="${id}"]`);
                    if (labelEl) label = labelEl.innerText?.trim() || '';
                }
                if (!label) {
                    const parent = el.closest('label');
                    if (parent) label = parent.innerText?.trim() || '';
                }
                if (!label) label = el.getAttribute('aria-label') || el.placeholder || el.name || '';

                const options = [];
                if (tag === 'select') {
                    el.querySelectorAll('option').forEach(opt => {
                        if (opt.value) options.push(opt.innerText?.trim() || opt.value);
                    });
                }

                fields.push({
                    label: label.slice(0, 100),
                    field_type: type,
                    name: el.name || '',
                    placeholder: el.placeholder || '',
                    required: el.required || false,
                    options
                });
            });

            // Find submit button text
            let submitText = 'Submit';
            const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
            if (submitBtn) {
                submitText = submitBtn.innerText?.trim() || submitBtn.value || 'Submit';
            }

            forms.push({
                action: form.action || '',
                method: (form.method || 'GET').toUpperCase(),
                fields,
                submit_text: submitText
            });
        });
        return forms;
    }""")
    return [
        DetectedForm(
            action=f["action"],
            method=f["method"],
            fields=[FormField(**ff) for ff in f["fields"]],
            submit_text=f["submit_text"],
        )
        for f in raw
    ]


async def fill_form(
    page: Page,
    field_values: dict[str, str],
    *,
    submit: bool = False,
    retry: RetryConfig,
    stealth: StealthConfig,
) -> None:
    """Fill form fields by label name.

    Args:
        page: The Playwright page.
        field_values: Mapping of label text to value (e.g., {"Email": "user@example.com"}).
        submit: Whether to submit the form after filling.
        retry: Retry configuration.
        stealth: Stealth configuration.
    """
    for label, value in field_values.items():
        el = await find_element(page, label, retry)
        tag = el.tag

        if tag == "select":
            await el.locator.select_option(label=value)
        elif tag in ("input", "textarea"):
            input_type = await el.locator.get_attribute("type") or "text"
            if input_type == "checkbox":
                checked = await el.locator.is_checked()
                should_check = value.lower() in ("true", "yes", "1", "on")
                if checked != should_check:
                    await el.locator.click()
            elif input_type == "radio":
                await el.locator.click()
            else:
                await el.locator.clear()
                if stealth.realistic_typing:
                    await el.locator.press_sequentially(value, delay=stealth.typing_delay_min_ms)
                else:
                    await el.locator.fill(value)
        else:
            await el.locator.fill(value)

        await random_delay(stealth)

    if submit:
        # Try to find and click a submit button
        forms = await detect_forms(page)
        if forms:
            try:
                el = await find_element(page, forms[0].submit_text, retry)
                await el.locator.click()
            except Exception:
                await page.keyboard.press("Enter")
        else:
            await page.keyboard.press("Enter")
