"""Tests for smart element finding."""

import pytest
from agentbrowser import BrowserAgent, ElementNotFoundError


@pytest.mark.asyncio
async def test_find_by_text():
    """Test finding elements by text content."""
    async with BrowserAgent(headless=True) as agent:
        await agent.goto("https://example.com")
        # "More information..." link should be findable
        await agent.click("More information")
        assert "iana" in agent.url.lower()


@pytest.mark.asyncio
async def test_element_not_found_error():
    """Test that ElementNotFoundError includes helpful info."""
    async with BrowserAgent(headless=True) as agent:
        await agent.goto("https://example.com")
        with pytest.raises(ElementNotFoundError) as exc_info:
            await agent.click("Nonexistent Button XYZ")
        assert "Nonexistent Button XYZ" in str(exc_info.value)
