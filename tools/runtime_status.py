"""Runtime status helpers for UI transparency."""

from __future__ import annotations

from typing import Mapping

from tools.provider_config import OPENAI, OFFLINE, OPENROUTER, get_provider_config


def _has_config_value(config: Mapping[str, str | None], key: str) -> bool:
    return bool(str(config.get(key) or "").strip())


def build_runtime_status_lines(config: Mapping[str, str | None]) -> list[str]:
    """Return concise runtime status lines without making external calls."""
    has_database_url = _has_config_value(config, "DATABASE_URL")
    provider_config = get_provider_config(config)

    if provider_config.error:
        llm_status = "Provider not configured"
        provider_status = (
            "The selected provider API key is missing. Cognivia will continue "
            "with deterministic guidance where possible."
        )
        credit_status = "No OpenAI/OpenRouter credits are used until a provider is configured."
    elif provider_config.provider == OPENROUTER:
        llm_status = "OpenRouter mode active"
        provider_status = "Provider: OpenRouter"
        credit_status = "Live model calls may use OpenRouter API credits."
    elif provider_config.provider == OPENAI:
        llm_status = "OpenAI mode active"
        provider_status = "Provider: OpenAI"
        credit_status = "Live model calls may use OpenAI API credits."
    elif provider_config.provider == OFFLINE:
        llm_status = "Offline mode active"
        provider_status = (
            "No OpenAI or OpenRouter models are being used. Cognivia will use "
            "deterministic guidance and may skip evidence-backed retrieval."
        )
        credit_status = "Offline mode does not use OpenAI/OpenRouter credits."

    memory_status = (
        "Memory: PostgreSQL configured"
        if has_database_url
        else "Memory: local fallback / no durable DB configured"
    )

    return [
        "Runtime status:",
        llm_status,
        provider_status,
        credit_status,
        "Codex/ChatGPT Plus is development tooling, not Cognivia app runtime.",
        memory_status,
        "Evidence: local Qdrant/RAG evidence path",
    ]
