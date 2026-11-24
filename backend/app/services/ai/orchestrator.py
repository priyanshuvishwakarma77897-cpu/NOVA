
from backend.app.core.config import settings
from backend.app.services.ai.provider import generate_response
from backend.app.services.ai.usage_manager import (

    reserve_quota,
    complete_reservation,
    mark_reservation_uncertain,
)


class AIOrchestrationError(Exception):
    """Raised when the AI request pipeline fails."""


def estimate_input_tokens(prompt: str) -> int:
    """
    Conservative upper-bound estimate for UTF-8 prompt bytes.

    This intentionally overestimates typical token usage.
    It is not an exact provider tokenizer.
    """

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    return max(1, len(prompt.encode("utf-8")) + 16)


async def generate_ai_response(prompt: str) -> dict:
    """
    Execute a protected AI request.

    Flow:
    1. Validate the prompt.
    2. Estimate input tokens.
    3. Reserve quota.
    4. Call the configured provider.
    5. Reconcile actual usage.
    """

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    provider = settings.AI_PROVIDER.lower().strip()

    if provider != "groq":
        raise ValueError(
            f"Quota protection is not configured for: {provider}"
        )

    model = settings.GROQ_MODEL

    estimated_input_tokens = estimate_input_tokens(prompt)
    reserved_output_tokens = settings.AI_MAX_OUTPUT_TOKENS

    # Reserve quota before contacting the provider.
    reservation_id = reserve_quota(
        provider=provider,
        model=model,
        estimated_input_tokens=estimated_input_tokens,
        reserved_output_tokens=reserved_output_tokens,
    )

    try:
        result = await generate_response(prompt)

    except Exception as exc:
        # The provider may have processed the request.
        # Preserve the reservation rather than releasing quota.
        try:
            mark_reservation_uncertain(reservation_id)
        except Exception as reservation_error:
            raise AIOrchestrationError(
                "AI request failed and reservation status "
                "could not be updated. Manual inspection required."
            ) from reservation_error

        raise AIOrchestrationError(
            "AI provider request failed. "
            "The quota reservation has been retained."
        ) from exc

    try:
        content = result["content"]
        input_tokens = result["input_tokens"]
        output_tokens = result["output_tokens"]

        if not isinstance(content, str) or not content:
            raise ValueError("Provider returned invalid content.")

        if (
            not isinstance(input_tokens, int)
            or isinstance(input_tokens, bool)
            or input_tokens < 0
        ):
            raise ValueError("Provider returned invalid input token usage.")

        if (
            not isinstance(output_tokens, int)
            or isinstance(output_tokens, bool)
            or output_tokens < 0
        ):
            raise ValueError("Provider returned invalid output token usage.")

        complete_reservation(
            reservation_id=reservation_id,
            actual_input_tokens=input_tokens,
            actual_output_tokens=output_tokens,
        )

    except Exception as exc:
        raise AIOrchestrationError(
            "AI response received, but usage reconciliation failed. "
            "The response has not been returned. "
            "The reservation must be inspected before further processing."
        ) from exc

    return {
        "content": content,
        "provider": provider,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
    }
