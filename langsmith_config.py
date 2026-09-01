"""Optional LangSmith tracing configuration.

LangSmith tracing is optional local observability. It remains disabled unless
the environment explicitly enables it.

It has been validated locally with the EU LangSmith endpoint and a
workspace-specific API key, but the app and LangGraph workflow do not require
it for normal reviewer-safe runs.
"""

import os


def configure_langsmith() -> None:
    """Configure safe LangSmith defaults without enabling tracing automatically.

    Default tracing flags:
    - LANGSMITH_TRACING=false
    - LANGCHAIN_TRACING_V2=false

    If tracing is explicitly enabled, sets:
    - LANGSMITH_PROJECT=skill-compass-local
    """
    os.environ.setdefault("LANGSMITH_TRACING", "false")
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")

    tracing_enabled = os.environ.get("LANGSMITH_TRACING", "").lower() == "true"
    legacy_tracing_enabled = (
        os.environ.get("LANGCHAIN_TRACING_V2", "").lower() == "true"
    )

    if not tracing_enabled and not legacy_tracing_enabled:
        return

    os.environ.setdefault("LANGSMITH_PROJECT", "skill-compass-local")
