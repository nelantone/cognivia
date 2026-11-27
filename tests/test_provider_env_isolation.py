"""Regression tests for pytest-level isolation from a developer's local .env."""

from __future__ import annotations

import os

import dotenv

import app
import openrouter_client
import rag.retriever

PROVIDER_ENV_NAMES = ("OPENAI_API_KEY", "OPENROUTER_API_KEY", "COGNIVIA_LLM_PROVIDER")


def test_pytest_bootstrap_blanks_provider_config():
    for name in PROVIDER_ENV_NAMES:
        assert os.environ[name] == ""


def test_dotenv_loading_is_disabled_for_tests(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OPENAI_API_KEY=not-a-real-key\nCOGNIVIA_LLM_PROVIDER=openai\n"
    )
    for name in PROVIDER_ENV_NAMES:
        monkeypatch.delenv(name, raising=False)

    assert dotenv.load_dotenv(env_file) is False

    for name in PROVIDER_ENV_NAMES:
        assert name not in os.environ


def test_app_modules_use_the_disabled_loader():
    for module in (app, openrouter_client, rag.retriever):
        assert module.load_dotenv() is False
