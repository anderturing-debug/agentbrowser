"""Tests for the BrowserAgent core functionality."""

import pytest
from agentbrowser import BrowserAgent, BrowserNotStartedError


@pytest.mark.asyncio
async def test_agent_context_manager():
    """Test that BrowserAgent works as an async context manager."""
    async with BrowserAgent(headless=True) as agent:
        assert agent.url == "about:blank"


@pytest.mark.asyncio
async def test_agent_not_started():
    """Test that using agent before start raises error."""
    agent = BrowserAgent()
    with pytest.raises(BrowserNotStartedError):
        _ = agent.page


@pytest.mark.asyncio
async def test_goto_and_url():
    """Test navigation and URL tracking."""
    async with BrowserAgent(headless=True) as agent:
        await agent.goto("https://example.com")
        assert "example.com" in agent.url


@pytest.mark.asyncio
async def test_get_text():
    """Test text extraction from a page."""
    async with BrowserAgent(headless=True) as agent:
        await agent.goto("https://example.com")
        text = await agent.get_text()
        assert "Example Domain" in text


@pytest.mark.asyncio
async def test_get_links():
    """Test link extraction."""
    async with BrowserAgent(headless=True) as agent:
        await agent.goto("https://example.com")
        links = await agent.get_links()
        assert len(links) > 0
        assert any("iana" in l.href.lower() for l in links)


@pytest.mark.asyncio
async def test_page_summary():
    """Test LLM-friendly page summary."""
    async with BrowserAgent(headless=True) as agent:
        await agent.goto("https://example.com")
        summary = await agent.page_summary()
        assert "example.com" in summary.lower()
        assert "VISIBLE ELEMENTS:" in summary


@pytest.mark.asyncio
async def test_screenshot_base64():
    """Test screenshot returns base64."""
    async with BrowserAgent(headless=True) as agent:
        await agent.goto("https://example.com")
        b64 = await agent.screenshot()
        assert len(b64) > 100  # Should be a real image


@pytest.mark.asyncio
async def test_screenshot_to_file(tmp_path):
    """Test saving screenshot to file."""
    async with BrowserAgent(headless=True) as agent:
        await agent.goto("https://example.com")
        path = tmp_path / "test.png"
        await agent.screenshot(str(path))
        assert path.exists()
        assert path.stat().st_size > 100


@pytest.mark.asyncio
async def test_click_element():
    """Test clicking an element by text."""
    async with BrowserAgent(headless=True) as agent:
        await agent.goto("https://example.com")
        await agent.click("More information")
        # Should navigate to IANA
        assert "iana" in agent.url.lower()


@pytest.mark.asyncio
async def test_scroll():
    """Test scrolling."""
    async with BrowserAgent(headless=True) as agent:
        await agent.goto("https://example.com")
        await agent.scroll_down(300)
        await agent.scroll_up(100)
        # No error means success


@pytest.mark.asyncio
async def test_get_meta():
    """Test metadata extraction."""
    async with BrowserAgent(headless=True) as agent:
        await agent.goto("https://example.com")
        meta = await agent.get_meta()
        assert "title" in meta
        assert "url" in meta
