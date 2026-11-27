"""Pytest bootstrap for offline-safe Cognivia tests."""

from __future__ import annotations

import os


def disable_langsmith_tracing_for_tests() -> None:
    """Keep tests isolated from local LangSmith shell or .env configuration."""
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    os.environ["LANGSMITH_API_KEY"] = ""
    os.environ["LANGCHAIN_API_KEY"] = ""


def isolate_provider_config_for_tests() -> None:
    """Blank provider settings that may come from the developer's shell."""
    for name in ("OPENAI_API_KEY", "OPENROUTER_API_KEY", "COGNIVIA_LLM_PROVIDER"):
        os.environ[name] = ""


def disable_dotenv_loading_for_tests() -> None:
    """Never read a developer's local .env during tests.

    app.py, openrouter_client and rag.retriever call load_dotenv(). Without
    this, a local .env can re-inject real provider keys, even after a test
    deletes the variable, and pytest can print them in failure output. This
    runs before those modules are imported, so their ``from dotenv import
    load_dotenv`` binds to the no-op.
    """
    import dotenv

    dotenv.load_dotenv = lambda *args, **kwargs: False


disable_langsmith_tracing_for_tests()
isolate_provider_config_for_tests()
disable_dotenv_loading_for_tests()
