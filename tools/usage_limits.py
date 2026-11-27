"""Demo usage limits for live LLM provider calls.

The limits count real provider calls (OpenAI or OpenRouter), not user queries:
one user action can trigger several calls (for example intent classification
retries). Offline mode and unconfigured providers never count or block.

- Per-session counter: lives in an injectable mapping, ``st.session_state`` by
  default (only when a Streamlit script run is active).
- Global daily counter: lives in a process-wide ``st.cache_resource`` object
  guarded by a ``threading.Lock``. It stores the UTC date and the count, so it
  resets at UTC midnight. It is in memory only: it also resets when the host
  (for example Render) restarts the service. That is acceptable for a demo.
- Embeddings in ``rag/retriever.py`` are not counted.
"""

from __future__ import annotations

import os
import threading
from collections.abc import Callable, MutableMapping
from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Mapping

import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

from tools.provider_config import OPENAI, OPENROUTER, get_provider_config

# Env var names keep the historical "QUERIES" wording; the values are LLM calls.
SESSION_LIMIT_ENV = "COGNIVIA_MAX_QUERIES_PER_SESSION"
DAILY_LIMIT_ENV = "COGNIVIA_MAX_QUERIES_PER_DAY"
DEFAULT_MAX_CALLS_PER_SESSION = 8
DEFAULT_MAX_CALLS_PER_DAY = 30
SESSION_COUNT_KEY = "cognivia_llm_calls_used"

LIMIT_MESSAGE = "Demo limit reached. Come back tomorrow or run the project locally."

Clock = Callable[[], datetime]


class LLMLimitReached(Exception):
    """Raised on paths that cannot return a value when the demo limit is hit."""


def parse_limit(raw: str | None, default: int) -> int:
    """Return a non-negative limit; empty, invalid or negative values use default."""
    text = str(raw or "").strip()
    if not text:
        return default
    try:
        value = int(text)
    except ValueError:
        return default
    return value if value >= 0 else default


def session_limit(config: Mapping[str, str | None] | None = None) -> int:
    values = config if config is not None else os.environ
    return parse_limit(values.get(SESSION_LIMIT_ENV), DEFAULT_MAX_CALLS_PER_SESSION)


def daily_limit(config: Mapping[str, str | None] | None = None) -> int:
    values = config if config is not None else os.environ
    return parse_limit(values.get(DAILY_LIMIT_ENV), DEFAULT_MAX_CALLS_PER_DAY)


def _utc_today(now: Clock | None) -> date:
    current = now() if now is not None else datetime.now(timezone.utc)
    if current.tzinfo is not None:
        current = current.astimezone(timezone.utc)
    return current.date()


class DailyCallCounter:
    """Thread-safe global call counter that resets when the UTC date changes."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._day: date | None = None
        self._count = 0

    def _roll(self, today: date) -> None:
        if self._day != today:
            self._day = today
            self._count = 0

    def used_today(self, today: date) -> int:
        with self._lock:
            self._roll(today)
            return self._count

    def try_consume(
        self,
        today: date,
        daily_max: int,
        session_store: MutableMapping | None,
        session_max: int,
    ) -> bool:
        """Consume one call from both budgets, or from neither if one is spent."""
        with self._lock:
            self._roll(today)
            session_used = _session_used(session_store)
            if session_store is not None and session_used >= session_max:
                return False
            if self._count >= daily_max:
                return False
            self._count += 1
            if session_store is not None:
                session_store[SESSION_COUNT_KEY] = session_used + 1
            return True


@st.cache_resource(show_spinner=False)
def _shared_counter() -> DailyCallCounter:
    return DailyCallCounter()


def get_global_counter() -> DailyCallCounter:
    """Return the process-wide counter (shared across Streamlit sessions)."""
    return _shared_counter()


def default_session_store() -> MutableMapping | None:
    """Return ``st.session_state`` only inside a Streamlit script run.

    Outside a script run (for example a plain thread) only the global daily
    limit applies. Current Cognivia paths call the provider from the script
    thread (the graph is linear and runs its nodes in the calling thread).
    """
    if get_script_run_ctx() is None:
        return None
    return st.session_state


def _session_used(session_store: MutableMapping | None) -> int:
    if session_store is None:
        return 0
    try:
        return max(0, int(session_store.get(SESSION_COUNT_KEY, 0)))
    except (TypeError, ValueError):
        return 0


def _counts_toward_limits(config: Mapping[str, str | None] | None) -> bool:
    provider_config = get_provider_config(config)
    return provider_config.error is None and provider_config.provider in {
        OPENAI,
        OPENROUTER,
    }


def try_consume_llm_call(
    config: Mapping[str, str | None] | None = None,
    *,
    session_store: MutableMapping | None = None,
    counter: DailyCallCounter | None = None,
    now: Clock | None = None,
) -> bool:
    """Reserve one live provider call; return False when a limit is reached.

    Offline mode and unconfigured providers return True without counting. The
    global daily limit always applies, even when no session store is available.
    """
    if not _counts_toward_limits(config):
        return True

    store = session_store if session_store is not None else default_session_store()
    active_counter = counter if counter is not None else get_global_counter()
    return active_counter.try_consume(
        _utc_today(now),
        daily_limit(config),
        store,
        session_limit(config),
    )


@dataclass(frozen=True)
class UsageSnapshot:
    """Remaining live LLM calls; ``None`` session fields mean no session store."""

    limited: bool
    session_remaining: int | None = None
    session_limit: int | None = None
    day_remaining: int | None = None
    day_limit: int | None = None


def get_usage_snapshot(
    config: Mapping[str, str | None] | None = None,
    *,
    session_store: MutableMapping | None = None,
    counter: DailyCallCounter | None = None,
    now: Clock | None = None,
) -> UsageSnapshot:
    """Return remaining calls without consuming any and without network access."""
    if not _counts_toward_limits(config):
        return UsageSnapshot(limited=False)

    store = session_store if session_store is not None else default_session_store()
    active_counter = counter if counter is not None else get_global_counter()
    session_max = session_limit(config)
    daily_max = daily_limit(config)
    day_used = active_counter.used_today(_utc_today(now))
    return UsageSnapshot(
        limited=True,
        session_remaining=(
            None if store is None else max(0, session_max - _session_used(store))
        ),
        session_limit=session_max,
        day_remaining=max(0, daily_max - day_used),
        day_limit=daily_max,
    )
