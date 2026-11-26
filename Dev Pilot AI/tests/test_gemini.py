import asyncio
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types
from app.config.model_config import MODEL_NAME


async def main():
    test_agent = Agent(
        name="gemini_test_agent",
        model=MODEL_NAME,
        instruction="Answer the user's question in one short sentence."
    )

    runner = InMemoryRunner(agent=test_agent)

    response = await runner.run_debug(
        "What is Python? Answer briefly."
    )

    print("\nGemini response:")
    print(response)


if __name__ == "__main__":
    asyncio.run(main())
