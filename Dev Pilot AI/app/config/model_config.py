
import os
import copy
from pathlib import Path
from typing import AsyncGenerator

from dotenv import load_dotenv
from google.adk.models import Gemini
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse

try:
    from httpx import TransportError
    NETWORK_ERRORS = (
        TimeoutError,
        ConnectionError,
        OSError,
        TransportError,
    )
except ImportError:
    NETWORK_ERRORS = (
        TimeoutError,
        ConnectionError,
        OSError,
    )


# Load app/.env
ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(ENV_PATH)

if not os.getenv("GOOGLE_API_KEY"):
    raise EnvironmentError(
        "GOOGLE_API_KEY is missing from app/.env"
    )


# Model priority
PRIMARY_MODEL = os.getenv(
    "GEMINI_PRIMARY_MODEL",
    "gemini-3.6-flash"
)

SECONDARY_MODEL = os.getenv(
    "GEMINI_SECONDARY_MODEL",
    "gemini-3-flash-preview"
)

TERTIARY_MODEL = os.getenv(
    "GEMINI_TERTIARY_MODEL",
    "gemini-2.5-flash-lite"
)


def is_retryable_error(exc: Exception) -> bool:
    """Identify temporary provider/network failures."""

    status = getattr(exc, "status_code", None)

    if status is None:
        status = getattr(exc, "code", None)

    try:
        status = int(status)
    except (TypeError, ValueError):
        status = None

    return (
        status in {429, 500, 502, 503, 504}
        or isinstance(exc, NETWORK_ERRORS)
    )


class GeminiFallbackModel(BaseLlm):
    """Try Gemini models in configured priority order."""

    fallback_models: list[Gemini]

    @property
    def capabilities(self):
        return self.fallback_models[0].capabilities

    async def generate_content_async(
        self,
        llm_request: LlmRequest,
        stream: bool = False,
    ) -> AsyncGenerator[LlmResponse, None]:

        last_error = None

        for index, model in enumerate(self.fallback_models):

            responses = []

            try:
                # Give every model an independent copy
                request_copy = copy.deepcopy(llm_request)
                # Set the model for the current fallback attempt
                request_copy.model = model.model

                async for response in model.generate_content_async(
                    request_copy,
                    stream=stream,
                ):
                    responses.append(response)

                if not responses:
                    raise RuntimeError(
                        f"{model.model} returned no response."
                    )

                print(
                    f"Model selected successfully: {model.model}"
                )

            except Exception as exc:

                if not is_retryable_error(exc):
                    raise

                last_error = exc

                print(
                    f"Temporary failure from {model.model}: {exc}"
                )

                if index < len(self.fallback_models) - 1:
                    print("Trying the next configured model...")
                    continue

                break

            # Yield only after the complete response succeeds
            for response in responses:
                yield response

            return

        if last_error:
            raise last_error


# Build the model candidates
MODEL_CANDIDATES = [
    Gemini(model=PRIMARY_MODEL),
    Gemini(model=SECONDARY_MODEL),
    Gemini(model=TERTIARY_MODEL),
]


# Keep the existing variable name used by all six agents.
# MODEL_NAME is now a BaseLlm instance, not a string.
MODEL_NAME = GeminiFallbackModel(
    model=PRIMARY_MODEL,
    fallback_models=MODEL_CANDIDATES,
)
