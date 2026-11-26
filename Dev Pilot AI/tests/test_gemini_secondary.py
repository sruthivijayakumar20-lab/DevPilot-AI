
import asyncio

from google.adk.models import Gemini
from google.adk.models.llm_request import LlmRequest
from app.config.model_config import SECONDARY_MODEL


async def main():
    model = Gemini(model=SECONDARY_MODEL)

    request = LlmRequest(
        model=SECONDARY_MODEL,
        contents=[
            {
                "role": "user",
                "parts": [{"text": "What is Python? Answer briefly."}]
            }
        ]
    )

    print("Testing model:", SECONDARY_MODEL)

    async for response in model.generate_content_async(
        request,
        stream=False,
    ):
        if response.content and response.content.parts:
            for part in response.content.parts:
                if part.text:
                    print("Response:", part.text)

    print("\nSecondary model API test completed.")


if __name__ == "__main__":
    asyncio.run(main())
