# Basic browser automation smoke test using browser-use AI agent
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables from project root
load_dotenv(dotenv_path="../../.env")

# browser-use has its own LLM wrappers
from browser_use.agent.service import Agent
from browser_use.browser.profile import BrowserProfile
from browser_use.browser.session import BrowserSession
from browser_use.llm.openai.chat import ChatOpenAI

async def run():
    """Run a simple browser automation task with AI agent."""
    
    # Initialize the LLM using browser-use's ChatOpenAI
    # Requires OPENAI_API_KEY environment variable
    llm = ChatOpenAI(
        model="gpt-4o",  # Fast and capable model
    )
    
    # Configure browser profile for better stability
    browser_profile = BrowserProfile(
        headless=False,  # Set to True for headless mode
        disable_security=True,
        extra_chromium_args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
        ],
    )
    
    # Create browser session
    browser_session = BrowserSession(browser_profile=browser_profile)
    
    # Create an agent with a simple task
    agent = Agent(
        task="Go to https://www.google.com and tell me the page title",
        llm=llm,
        browser_session=browser_session,
    )
    
    # Run the agent with max 5 steps
    print("Starting browser agent...")
    result = await agent.run(max_steps=5)
    print("\n=== Agent Result ===")
    print(result)

if __name__ == '__main__':
    asyncio.run(run())
