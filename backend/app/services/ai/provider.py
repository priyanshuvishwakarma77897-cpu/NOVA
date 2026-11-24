
from backend.app.core.config import settings

from backend.app.services.ai.gemini import (
    generate_response as generate_gemini_response,
)

from backend.app.services.ai.groq import (
    generate_response as generate_groq_response,
)


async def generate_response(prompt: str) -> dict:
    """Generate an AI response using the configured provider."""

    provider = settings.AI_PROVIDER.lower()

    if provider == "groq":
        return await generate_groq_response(prompt)

    if provider == "gemini":
        return await generate_gemini_response(prompt)

    raise ValueError(f"Unsupported AI provider: {provider}")
