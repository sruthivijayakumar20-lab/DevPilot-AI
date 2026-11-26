
import asyncio
from unittest.mock import patch

from google.adk.models import Gemini
from google.adk.models.llm_request import LlmRequest
from google.genai import types

from app.config.model_config import MODEL_NAME


class Simulated503(Exception):
    status_code = 503


original_generate = Gemini.generate_content_async


async def patched_generate(self, llm_request, stream=False):
    if self.model == MODEL_NAME.fallback_models[0].model:
        print(f"\nSimulating 503 from: {self.model}")
        raise Simulated503("503 Service Unavailable")

    print(f"\nMaking real API request using: {self.model}")

    async for response in original_generate(
        self,
        llm_request,
        stream=stream,
    ):
        yield response


async def main():
    request = LlmRequest(
        model=MODEL_NAME.model,
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part(
                        text="Explain Python in two sentences."
                    )
                ],
            )
        ],
    )

    with patch.object(
        Gemini,
        "generate_content_async",
        patched_generate,
    ):
        async for response in MODEL_NAME.generate_content_async(
            request,
            stream=False,
        ):
            if response.content:
                for part in response.content.parts:
                    if part.text:
                        print("\nFinal response:", part.text)


if __name__ == "__main__":
    asyncio.run(main())
