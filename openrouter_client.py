import logging
import os
import re

import requests
from dotenv import load_dotenv
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from tools.provider_config import (
    OPENAI,
    OPENROUTER,
    get_provider_config,
    provider_api_key,
    provider_base_url,
)

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENAI_URL = "https://api.openai.com/v1/chat/completions"
DEFAULT_MODEL = "openai/gpt-5.4-mini"
GPT5_OPENAI_MODEL_PATTERN = re.compile(r"^openai/gpt-5(?:$|[.-])", re.IGNORECASE)


def _should_retry(exception):
    """Return True for transient errors worth retrying (5xx, timeouts, connection errors)."""
    if isinstance(exception, requests.exceptions.HTTPError):
        return (
            exception.response is not None
            and 500 <= exception.response.status_code < 600
        )

    return isinstance(
        exception,
        (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.ReadTimeout,
        ),
    )


def should_send_temperature(model: str | None) -> bool:
    """Return False for OpenAI GPT-5-family models that reject custom temperature."""
    clean_model = str(model or "").strip()
    if not clean_model:
        return True

    return not GPT5_OPENAI_MODEL_PATTERN.match(clean_model)


@retry(
    retry=retry_if_exception(_should_retry),
    stop=stop_after_attempt(2),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    reraise=True,
)
def _make_request(payload, headers):
    """Make request with retry on transient errors."""
    response = requests.post(
        OPENROUTER_URL,
        headers=headers,
        json=payload,
        timeout=60,
    )
    response.raise_for_status()
    return response


class OpenRouterError(Exception):
    """Generic user-facing error for OpenRouter failures."""

    pass


def call_openrouter(
    user_prompt,
    system_prompt,
    model=DEFAULT_MODEL,
    temperature=0.7,
    max_tokens=1800,
):
    api_key = OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logging.error("OPENROUTER_API_KEY is missing")
        raise OpenRouterError(
            "API key is not configured. Please check your environment settings."
        )

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
    }
    if should_send_temperature(model):
        payload["temperature"] = temperature

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = _make_request(payload, headers)
    except requests.exceptions.HTTPError as error:
        status_code = error.response.status_code if error.response is not None else 0
        if 400 <= status_code < 500:
            error_category = "client_error"
        elif 500 <= status_code < 600:
            error_category = "server_error"
        else:
            error_category = "http_error"
        logging.warning(
            "OpenRouter chat completion failed: status=%s category=%s",
            status_code,
            error_category,
        )
        if 400 <= status_code < 500:
            raise OpenRouterError(
                "The request was invalid. Please check your input and try again."
            ) from error
        raise OpenRouterError(
            "The AI service is temporarily unavailable. Please try again later."
        ) from error
    except requests.exceptions.RequestException as error:
        logging.exception("OpenRouter connection error: %s", error)
        raise OpenRouterError(
            "Could not connect to the AI service. "
            "Please check your internet connection and try again."
        ) from error

    data = response.json()
    message = data["choices"][0]["message"]
    content = message.get("content")

    if content:
        return content

    return "The model returned no final answer. Increase the max_tokens or use a different model."


def call_provider_chat(
    user_prompt,
    system_prompt,
    model=DEFAULT_MODEL,
    temperature=0.7,
    max_tokens=1800,
):
    """Call the explicitly selected provider, preserving the legacy wrapper."""
    provider_config = get_provider_config()
    if provider_config.error or provider_config.provider not in {OPENROUTER, OPENAI}:
        raise OpenRouterError(
            provider_config.error or "AI provider is configured for offline mode."
        )

    if provider_config.provider == OPENROUTER:
        return call_openrouter(
            user_prompt,
            system_prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    api_key = provider_api_key(provider_config)
    if not api_key:
        raise OpenRouterError("The selected provider API key is not configured.")

    url = provider_base_url(provider_config)
    url = f"{url}/chat/completions" if url else OPENAI_URL
    payload = {
        "model": model.removeprefix("openai/"),
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "max_tokens": max_tokens,
    }
    if should_send_temperature(model):
        payload["temperature"] = temperature

    try:
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=60,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"].get("content")
    except requests.exceptions.RequestException as error:
        logging.exception("Provider chat request failed: %s", error)
        raise OpenRouterError("Could not connect to the AI service.") from error

    return content or "The model returned no final answer."
