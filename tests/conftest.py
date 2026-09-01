"""Pytest bootstrap for offline-safe Cognivia tests."""

from __future__ import annotations

import os


def disable_langsmith_tracing_for_tests() -> None:
    """Keep tests isolated from local LangSmith shell or .env configuration."""
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"
    os.environ["LANGSMITH_API_KEY"] = ""
    os.environ["LANGCHAIN_API_KEY"] = ""


disable_langsmith_tracing_for_tests()
