"""Tests for form detection and filling."""

import pytest
from agentbrowser import BrowserAgent


@pytest.mark.asyncio
async def test_detect_forms():
    """Test form detection on httpbin."""
    async with BrowserAgent(headless=True) as agent:
        await agent.goto("https://httpbin.org/forms/post")
        forms = await agent.detect_forms()
        assert len(forms) >= 1
        form = forms[0]
        assert len(form.fields) > 0
        field_labels = [f.label for f in form.fields]
        # httpbin form has customer name, telephone, email, etc.
        assert any("customer" in l.lower() or "name" in l.lower() for l in field_labels)
