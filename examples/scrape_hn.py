"""Example: Scrape Hacker News front page."""

import asyncio
from agentbrowser import BrowserAgent


async def main():
    async with BrowserAgent(headless=True) as agent:
        await agent.goto("https://news.ycombinator.com")

        # Get page summary
        summary = await agent.page_summary()
        print(summary)
        print("\n" + "=" * 60 + "\n")

        # Extract all links
        links = await agent.get_links()
        print("TOP STORIES:")
        story_links = [l for l in links if l.is_external and len(l.text) > 10]
        for i, link in enumerate(story_links[:30], 1):
            print(f"  {i}. {link.text}")
            print(f"     {link.href}")
        print(f"\nTotal external links: {len(story_links)}")

        # Get all visible text
        text = await agent.get_text()
        print(f"\nPage text length: {len(text)} chars")

        # Take a screenshot
        await agent.screenshot("hn_front_page.png", full_page=True)
        print("\nScreenshot saved to hn_front_page.png")


if __name__ == "__main__":
    asyncio.run(main())
