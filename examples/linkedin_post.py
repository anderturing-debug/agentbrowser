"""Example: Post to LinkedIn using a saved profile.

⚠️  Requires a saved 'linkedin' profile with valid session cookies.
Run login flow first and save with: await agent.save_profile("linkedin")
"""

import asyncio
from agentbrowser import BrowserAgent


async def main():
    async with BrowserAgent(
        headless=False,  # Watch it work
        profile="linkedin",
        stealth=True,  # Anti-detection is critical for LinkedIn
    ) as agent:
        await agent.goto("https://www.linkedin.com/feed/")

        # Wait for feed to load
        await agent.wait_for("Start a post")

        # Get a summary of the page
        summary = await agent.page_summary()
        print(summary)

        # Click "Start a post"
        await agent.click("Start a post")
        await agent.wait(1500)  # Wait for modal

        # Type the post content
        # Note: LinkedIn's editor is complex, this is illustrative
        await agent.press("Tab")
        await agent.page.keyboard.type(
            "Just shipped agentbrowser — an open source tool that gives "
            "AI agents a real browser. 🤖\n\n"
            "Smart element finding, stealth mode, LLM-friendly page summaries.\n\n"
            "Check it out: github.com/anderturing-debug/agentbrowser\n\n"
            "#AI #OpenSource #Automation"
        )

        # Screenshot before posting
        await agent.screenshot("linkedin_draft.png")
        print("Draft screenshot saved. Review before posting!")

        # Uncomment to actually post:
        # await agent.click("Post")
        # print("Posted! 🎉")


if __name__ == "__main__":
    asyncio.run(main())
