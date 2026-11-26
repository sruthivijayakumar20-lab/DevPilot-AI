
import asyncio

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.orchestrator.development_workflow import development_workflow

import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / "app" / ".env"

load_dotenv(ENV_PATH, override=True)

if not os.getenv("GROQ_API_KEY"):
    raise ValueError("GROQ_API_KEY was not loaded")


APP_NAME = "development_workflow_test"
USER_ID = "local_user"


async def main():

    session_service = InMemorySessionService()

    runner = Runner(
        agent=development_workflow,
        app_name=APP_NAME,
        session_service=session_service,
    )

    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
    )

    message = types.Content(
        role="user",
        parts=[
            types.Part.from_text(
                text=(
                    "Analyze the repository and prepare "
                    "a plan to implement JWT authentication."
                )
            )
        ],
    )

    try:
        async for event in runner.run_async(
            user_id=USER_ID,
            session_id=session.id,
            new_message=message,
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"\n{event.author}:")
                        print(part.text)

        # Verify repository summary was saved.
        final_session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=session.id,
        )

        print("\nRepository summary saved:",
              "repository_summary" in final_session.state)

    finally:
        await runner.close()


if __name__ == "__main__":
    asyncio.run(main())
