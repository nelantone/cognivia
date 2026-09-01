"""Offline tests for explicit provider configuration."""

from tools.provider_config import (
    OPENAI,
    OFFLINE,
    OPENROUTER,
    get_provider_config,
    provider_api_key,
    provider_base_url,
)


def test_provider_defaults_to_legacy_openrouter_when_only_its_key_exists():
    config = get_provider_config({"OPENROUTER_API_KEY": "router-test-key"})

    assert config.provider == OPENROUTER
    assert config.configured
    assert provider_api_key(config, {"OPENROUTER_API_KEY": "router-test-key"}) == (
        "router-test-key"
    )
    assert provider_base_url(config) == "https://openrouter.ai/api/v1"


def test_openai_key_is_not_used_without_explicit_provider():
    config = get_provider_config({"OPENAI_API_KEY": "openai-test-key"})

    assert config.provider == OFFLINE
    assert not config.openrouter_configured
    assert config.openai_configured
    assert provider_api_key(config, {"OPENAI_API_KEY": "openai-test-key"}) is None


def test_explicit_openai_uses_only_openai_key_and_native_base_url():
    values = {
        "COGNIVIA_LLM_PROVIDER": "openai",
        "OPENAI_API_KEY": "openai-test-key",
        "OPENROUTER_API_KEY": "router-test-key",
    }
    config = get_provider_config(values)

    assert config.provider == OPENAI
    assert config.configured
    assert provider_api_key(config, values) == "openai-test-key"
    assert provider_base_url(config) is None


def test_explicit_offline_never_uses_configured_keys():
    values = {
        "COGNIVIA_LLM_PROVIDER": "offline",
        "OPENAI_API_KEY": "openai-test-key",
        "OPENROUTER_API_KEY": "router-test-key",
    }
    config = get_provider_config(values)

    assert config.provider == OFFLINE
    assert config.configured
    assert provider_api_key(config, values) is None


def test_missing_selected_key_reports_safe_configuration_error():
    config = get_provider_config({"COGNIVIA_LLM_PROVIDER": "openai"})

    assert config.error == "OpenAI provider selected but OPENAI_API_KEY is missing."
    assert not config.configured
    assert "API_KEY" in config.error
    assert "test" not in config.error


def test_unsupported_provider_reports_configuration_error_without_keys():
    config = get_provider_config({"COGNIVIA_LLM_PROVIDER": "unknown"})

    assert config.error == "Unsupported provider: unknown"
    assert not config.configured
