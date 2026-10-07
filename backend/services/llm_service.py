"""Provider wrapper for the language-model calls used by the project.

The rest of the application calls this module instead of talking directly to
a provider. Temporary provider failures are retried here so a short outage
does not immediately break a research run.
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable

from backend.utils.config import settings
from backend.utils.logger import get_logger

logger = get_logger(__name__)

MAX_ATTEMPTS = 3
RETRY_DELAYS = (1, 2)


class LLMConfigurationError(RuntimeError):
    """Raised when the selected provider is not configured correctly."""


def _require_provider() -> str:
    provider = settings.LLM_PROVIDER
    if provider not in {"gemini", "openai"}:
        raise LLMConfigurationError(
            f"Unsupported LLM_PROVIDER={provider!r}. Use 'gemini' or 'openai'."
        )
    return provider


def generate_answer(prompt: str) -> str:
    """Generate plain text from the configured provider."""
    provider = _require_provider()
    if provider == "openai":
        return _generate_with_openai(prompt)
    return _generate_with_gemini(prompt)


def generate_json(prompt: str) -> dict[str, Any]:
    """Generate and parse a JSON object using provider-native JSON mode."""
    provider = _require_provider()
    if provider == "openai":
        raw = _generate_with_openai(prompt, json_mode=True)
    else:
        raw = _generate_with_gemini(prompt, json_mode=True)

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("The language model returned invalid JSON.") from exc

    if not isinstance(parsed, dict):
        raise ValueError("The language model JSON response must be an object.")
    return parsed


def _retry_call(operation: Callable[[], Any], label: str) -> Any:
    """Retry temporary provider failures with a short exponential backoff."""
    last_exc: Exception | None = None

    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            return operation()
        except Exception as exc:  # provider SDKs expose different exception classes
            last_exc = exc
            if attempt >= MAX_ATTEMPTS or not _is_transient_error(exc):
                raise

            delay = RETRY_DELAYS[attempt - 1]
            logger.warning(
                "%s temporarily unavailable (attempt %s/%s). Retrying in %ss: %s",
                label,
                attempt,
                MAX_ATTEMPTS,
                delay,
                exc,
            )
            time.sleep(delay)

    raise last_exc or RuntimeError(f"{label} failed.")


def _is_transient_error(exc: Exception) -> bool:
    status_code = getattr(exc, "status_code", None)
    if status_code in {429, 500, 502, 503, 504}:
        return True

    text = str(exc).lower()
    return any(
        marker in text
        for marker in (
            "503 unavailable",
            "service unavailable",
            "temporarily unavailable",
            "high demand",
            "rate limit",
            "too many requests",
            "internal server error",
            "bad gateway",
            "gateway timeout",
        )
    )


def _generate_with_gemini(prompt: str, *, json_mode: bool = False) -> str:
    if not settings.GEMINI_API_KEY:
        raise LLMConfigurationError(
            "GEMINI_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    config = types.GenerateContentConfig(
        max_output_tokens=4096 if not json_mode else 2048,
        response_mime_type="application/json" if json_mode else None,
    )

    def request() -> Any:
        return client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
            config=config,
        )

    response = _retry_call(request, "Gemini")
    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("The Gemini service returned an empty response.")
    return text


def _generate_with_openai(prompt: str, *, json_mode: bool = False) -> str:
    if not settings.OPENAI_API_KEY:
        raise LLMConfigurationError(
            "OPENAI_API_KEY is not set. Add it to .env when LLM_PROVIDER=openai."
        )

    from openai import OpenAI

    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    kwargs: dict[str, Any] = {
        "model": settings.OPENAI_MODEL,
        "messages": [{"role": "user", "content": prompt}],
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = _retry_call(
        lambda: client.chat.completions.create(**kwargs),
        "OpenAI",
    )
    text = (response.choices[0].message.content or "").strip()
    if not text:
        raise RuntimeError("The OpenAI service returned an empty response.")
    return text
