import asyncio
from agentbrowser import BrowserAgent

async def main():
    async with BrowserAgent(headless=True) as agent:
        await agent.goto("https://example.com")
        text = await agent.get_text()
        print(f"Page text length: {len(text)}")
        print(f"First 200 chars: {text[:200]}")
        
        links = await agent.get_links()
        print(f"Links found: {len(links)}")
        
        summary = await agent.page_summary()
        print(f"Page summary:\n{summary}")
        
        await agent.screenshot("test_screenshot.png")
        print("Screenshot saved!")

asyncio.run(main())
