"""Example: Log into GitHub and save the session profile.

⚠️  Replace with your actual credentials or use environment variables.
"""

import asyncio
import os
from agentbrowser import BrowserAgent


async def main():
    username = os.environ.get("GITHUB_USER", "your-username")
    password = os.environ.get("GITHUB_PASS", "your-password")

    async with BrowserAgent(headless=False, stealth=True) as agent:
        await agent.goto("https://github.com/login")

        # Fill login form
        await agent.type("Username or email address", username)
        await agent.type("Password", password)
        await agent.click("Sign in")

        # Wait for dashboard to load
        await agent.wait_for("Dashboard")

        # Save session for reuse
        await agent.save_profile("github")
        print("✅ Logged in and profile saved!")

        # Get page summary
        summary = await agent.page_summary()
        print(summary)

    # Later: reuse the saved profile
    async with BrowserAgent(profile="github") as agent:
        await agent.goto("https://github.com")
        print(f"Loaded profile — URL: {agent.url}")
        # Should be logged in already!


if __name__ == "__main__":
    asyncio.run(main())
