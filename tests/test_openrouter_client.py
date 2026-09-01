"""Tests for openrouter_client retry decision logic."""

import pytest
import requests

import openrouter_client
from openrouter_client import (
    _should_retry,
    call_openrouter,
    call_provider_chat,
    should_send_temperature,
)


class FakeOpenRouterResponse:
    """Minimal response object for call_openrouter payload tests."""

    def json(self):
        return {"choices": [{"message": {"content": "ok"}}]}

    def raise_for_status(self):
        return None


def _capture_openrouter_payload(monkeypatch, model, temperature=0.3):
    captured = {}

    def fake_make_request(payload, headers):
        captured["payload"] = payload
        captured["headers"] = headers
        return FakeOpenRouterResponse()

    monkeypatch.setattr(openrouter_client, "OPENROUTER_API_KEY", "test-api-key")
    monkeypatch.setattr(openrouter_client, "_make_request", fake_make_request)

    result = call_openrouter(
        user_prompt="User prompt",
        system_prompt="System prompt",
        model=model,
        temperature=temperature,
    )

    assert result == "ok"
    return captured["payload"]


class TestShouldSendTemperature:
    """Tests for model-specific temperature payload support."""

    @pytest.mark.parametrize(
        "model",
        [
            "openai/gpt-5",
            "openai/gpt-5-mini",
            "openai/gpt-5.1",
            "openai/gpt-5.4-20260317",
            "openai/gpt-5.2-codex-20260114",
            "openai/gpt-5.4-mini",
        ],
    )
    def test_gpt5_family_returns_false(self, model):
        assert should_send_temperature(model) is False

    @pytest.mark.parametrize(
        "model",
        [
            "",
            None,
            "openai/gpt-4.1",
            "anthropic/claude-3.5-sonnet",
        ],
    )
    def test_non_gpt5_or_empty_returns_true(self, model):
        assert should_send_temperature(model) is True


