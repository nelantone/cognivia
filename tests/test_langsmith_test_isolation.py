"""Regression tests for pytest-level LangSmith isolation."""

from __future__ import annotations

import importlib
import os
import sys


def test_pytest_bootstrap_disables_langsmith_before_tests_import_app_modules():
    assert os.environ["LANGSMITH_TRACING"] == "false"
    assert os.environ["LANGCHAIN_TRACING_V2"] == "false"
    assert os.environ["LANGSMITH_API_KEY"] == ""
    assert os.environ["LANGCHAIN_API_KEY"] == ""


def test_langsmith_isolation_overrides_hostile_local_tracing_config(monkeypatch):
    monkeypatch.setenv("LANGSMITH_TRACING", "true")
    monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
    monkeypatch.setenv("LANGSMITH_API_KEY", "fake-test-key")
    monkeypatch.setenv("LANGCHAIN_API_KEY", "fake-test-key")

    sys.modules["conftest"].disable_langsmith_tracing_for_tests()
    langsmith_config = importlib.import_module("langsmith_config")
    importlib.reload(langsmith_config)
    langsmith_config.configure_langsmith()

    assert os.environ["LANGSMITH_TRACING"] == "false"
    assert os.environ["LANGCHAIN_TRACING_V2"] == "false"
    assert os.environ["LANGSMITH_API_KEY"] == ""
    assert os.environ["LANGCHAIN_API_KEY"] == ""
