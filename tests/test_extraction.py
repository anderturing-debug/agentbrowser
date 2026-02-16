"""Tests for page content extraction."""

import pytest
from agentbrowser import BrowserAgent


@pytest.mark.asyncio
async def test_get_visible_text():
    """Test visible text extraction."""
    async with BrowserAgent(headless=True) as agent:
        await agent.goto("https://example.com")
        text = await agent.get_text()
        assert "Example Domain" in text
        assert len(text) > 20


@pytest.mark.asyncio
async def test_get_links_structure():
    """Test that links have correct structure."""
    async with BrowserAgent(headless=True) as agent:
        await agent.goto("https://example.com")
        links = await agent.get_links()
        for link in links:
            assert hasattr(link, "text")
            assert hasattr(link, "href")
            assert hasattr(link, "is_external")
            assert link.href.startswith("http")