class TestCallOpenRouterPayload:
    """Tests for OpenRouter chat completion payload construction."""

    def test_gpt5_model_payload_omits_temperature(self, monkeypatch):
        payload = _capture_openrouter_payload(monkeypatch, "openai/gpt-5")

        assert "temperature" not in payload

    def test_gpt5_dated_variant_payload_omits_temperature(self, monkeypatch):
        payload = _capture_openrouter_payload(
            monkeypatch,
            "openai/gpt-5.4-20260317",
        )

        assert "temperature" not in payload

    def test_gpt5_codex_variant_payload_omits_temperature(self, monkeypatch):
        payload = _capture_openrouter_payload(
            monkeypatch,
            "openai/gpt-5.2-codex-20260114",
        )

        assert "temperature" not in payload

    def test_non_gpt5_model_payload_includes_temperature(self, monkeypatch):
        payload = _capture_openrouter_payload(
            monkeypatch,
            "openai/gpt-4.1",
            temperature=0.2,
        )

        assert payload["temperature"] == 0.2

    def test_http_error_log_excludes_response_and_request_secrets(
        self,
        monkeypatch,
        caplog,
    ):
        response = requests.Response()
        response.status_code = 400
        response._content = b"raw-provider-secret-body with echoed user content"
        error = requests.HTTPError("provider request failed", response=response)

        def fail_request(payload, headers):
            raise error

        monkeypatch.setattr(openrouter_client, "OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(openrouter_client, "_make_request", fail_request)

        with caplog.at_level("WARNING"):
            with pytest.raises(openrouter_client.OpenRouterError):
                call_openrouter(
                    user_prompt="private-user-prompt",
                    system_prompt="private-system-prompt",
                )

        log_text = caplog.text
        assert "status=400" in log_text
        assert "category=client_error" in log_text
        assert "raw-provider-secret-body" not in log_text
        assert "echoed user content" not in log_text
        assert "private-user-prompt" not in log_text
        assert "private-system-prompt" not in log_text
        assert "test-api-key" not in log_text


class TestProviderChat:
    """Provider selection tests use request fakes and never access the network."""

    def test_openai_provider_uses_openai_key_and_native_url(self, monkeypatch):
        captured = {}

        def fake_post(url, headers, json, timeout):
            captured.update(url=url, headers=headers, json=json, timeout=timeout)
            return FakeOpenRouterResponse()

        monkeypatch.setenv("COGNIVIA_LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
        monkeypatch.setenv("OPENROUTER_API_KEY", "router-test-key")
        monkeypatch.setattr(openrouter_client.requests, "post", fake_post)

        assert call_provider_chat("user", "system", model="openai/gpt-4.1") == "ok"
        assert captured["url"] == "https://api.openai.com/v1/chat/completions"
        assert captured["headers"]["Authorization"] == "Bearer openai-test-key"
        assert captured["json"]["model"] == "gpt-4.1"

    def test_offline_provider_does_not_call_requests(self, monkeypatch):
        def unexpected_post(*args, **kwargs):
            raise AssertionError("offline mode attempted a provider request")

        monkeypatch.setenv("COGNIVIA_LLM_PROVIDER", "offline")
        monkeypatch.setenv("OPENAI_API_KEY", "openai-test-key")
        monkeypatch.setenv("OPENROUTER_API_KEY", "router-test-key")
        monkeypatch.setattr(openrouter_client.requests, "post", unexpected_post)

        with pytest.raises(openrouter_client.OpenRouterError, match="offline"):
            call_provider_chat("user", "system")

    def test_openrouter_provider_keeps_legacy_request_path(self, monkeypatch):
        monkeypatch.setenv("COGNIVIA_LLM_PROVIDER", "openrouter")
        monkeypatch.setenv("OPENROUTER_API_KEY", "router-test-key")
        monkeypatch.setattr(
            openrouter_client,
            "_make_request",
            lambda payload, headers: FakeOpenRouterResponse(),
        )

        assert call_provider_chat("user", "system", model="openai/gpt-4.1") == "ok"


class TestShouldRetry:
    """Tests for _should_retry() retry decision logic."""

    def test_5xx_returns_true(self):
        """HTTP 5xx errors should be retried."""
        resp = requests.Response()
        resp.status_code = 502
        err = requests.HTTPError(response=resp)
        assert _should_retry(err) is True

    def test_500_returns_true(self):
        """HTTP 500 should be retried."""
        resp = requests.Response()
        resp.status_code = 500
        err = requests.HTTPError(response=resp)
        assert _should_retry(err) is True

    def test_599_returns_true(self):
        """HTTP 599 should be retried."""
        resp = requests.Response()
        resp.status_code = 599
        err = requests.HTTPError(response=resp)
        assert _should_retry(err) is True

    def test_400_returns_false(self):
        """HTTP 400 should not be retried."""
        resp = requests.Response()
        resp.status_code = 400
        err = requests.HTTPError(response=resp)
        assert _should_retry(err) is False

    def test_401_returns_false(self):
        """HTTP 401 should not be retried."""
        resp = requests.Response()
        resp.status_code = 401
        err = requests.HTTPError(response=resp)
        assert _should_retry(err) is False

    def test_403_returns_false(self):
        """HTTP 403 should not be retried."""
        resp = requests.Response()
        resp.status_code = 403
        err = requests.HTTPError(response=resp)
        assert _should_retry(err) is False

    def test_404_returns_false(self):
        """HTTP 404 should not be retried."""
        resp = requests.Response()
        resp.status_code = 404
        err = requests.HTTPError(response=resp)
        assert _should_retry(err) is False

    def test_timeout_returns_true(self):
        """Timeout should be retried."""
        assert _should_retry(requests.exceptions.Timeout()) is True

    def test_read_timeout_returns_true(self):
        """ReadTimeout should be retried."""
        assert _should_retry(requests.exceptions.ReadTimeout()) is True

    def test_connection_error_returns_true(self):
        """ConnectionError should be retried."""
        assert _should_retry(requests.exceptions.ConnectionError()) is True

    def test_generic_request_exception_returns_false(self):
        """Generic RequestException should not be retried."""
        assert _should_retry(requests.exceptions.RequestException()) is False

    def test_http_error_without_response_returns_false(self):
        """HTTPError without response should not be retried."""
        err = requests.HTTPError()
        assert _should_retry(err) is False
