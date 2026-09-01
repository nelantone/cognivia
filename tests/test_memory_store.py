"""Tests for the durable learner memory foundation."""

import json
from datetime import datetime, timezone

import pytest

from memory import (
    InMemoryMemoryStore,
    MemoryValidationError,
    NullMemoryStore,
    PostgresMemoryStore,
    build_learner_memory_export,
    learner_memory_export_to_json,
    normalize_learning_event,
    normalize_learner_profile,
)
from memory.schema import MEMORY_SCHEMA_SQL, OPTIONAL_MEMORY_EMBEDDINGS_SCHEMA_SQL
from tools.guided_intake import ENTRY_POINTS, PREFERRED_WORK_STYLES


def _profile(**overrides):
    values = {
        "entry_point": ENTRY_POINTS[0],
        "current_level": " Beginner ",
        "current_skills": " Python, APIs\nRAG ",
        "interests": "documents, useful AI products",
        "preferred_work_style": PREFERRED_WORK_STYLES[0],
        "target_role": " AI Application Engineer ",
        "goal": " Build a practical RAG portfolio project ",
        "time_available_minutes": 60,
    }
    values.update(overrides)
    return values


def test_normalize_learner_profile_accepts_current_guided_intake_shape():
    profile = normalize_learner_profile(_profile(target_role="  "))

    assert profile == {
        "entry_point": ENTRY_POINTS[0],
        "current_level": "beginner",
        "skills": ["Python", "APIs", "RAG"],
        "interests": ["documents", "useful AI products"],
        "target_role_or_direction": None,
        "preferred_work_style": PREFERRED_WORK_STYLES[0],
        "available_learning_time_minutes": 60,
        "motivation": None,
        "constraints_blockers": None,
        "preferred_next_action": None,
        "goal": "Build a practical RAG portfolio project",
        "raw_form": {},
        "created_at": profile["created_at"],
    }


def test_normalize_learner_profile_accepts_expanded_memory_fields():
    profile = normalize_learner_profile(
        _profile(
            skills=["Python", "evaluation"],
            current_skills="ignored",
            target_role_or_direction="AI Quality Engineer",
            available_learning_time_minutes=90,
            motivation="Portfolio confidence",
            constraints_blockers="Limited time",
            preferred_next_action="build project",
        ),
        raw_form={"source": "test"},
    )

    assert profile["skills"] == ["Python", "evaluation"]
    assert profile["target_role_or_direction"] == "AI Quality Engineer"
    assert profile["available_learning_time_minutes"] == 90
    assert profile["motivation"] == "Portfolio confidence"
    assert profile["constraints_blockers"] == "Limited time"
    assert profile["preferred_next_action"] == "build project"
    assert profile["raw_form"] == {"source": "test"}


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("current_level", "expert", "current_level"),
        ("preferred_work_style", "other", "preferred_work_style"),
        ("current_skills", " ", "skills"),
        ("interests", " ", "interests"),
        ("goal", " ", "goal"),
        ("time_available_minutes", 0, "available_learning_time_minutes"),
        ("time_available_minutes", 481, "available_learning_time_minutes"),
    ],
)
def test_normalize_learner_profile_rejects_invalid_values(field, value, match):
    with pytest.raises(MemoryValidationError, match=match):
        normalize_learner_profile(_profile(**{field: value}))


def test_normalize_learning_event_shapes_append_only_payload():
    event = normalize_learning_event(
        learner_id="learner-1",
        event_type="noise_to_signal_decision",
        user_goal="Should I learn RAG or agents?",
        selected_focus="RAG",
        recommendation="Start with a small RAG app.",
        next_action="Build one retrieval prototype.",
        evidence_refs=[{"source": "ai_engineering_learning_paths.md"}],
        decision_status="resolved",
        interaction_mode="comparison",
        decision_trace=["User goal: Should I learn RAG or agents?"],
        metadata={"app": "noise_to_signal"},
    )

    assert event["learner_id"] == "learner-1"
    assert event["event_type"] == "noise_to_signal_decision"
    assert event["evidence_refs"] == [{"source": "ai_engineering_learning_paths.md"}]
    assert event["decision_trace"] == ["User goal: Should I learn RAG or agents?"]
    assert event["metadata"] == {"app": "noise_to_signal"}
    assert event["created_at"]


def test_normalize_learning_event_removes_full_evidence_content():
    event = normalize_learning_event(
        learner_id="learner-1",
        user_goal="Learn RAG",
        evidence_refs=[
            {
                "source": "ai_engineering_learning_paths.md",
                "page_content": "Full retrieved document text should not be stored.",
                "title": "AI Engineering Learning Paths",
            }
        ],
    )

    assert event["evidence_refs"] == [
        {
            "source": "ai_engineering_learning_paths.md",
            "title": "AI Engineering Learning Paths",
        }
    ]


def test_build_learner_memory_export_includes_profile_events_and_metadata():
    payload = build_learner_memory_export(
        learner_id="learner-1",
        latest_profile={"goal": "Build a RAG project"},
        recent_learning_events=[
            {
                "event_type": "noise_to_signal_decision",
                "user_goal": "Choose next focus",
                "next_action": "Build one retrieval prototype.",
            }
        ],
        exported_at="2026-07-10T12:00:00+00:00",
    )

    assert payload["export_version"] == "learner_memory.v1"
    assert payload["exported_at"] == "2026-07-10T12:00:00+00:00"
    assert payload["learner_id"] == "learner-1"
    assert payload["latest_profile"] == {"goal": "Build a RAG project"}
    assert payload["recent_learning_events"][0]["next_action"] == (
        "Build one retrieval prototype."
    )
    assert "not a full chat transcript" in payload["note"]


