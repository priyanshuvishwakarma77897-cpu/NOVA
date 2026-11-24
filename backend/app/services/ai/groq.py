
from groq import AsyncGroq

from backend.app.core.config import settings


async def generate_response(prompt: str) -> dict:
    """Generate a Groq response and return actual token usage."""

    if not settings.GROQ_API_KEY:
        raise RuntimeError("Groq API key is not configured.")

    async with AsyncGroq(
        api_key=settings.GROQ_API_KEY,
        max_retries=0,
    ) as client:
        response = await client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            max_completion_tokens=settings.AI_MAX_OUTPUT_TOKENS,
        )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("Groq returned an empty response.")

    if response.usage is None:
        raise RuntimeError("Groq did not return token usage information.")

    return {
        "content": content,
        "input_tokens": response.usage.prompt_tokens,
        "output_tokens": response.usage.completion_tokens,
    }
