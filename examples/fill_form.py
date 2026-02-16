"""Example: Fill out a form on a demo site."""

import asyncio
from agentbrowser import BrowserAgent


async def main():
    async with BrowserAgent(headless=True) as agent:
        # Navigate to a form demo page
        await agent.goto("https://httpbin.org/forms/post")

        # Detect forms on the page
        forms = await agent.detect_forms()
        for form in forms:
            print(f"Form: {form.action} ({form.method})")
            for field in form.fields:
                print(f"  - {field.label} [{field.field_type}]")

        # Fill the form by label
        await agent.fill_form({
            "Customer name": "Ander Turing",
            "Telephone": "555-0123",
            "E-mail address": "ander@example.com",
            "Size": "Medium",  # select dropdown
            "Comments": "Testing agentbrowser! 🤖",
        })

        # Take a screenshot of the filled form
        await agent.screenshot("filled_form.png")
        print("Form filled! Screenshot saved to filled_form.png")


if __name__ == "__main__":
    asyncio.run(main())