def test_build_learner_memory_export_removes_full_text_and_secret_fields():
    payload = build_learner_memory_export(
        learner_id="learner-1",
        latest_profile={
            "goal": "Build a RAG project",
            "openrouter_api_key": "secret-value",
            "raw_form": {"password": "secret-value", "motivation": "portfolio"},
        },
        recent_learning_events=[
            {
                "event_type": "noise_to_signal_decision",
                "evidence_refs": [
                    {
                        "source": "rag_eval.md",
                        "page_content": "Full retrieved document text.",
                        "title": "RAG Evaluation",
                    }
                ],
                "metadata": {"auth_token": "secret-value", "safe": "kept"},
                "full_text": "Full transcript text.",
            }
        ],
        exported_at="2026-07-10T12:00:00+00:00",
    )
    export_json = learner_memory_export_to_json(payload)

    assert "secret-value" not in export_json
    assert "Full retrieved document text" not in export_json
    assert "Full transcript text" not in export_json
    assert payload["latest_profile"] == {
        "goal": "Build a RAG project",
        "raw_form": {"motivation": "portfolio"},
    }
    assert payload["recent_learning_events"][0]["evidence_refs"] == [
        {"source": "rag_eval.md", "title": "RAG Evaluation"}
    ]
    assert payload["recent_learning_events"][0]["metadata"] == {"safe": "kept"}


def test_learner_memory_export_to_json_returns_valid_json():
    payload = build_learner_memory_export(
        learner_id="learner-1",
        latest_profile=None,
        recent_learning_events=[],
        exported_at="2026-07-10T12:00:00+00:00",
    )

    assert json.loads(learner_memory_export_to_json(payload)) == payload


def test_build_learner_memory_export_serializes_datetime_values():
    payload = build_learner_memory_export(
        learner_id="learner-1",
        latest_profile=None,
        recent_learning_events=[
            {"created_at": datetime(2026, 7, 10, 12, 0, tzinfo=timezone.utc)}
        ],
        exported_at="2026-07-10T12:00:00+00:00",
    )

    assert payload["recent_learning_events"][0]["created_at"] == (
        "2026-07-10T12:00:00+00:00"
    )


def test_null_memory_store_never_raises_or_persists():
    store = NullMemoryStore()

    assert store.save_learner_profile("learner-1", _profile()) is None
    assert (
        store.save_learning_event(
            learner_id="learner-1",
            user_goal="What should I learn next?",
        )
        is None
    )
    assert store.get_latest_learner_profile("learner-1") is None
    assert store.get_recent_learning_events("learner-1") == []
    assert store.search_memory("learner-1", "RAG") == []


def test_in_memory_store_saves_latest_profile_and_recent_events_newest_first():
    store = InMemoryMemoryStore()

    first_profile_id = store.save_learner_profile("learner-1", _profile(goal="First"))
    second_profile_id = store.save_learner_profile("learner-1", _profile(goal="Second"))
    first_event_id = store.save_learning_event(
        learner_id="learner-1",
        user_goal="First goal",
        recommendation="Try RAG.",
    )
    second_event_id = store.save_learning_event(
        learner_id="learner-1",
        user_goal="Second goal",
        recommendation="Try evaluation.",
    )

    assert first_profile_id
    assert second_profile_id
    assert first_event_id
    assert second_event_id
    assert store.get_latest_learner_profile("learner-1")["goal"] == "Second"
    assert store.get_latest_learner_profile("learner-1")["learner_id"] == "learner-1"
    assert [
        event["user_goal"]
        for event in store.get_recent_learning_events("learner-1", limit=10)
    ] == ["Second goal", "First goal"]
    assert store.get_recent_learning_events("learner-1", limit=0) == []


def test_in_memory_search_scopes_results_by_learner():
    store = InMemoryMemoryStore()
    store.save_learning_event(
        learner_id="learner-1",
        user_goal="Learn RAG",
        recommendation="Build a retrieval app.",
    )
    store.save_learning_event(
        learner_id="learner-2",
        user_goal="Learn RAG",
        recommendation="This should not appear.",
    )

    results = store.search_memory("learner-1", "retrieval")

    assert len(results) == 1
    assert results[0]["learner_id"] == "learner-1"


def test_postgres_store_without_url_fails_soft():
    store = PostgresMemoryStore()

    assert store.create_schema() is False
    assert store.create_vector_schema() is False
    assert store.save_learner_profile("learner-1", _profile()) is None
    assert (
        store.save_learning_event(
            learner_id="learner-1",
            user_goal="What should I learn next?",
        )
        is None
    )
    assert store.get_latest_learner_profile("learner-1") is None
    assert store.get_recent_learning_events("learner-1") == []
    assert store.search_memory("learner-1", "RAG") == []


def test_default_schema_does_not_require_pgvector():
    assert "vector(1536)" not in MEMORY_SCHEMA_SQL
    assert "vector(1536)" in OPTIONAL_MEMORY_EMBEDDINGS_SCHEMA_SQL


def test_memory_store_does_not_require_openrouter_configuration(monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    store = InMemoryMemoryStore()

    event_id = store.save_learning_event(
        learner_id="learner-1",
        user_goal="Learn RAG",
        recommendation="Build a retrieval app.",
    )

    assert event_id
