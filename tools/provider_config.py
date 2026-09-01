"""Provider configuration and safe client settings."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Mapping

OPENROUTER = "openrouter"
OPENAI = "openai"
OFFLINE = "offline"
SUPPORTED_PROVIDERS = frozenset({OPENROUTER, OPENAI, OFFLINE})
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


@dataclass(frozen=True)
class ProviderConfig:
    """Resolved provider configuration without exposing secret values."""

    provider: str
    openrouter_configured: bool
    openai_configured: bool
    error: str | None = None

    @property
    def configured(self) -> bool:
        if self.provider == OPENROUTER:
            return self.openrouter_configured
        if self.provider == OPENAI:
            return self.openai_configured
        return self.provider == OFFLINE


def _has_value(config: Mapping[str, str | None], key: str) -> bool:
    return bool(str(config.get(key) or "").strip())


def get_provider_config(
    config: Mapping[str, str | None] | None = None,
) -> ProviderConfig:
    """Resolve provider selection without making network calls.

    An omitted selector preserves the legacy OpenRouter behavior when its key
    exists. OpenAI is never selected from key presence alone.
    """
    values = config if config is not None else os.environ
    openrouter_configured = _has_value(values, "OPENROUTER_API_KEY")
    openai_configured = _has_value(values, "OPENAI_API_KEY")
    selected = str(values.get("COGNIVIA_LLM_PROVIDER") or "").strip().lower()

    if not selected:
        selected = OPENROUTER if openrouter_configured else OFFLINE

    if selected not in SUPPORTED_PROVIDERS:
        return ProviderConfig(
            selected,
            openrouter_configured,
            openai_configured,
            f"Unsupported provider: {selected}",
        )

    if selected == OPENROUTER and not openrouter_configured:
        error = "OpenRouter provider selected but OPENROUTER_API_KEY is missing."
    elif selected == OPENAI and not openai_configured:
        error = "OpenAI provider selected but OPENAI_API_KEY is missing."
    else:
        error = None

    return ProviderConfig(selected, openrouter_configured, openai_configured, error)


def provider_api_key(provider_config: ProviderConfig, config=None) -> str | None:
    """Return only the selected provider key for internal client construction."""
    values = config if config is not None else os.environ
    if provider_config.provider == OPENROUTER:
        return str(values.get("OPENROUTER_API_KEY") or "").strip() or None
    if provider_config.provider == OPENAI:
        return str(values.get("OPENAI_API_KEY") or "").strip() or None
    return None


def provider_base_url(provider_config: ProviderConfig) -> str | None:
    """Return a custom base URL only for OpenRouter."""
    return OPENROUTER_BASE_URL if provider_config.provider == OPENROUTER else None
