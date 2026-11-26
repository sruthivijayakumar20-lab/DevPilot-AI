
import asyncio
from unittest.mock import patch

from google.adk.models import Gemini
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

from app.config.model_config import MODEL_NAME


class Simulated503(Exception):
    status_code = 503


async def fake_generate(self, llm_request, stream=False):
    calls.append(self.model)

    if self.model == MODEL_NAME.fallback_models[0].model:
        raise Simulated503("503 Service Unavailable")

    yield LlmResponse(
        content=types.Content(
            role="model",
            parts=[types.Part(text="Secondary model succeeded")],
        ),
        partial=False,
    )


calls = []


async def main():
    calls.clear()

    request = LlmRequest(
        contents=[
            types.Content(
                role="user",
                parts=[types.Part(text="Test fallback")],
            )
        ]
    )

    with patch.object(
        Gemini,
        "generate_content_async",
        fake_generate,
    ):
        responses = []

        async for response in MODEL_NAME.generate_content_async(
            request,
            stream=False,
        ):
            responses.append(response)

    assert len(responses) == 1

    assert (
        responses[0].content.parts[0].text
        == "Secondary model succeeded"
    )

    assert calls == [
        MODEL_NAME.fallback_models[0].model,
        MODEL_NAME.fallback_models[1].model,
    ]

    print("\nPASS: Primary model returned simulated 503")
    print("PASS: Secondary model was attempted")
    print("PASS: Secondary model returned successfully")
    print("PASS: Tertiary model was not called")
    print("PASS: Fallback response received correctly")


if __name__ == "__main__":
    asyncio.run(main())
