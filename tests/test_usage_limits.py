"""Offline tests for demo LLM-call limits (no provider calls)."""

from datetime import datetime, timezone

import pytest

from tools import usage_limits
from tools.usage_limits import (
    DailyCallCounter,
    LIMIT_MESSAGE,
    SESSION_COUNT_KEY,
    get_usage_snapshot,
    parse_limit,
    try_consume_llm_call,
)
from tools.runtime_status import build_usage_status_text

LIVE = {"COGNIVIA_LLM_PROVIDER": "openai", "OPENAI_API_KEY": "test-key"}


def clock(year=2026, month=11, day=25, hour=12):
    moment = datetime(year, month, day, hour, tzinfo=timezone.utc)
    return lambda: moment


def live(**limits):
    return {**LIVE, **limits}


def test_defaults_are_8_per_session_and_30_per_day():
    assert usage_limits.session_limit({}) == 8
    assert usage_limits.daily_limit({}) == 30


def test_limit_message_is_the_agreed_text():
    assert LIMIT_MESSAGE == (
        "Demo limit reached. Come back tomorrow or run the project locally."
    )


@pytest.mark.parametrize("raw", [None, "", "  ", "abc", "1.5", "-3"])
def test_invalid_or_empty_values_fall_back_to_default(raw):
    assert parse_limit(raw, 8) == 8


def test_zero_is_a_valid_limit_and_valid_values_are_used():
    assert parse_limit("0", 8) == 0
    assert parse_limit(" 5 ", 8) == 5


def test_session_limit_blocks_after_n_calls():
    config = live(COGNIVIA_MAX_QUERIES_PER_SESSION="2")
    store, counter = {}, DailyCallCounter()

    results = [
        try_consume_llm_call(config, session_store=store, counter=counter, now=clock())
        for _ in range(3)
    ]

    assert results == [True, True, False]
    assert store[SESSION_COUNT_KEY] == 2


def test_global_limit_is_shared_across_sessions():
    config = live(COGNIVIA_MAX_QUERIES_PER_DAY="2")
    counter = DailyCallCounter()

    results = [
        try_consume_llm_call(config, session_store={}, counter=counter, now=clock())
        for _ in range(3)
    ]

    assert results == [True, True, False]


def test_global_limit_applies_without_session_store(monkeypatch):
    monkeypatch.setattr(usage_limits, "default_session_store", lambda: None)
    config = live(COGNIVIA_MAX_QUERIES_PER_DAY="1")
    counter = DailyCallCounter()

    assert try_consume_llm_call(config, counter=counter, now=clock()) is True
    assert try_consume_llm_call(config, counter=counter, now=clock()) is False


def test_blocked_session_does_not_consume_global_budget():
    config = live(COGNIVIA_MAX_QUERIES_PER_SESSION="1", COGNIVIA_MAX_QUERIES_PER_DAY="5")
    counter = DailyCallCounter()
    store = {}

    try_consume_llm_call(config, session_store=store, counter=counter, now=clock())
    try_consume_llm_call(config, session_store=store, counter=counter, now=clock())

    assert counter.used_today(clock()().date()) == 1


def test_daily_counter_resets_when_utc_day_changes():
    config = live(COGNIVIA_MAX_QUERIES_PER_DAY="1")
    counter = DailyCallCounter()

    assert try_consume_llm_call(config, session_store={}, counter=counter, now=clock(day=25, hour=23))
    assert not try_consume_llm_call(config, session_store={}, counter=counter, now=clock(day=25, hour=23))
    assert try_consume_llm_call(config, session_store={}, counter=counter, now=clock(day=26, hour=0))


def test_zero_blocks_every_call():
    counter = DailyCallCounter()

    assert not try_consume_llm_call(
        live(COGNIVIA_MAX_QUERIES_PER_DAY="0"), session_store={}, counter=counter, now=clock()
    )
    assert not try_consume_llm_call(
        live(COGNIVIA_MAX_QUERIES_PER_SESSION="0"), session_store={}, counter=counter, now=clock()
    )


def test_invalid_env_values_use_defaults_without_breaking():
    config = live(
        COGNIVIA_MAX_QUERIES_PER_SESSION="nope", COGNIVIA_MAX_QUERIES_PER_DAY=""
    )
    snapshot = get_usage_snapshot(config, session_store={}, counter=DailyCallCounter(), now=clock())

    assert (snapshot.session_limit, snapshot.day_limit) == (8, 30)


@pytest.mark.parametrize(
    "config",
    [
        {},
        {"COGNIVIA_LLM_PROVIDER": "offline", "OPENAI_API_KEY": "k"},
        {"COGNIVIA_LLM_PROVIDER": "openai"},
    ],
)
def test_offline_or_unconfigured_never_counts_or_blocks(config):
    config = {**config, "COGNIVIA_MAX_QUERIES_PER_SESSION": "0", "COGNIVIA_MAX_QUERIES_PER_DAY": "0"}
    counter, store = DailyCallCounter(), {}

    assert try_consume_llm_call(config, session_store=store, counter=counter, now=clock())
    assert store == {}
    assert counter.used_today(clock()().date()) == 0
    assert not get_usage_snapshot(config, session_store=store, counter=counter).limited


def test_usage_status_text_reports_remaining_calls_without_consuming():
    counter, store = DailyCallCounter(), {}
    try_consume_llm_call(live(), session_store=store, counter=counter, now=clock())

    text = build_usage_status_text(live(), session_store=store, counter=counter, now=clock())

    assert text == "session 7/8, today 29/30 calls left"
    assert build_usage_status_text({}, session_store={}, counter=counter) == "Not limited"
    assert counter.used_today(clock()().date()) == 1
