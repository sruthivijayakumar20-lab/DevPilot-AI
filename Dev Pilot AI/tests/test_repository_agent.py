
import asyncio
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = PROJECT_ROOT / "app" / ".env"
load_dotenv(ENV_PATH, override=True)

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from app.orchestrator.development_workflow import development_workflow


async def main():
    app_name = "repository_agent_test"
    user_id = "test_user"

    session_service = InMemorySessionService()

    runner = Runner(
            agent=development_workflow,
            app_name=app_name,
            session_service=session_service,)

    session = await session_service.create_session(
        app_name=app_name,
        user_id=user_id
    )

    message = types.Content(
        role="user",
        parts=[
            types.Part.from_text(
                text="Analyze the Financial Agent repository. "
                     "Identify its languages, frameworks, entry points, "
                     "important configuration files and architecture."
            )
        ]
    )

    try:
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session.id,
            new_message=message
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        print(f"\n{event.author}:")
                        print(part.text)

    finally:
        await runner.close()


if __name__ == "__main__":
    asyncio.run(main())
