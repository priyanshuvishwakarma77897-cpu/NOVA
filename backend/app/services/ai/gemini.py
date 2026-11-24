
from google import genai

from backend.app.core.config import settings


async def generate_response(prompt: str) -> dict:
    """Generate a Gemini response with actual token usage."""

    if not settings.GEMINI_API_KEY:
        raise RuntimeError("Gemini API key is not configured.")

    client = genai.Client(
        api_key=settings.GEMINI_API_KEY
    ).aio

    try:
        response = await client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )

        if not response.text:
            raise RuntimeError("Gemini returned an empty response.")

        usage = response.usage_metadata

        if usage is None:
            raise RuntimeError("Gemini did not return token usage.")

        if (
            usage.prompt_token_count is None
            or usage.candidates_token_count is None
        ):
            raise RuntimeError("Gemini returned incomplete token usage.")

        return {
            "content": response.text,
            "input_tokens": usage.prompt_token_count,
            "output_tokens": usage.candidates_token_count,
        }

    finally:
        await client.aclose()
