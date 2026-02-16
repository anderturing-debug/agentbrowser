# 🤖 agentbrowser

**Give your AI agents a real browser.**

Playwright-based, stealth-mode, with smart element finding and LLM-friendly page summaries. Built for AI agents that need to actually browse the web — not just fetch HTML.

[![CI](https://github.com/anderturing-debug/agentbrowser/actions/workflows/ci.yml/badge.svg)](https://github.com/anderturing-debug/agentbrowser/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## Why?

AI agents need to interact with the web. Current options suck:

| Approach | Problem |
|---|---|
| Raw Playwright/Selenium | Too low-level — agents can't reason about CSS selectors |
| Cloud browser APIs | $0.01/action adds up fast, vendor lock-in |
| HTTP fetching (requests/httpx) | Misses JS-rendered content, can't interact |
| **agentbrowser** | ✅ High-level API, stealth mode, LLM-friendly output |

agentbrowser lets agents think in terms of **"click the Sign In button"** instead of `page.locator('button.btn-primary.auth-submit').click()`.

## Quick Start

```bash
pip install agentbrowser
playwright install chromium
```

```python
import asyncio
from agentbrowser import BrowserAgent

async def main():
    async with BrowserAgent() as agent:
        await agent.goto("https://news.ycombinator.com")
        summary = await agent.page_summary()  # LLM-friendly!
        print(summary)

asyncio.run(main())
```

**5 lines.** That's it. Your agent now has a browser.

## Features

### 🔍 Smart Element Finding

Find elements the way humans describe them — by text, not selectors:

```python
# These all work — fuzzy matching, case-insensitive
await agent.click("Sign in")        # finds button with text "Sign in", "SIGN IN", "Sign In"
await agent.click("Submit")         # button by text
await agent.type("Email", "me@x.com")  # finds input by its label
await agent.type("Search", "AI")    # finds by placeholder text
await agent.click("#custom-id")     # CSS selectors work too
```

When an element isn't found, you get **helpful errors**:
```
ElementNotFoundError: Element 'Submit' not found.
Available: [button] "Cancel", [button] "Save Draft", [button] "Post"
```

### 🤖 LLM-Friendly Page Summary

The killer feature. `page_summary()` returns structured text that AI agents can reason about:

```
URL: https://linkedin.com/feed
Title: LinkedIn Feed

VISIBLE ELEMENTS:
- [button] "Start a post"
- [textbox] "Search" (placeholder: "Search")
- [link] "Home" (active)
- [link] "My Network"
- [link] "Jobs"
- [link] "Messaging (3)"

FORMS: None visible

NAVIGATION: Home | My Network | Jobs | Messaging | Notifications

PAGE CONTENT (preview):
  Welcome back, Ander!
  Here's what's trending in your network...
```

### 🕵️ Stealth Mode

Built-in anti-detection that actually works on LinkedIn, Twitter, etc:

- `playwright-stealth` patches
- Random delays between actions (human-like timing)
- Realistic typing with per-keystroke delays
- Mouse jitter on movements
- Proper user agent rotation
- Realistic viewport sizes

```python
# Stealth is ON by default
async with BrowserAgent(stealth=True) as agent:  # default
    await agent.goto("https://linkedin.com")
    # Won't get detected as a bot
```

### 👤 Browser Profiles

Save and reuse login sessions across runs:

```python
# Login once
async with BrowserAgent() as agent:
    await agent.goto("https://github.com/login")
    await agent.type("Username or email address", "myuser")
    await agent.type("Password", "mypass")
    await agent.click("Sign in")
    await agent.save_profile("github")  # saves cookies + localStorage

# Reuse later — already logged in!
async with BrowserAgent(profile="github") as agent:
    await agent.goto("https://github.com")
    # No login needed!
```

### 📝 Form Filling

Detect forms and fill them by label:

```python
# Auto-detect forms on the page
forms = await agent.detect_forms()
for form in forms:
    print(f"{form.method} {form.action}")
    for field in form.fields:
        print(f"  {field.label} [{field.field_type}]")

# Fill by label name
await agent.fill_form({
    "First Name": "Ander",
    "Email": "ander@example.com",
    "Country": "United States",  # works for dropdowns too
}, submit=True)
```

### 🎬 Record & Replay

Record action sequences and replay them:

```python
async with BrowserAgent() as agent:
    agent.start_recording()

    await agent.goto("https://example.com")
    await agent.click("Login")
    await agent.type("Email", "user@example.com")

    agent.stop_recording()
    agent.save_recording("login-flow")

# Later:
async with BrowserAgent() as agent:
    await agent.replay("login-flow")
```

### 📸 Screenshots

Full page, viewport, or element screenshots:

```python
# Returns base64 (great for sending to vision LLMs)
b64 = await agent.screenshot()

# Save to file
await agent.screenshot("page.png")

# Full scrollable page
await agent.screenshot("full.png", full_page=True)

# Specific element
await agent.screenshot("hero.png", element="main heading")
```

## CLI

```bash
# Navigate and get summary
agentbrowser goto "https://example.com"

# Interact
agentbrowser click "Submit"
agentbrowser type "Search" "AI agents"

# Extract content
agentbrowser extract --format text
agentbrowser extract --format json
agentbrowser extract --format links
agentbrowser summary

# Screenshots
agentbrowser screenshot output.png
agentbrowser screenshot --full-page page.png

# Profiles
agentbrowser profile list
agentbrowser profile create github --url https://github.com
agentbrowser profile delete old-profile

# Record & Replay
agentbrowser replay login-flow --headed
```

## Full API Reference

### `BrowserAgent`

```python
BrowserAgent(
    headless=True,          # Run without visible window
    profile=None,           # Load saved profile
    browser_type="chromium", # chromium/firefox/webkit
    stealth=True,           # Anti-detection
    timeout_ms=30000,       # Default timeout
    viewport=(1920, 1080),  # Browser viewport size
    data_dir=None,          # Custom data directory
)
```

### Navigation

| Method | Description |
|---|---|
| `await agent.goto(url)` | Navigate to URL |
| `await agent.back()` | Go back |
| `await agent.forward()` | Go forward |
| `await agent.refresh()` | Refresh page |
| `agent.url` | Current URL (property) |
| `await agent.get_title()` | Page title |

### Interaction

| Method | Description |
|---|---|
| `await agent.click(query)` | Click element by text/selector |
| `await agent.type(query, text)` | Type into input by label/placeholder |
| `await agent.hover(query)` | Hover over element |
| `await agent.select(query, value)` | Select dropdown option |
| `await agent.press(key)` | Press keyboard key |
| `await agent.scroll_down(px)` | Scroll down |
| `await agent.scroll_up(px)` | Scroll up |
| `await agent.scroll_to(query)` | Scroll to element |

### Extraction

| Method | Description |
|---|---|
| `await agent.page_summary()` | LLM-friendly page state |
| `await agent.get_text()` | All visible text |
| `await agent.get_links()` | All links with text/href |
| `await agent.get_tables()` | All tables as structured data |
| `await agent.get_meta()` | Page metadata (title, description, etc.) |
| `await agent.screenshot(path)` | Screenshot (returns base64) |

### Forms

| Method | Description |
|---|---|
| `await agent.fill_form(fields)` | Fill form by label mapping |
| `await agent.detect_forms()` | List all forms and their fields |

### Waiting

| Method | Description |
|---|---|
| `await agent.wait_for(text)` | Wait for text to appear |
| `await agent.wait(ms)` | Wait fixed duration |

### Profiles & Recording

| Method | Description |
|---|---|
| `await agent.save_profile(name)` | Save cookies + storage |
| `await agent.load_profile(name)` | Load saved profile |
| `agent.list_profiles()` | List all profiles |
| `agent.start_recording()` | Start recording actions |
| `agent.stop_recording()` | Stop and get actions |
| `agent.save_recording(name)` | Save recording |
| `await agent.replay(name)` | Replay saved recording |

## Architecture

```
agentbrowser/
├── agent.py         # BrowserAgent — the main API that ties everything together
├── browser.py       # Playwright lifecycle (launch, context, page management)
├── elements.py      # Smart element finding (fuzzy text, ARIA roles, labels)
├── actions.py       # Click, type, select, scroll with retries + stealth delays
├── extraction.py    # Get text, links, tables, metadata from pages
├── forms.py         # Form detection and filling by label
├── page_state.py    # LLM-friendly page summarization
├── screenshot.py    # Screenshot capture (full page, element, viewport)
├── stealth.py       # Anti-detection (delays, typing, mouse jitter, UA rotation)
├── profiles.py      # Browser profile management (cookies, localStorage)
├── recorder.py      # Action recording and replay
├── storage.py       # SQLite persistence for profiles and recordings
├── config.py        # Pydantic configuration models
├── exceptions.py    # Custom exception hierarchy
└── cli.py           # Click-based CLI with Rich output
```

### Design Philosophy: For Agents, Not For Testing

Traditional browser automation (Selenium, Playwright) is built for **testing** — you know the page structure, you write specific selectors, you assert expected states.

agentbrowser is built for **agents** — the agent doesn't know the page structure ahead of time. It needs to:

1. **Understand** what's on the page (`page_summary()`)
2. **Find** elements by how humans describe them ("the login button")
3. **Act** with realistic human-like behavior (stealth)
4. **Recover** from errors with helpful feedback
5. **Remember** sessions across runs (profiles)

## Examples

See the [`examples/`](examples/) directory:

- **[scrape_hn.py](examples/scrape_hn.py)** — Scrape Hacker News front page
- **[fill_form.py](examples/fill_form.py)** — Detect and fill forms
- **[login_github.py](examples/login_github.py)** — Login to GitHub, save session
- **[linkedin_post.py](examples/linkedin_post.py)** — Post to LinkedIn with stealth mode

## Development

```bash
git clone https://github.com/anderturing-debug/agentbrowser.git
cd agentbrowser
pip install -e ".[dev]"
playwright install chromium --with-deps
pytest tests/ -v
```

## License

MIT — do whatever you want with it.

---

Built by [Ander Turing](https://github.com/anderturing-debug) 🤖
