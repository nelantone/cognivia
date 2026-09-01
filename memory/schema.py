"""Schema helpers for durable learner memory."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, TypedDict

from security import _check_input_safety
from tools.guided_intake import CURRENT_LEVEL_OPTIONS, PREFERRED_WORK_STYLES

MAX_SHORT_TEXT_LENGTH = 100
MAX_GOAL_LENGTH = 500
MAX_LONG_TEXT_LENGTH = 1000
MAX_LIST_ITEMS = 20
MAX_LIST_ITEM_LENGTH = 80
MAX_EVENT_LIMIT = 50
MAX_LEARNING_TIME_MINUTES = 480
EVIDENCE_CONTENT_KEYS = {"content", "document", "full_text", "page_content", "text"}

MEMORY_SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS learners (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    display_name text NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS learner_profiles (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    learner_id uuid NOT NULL REFERENCES learners(id),
    entry_point text NULL,
    current_level text NOT NULL,
    skills jsonb NOT NULL DEFAULT '[]'::jsonb,
    interests jsonb NOT NULL DEFAULT '[]'::jsonb,
    target_role_or_direction text NULL,
    preferred_work_style text NULL,
    available_learning_time_minutes integer NULL,
    motivation text NULL,
    constraints_blockers text NULL,
    preferred_next_action text NULL,
    goal text NOT NULL,
    raw_form jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS learning_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    learner_id uuid NOT NULL REFERENCES learners(id),
    profile_id uuid NULL REFERENCES learner_profiles(id),
    event_type text NOT NULL,
    user_goal text NOT NULL,
    selected_focus text NULL,
    recommended_direction text NULL,
    recommendation text NULL,
    next_action text NULL,
    decision_status text NULL,
    interaction_mode text NULL,
    evidence_refs jsonb NOT NULL DEFAULT '[]'::jsonb,
    decision_trace jsonb NOT NULL DEFAULT '[]'::jsonb,
    metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_at timestamptz NOT NULL DEFAULT now()
);
"""

OPTIONAL_MEMORY_EMBEDDINGS_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS memory_embeddings (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    learner_id uuid NOT NULL REFERENCES learners(id),
    learning_event_id uuid NULL REFERENCES learning_events(id),
    learner_profile_id uuid NULL REFERENCES learner_profiles(id),
    content text NOT NULL,
    embedding vector(1536) NULL,
    embedding_model text NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
"""


class MemoryValidationError(ValueError):
    """Raised when learner memory input is invalid."""


class LearnerProfileSnapshot(TypedDict, total=False):
    """Normalized learner profile fields stored in durable memory."""

    learner_id: str
    entry_point: str | None
    current_level: str
    skills: list[str]
    interests: list[str]
    target_role_or_direction: str | None
    preferred_work_style: str
    available_learning_time_minutes: int
    motivation: str | None
    constraints_blockers: str | None
    preferred_next_action: str | None
    goal: str
    raw_form: dict[str, Any]
    created_at: str


class LearningEvent(TypedDict, total=False):
    """Normalized append-only learner memory event."""

    learner_id: str
    profile_id: str | None
    event_type: str
    user_goal: str
    selected_focus: str | None
    recommended_direction: str | None
    recommendation: str | None
    next_action: str | None
    decision_status: str | None
    interaction_mode: str | None
    evidence_refs: list[dict[str, Any]]
    decision_trace: list[str]
    metadata: dict[str, Any]
    created_at: str


def _clean_text(value: object) -> str:
    return " ".join(str(value or "").split())


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _optional_text(
    value: object,
    field_name: str,
    *,
    max_length: int = MAX_SHORT_TEXT_LENGTH,
) -> str | None:
    clean_value = _clean_text(value)

    if not clean_value:
        return None

    if len(clean_value) > max_length:
        raise MemoryValidationError(
            f"{field_name} must be under {max_length} characters."
        )

    is_safe, error_message = _check_input_safety(clean_value, field_name)
    if not is_safe:
        raise MemoryValidationError(error_message)

    return clean_value


def _required_text(
    value: object,
    field_name: str,
    *,
    max_length: int = MAX_SHORT_TEXT_LENGTH,
) -> str:
    clean_value = _optional_text(value, field_name, max_length=max_length)

    if not clean_value:
        raise MemoryValidationError(f"{field_name} is required.")

    return clean_value


def _split_items(value: object) -> list[str]:
    if isinstance(value, str):
        raw_items = value.replace("\n", ",").split(",")
    elif isinstance(value, list | tuple):
        raw_items = value
    else:
        raw_items = []

    items = []
    for item in raw_items:
        clean_item = _optional_text(
            item,
            "profile list item",
            max_length=MAX_LIST_ITEM_LENGTH,
        )
        if clean_item:
            items.append(clean_item)

    return items[:MAX_LIST_ITEMS]


def _require_items(value: object, field_name: str) -> list[str]:
    items = _split_items(value)

    if not items:
        raise MemoryValidationError(f"{field_name} is required.")

    return items


def _learning_time_minutes(profile: dict[str, Any]) -> int:
    raw_value = profile.get(
        "available_learning_time_minutes",
        profile.get("time_available_minutes"),
    )

    try:
        minutes = int(raw_value)
    except (TypeError, ValueError) as exc:
        raise MemoryValidationError(
            "available_learning_time_minutes must be an integer."
        ) from exc

    if minutes < 1 or minutes > MAX_LEARNING_TIME_MINUTES:
        raise MemoryValidationError(
            "available_learning_time_minutes must be between 1 and 480."
        )

    return minutes


def _clean_evidence_refs(
    evidence_refs: list[dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    clean_refs = []
    for evidence_ref in evidence_refs or []:
        if not isinstance(evidence_ref, dict):
            continue

        clean_refs.append(
            {
                str(key): value
                for key, value in evidence_ref.items()
                if str(key).lower() not in EVIDENCE_CONTENT_KEYS
            }
        )

    return clean_refs


def normalize_learner_profile(
    profile: dict[str, Any],
    raw_form: dict[str, Any] | None = None,
    learner_id: str | None = None,
) -> LearnerProfileSnapshot:
    """Normalize and validate learner profile data before persistence."""
    current_level = _required_text(profile.get("current_level"), "current_level")
    current_level = current_level.lower()

    if current_level not in CURRENT_LEVEL_OPTIONS:
        raise MemoryValidationError(
            "current_level must be beginner, intermediate, or advanced."
        )

    preferred_work_style = _required_text(
        profile.get("preferred_work_style"),
        "preferred_work_style",
    )
    if preferred_work_style not in PREFERRED_WORK_STYLES:
        raise MemoryValidationError(
            "preferred_work_style must be one of the guided options."
        )

    skills = _require_items(profile.get("skills", profile.get("current_skills")), "skills")
    interests = _require_items(profile.get("interests"), "interests")

    target_role = _optional_text(
        profile.get("target_role_or_direction", profile.get("target_role")),
        "target_role_or_direction",
    )

    normalized_profile: LearnerProfileSnapshot = {
        "entry_point": _optional_text(profile.get("entry_point"), "entry_point"),
        "current_level": current_level,
        "skills": skills,
        "interests": interests,
        "target_role_or_direction": target_role,
        "preferred_work_style": preferred_work_style,
        "available_learning_time_minutes": _learning_time_minutes(profile),
        "motivation": _optional_text(
            profile.get("motivation"),
            "motivation",
            max_length=MAX_LONG_TEXT_LENGTH,
        ),
        "constraints_blockers": _optional_text(
            profile.get("constraints_blockers"),
            "constraints_blockers",
            max_length=MAX_LONG_TEXT_LENGTH,
        ),
        "preferred_next_action": _optional_text(
            profile.get("preferred_next_action"),
            "preferred_next_action",
        ),
        "goal": _required_text(profile.get("goal"), "goal", max_length=MAX_GOAL_LENGTH),
        "raw_form": raw_form or {},
        "created_at": _optional_text(profile.get("created_at"), "created_at")
        or _utc_timestamp(),
    }

    if learner_id:
        normalized_profile["learner_id"] = _required_text(learner_id, "learner_id")

    return normalized_profile


def normalize_learning_event(
    *,
    learner_id: str,
    user_goal: str,
    event_type: str = "learning_event",
    profile_id: str | None = None,
    selected_focus: str | None = None,
    recommended_direction: str | None = None,
    recommendation: str | None = None,
    next_action: str | None = None,
    evidence_refs: list[dict[str, Any]] | None = None,
    decision_status: str | None = None,
    interaction_mode: str | None = None,
    decision_trace: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    created_at: str | None = None,
) -> LearningEvent:
    """Normalize and validate a learner memory event."""
    clean_trace = [
        trace_item
        for trace_item in (
            _optional_text(item, "decision_trace item", max_length=MAX_LONG_TEXT_LENGTH)
            for item in decision_trace or []
        )
        if trace_item
    ]

    normalized_event: LearningEvent = {
        "learner_id": _required_text(learner_id, "learner_id"),
        "profile_id": _optional_text(profile_id, "profile_id"),
        "event_type": _required_text(event_type, "event_type"),
        "user_goal": _required_text(user_goal, "user_goal", max_length=MAX_GOAL_LENGTH),
        "selected_focus": _optional_text(selected_focus, "selected_focus"),
        "recommended_direction": _optional_text(
            recommended_direction,
            "recommended_direction",
        ),
        "recommendation": _optional_text(
            recommendation,
            "recommendation",
            max_length=MAX_LONG_TEXT_LENGTH,
        ),
        "next_action": _optional_text(
            next_action,
            "next_action",
            max_length=MAX_LONG_TEXT_LENGTH,
        ),
        "decision_status": _optional_text(decision_status, "decision_status"),
        "interaction_mode": _optional_text(interaction_mode, "interaction_mode"),
        "evidence_refs": _clean_evidence_refs(evidence_refs),
        "decision_trace": clean_trace,
        "metadata": metadata or {},
        "created_at": _optional_text(created_at, "created_at") or _utc_timestamp(),
    }

    return normalized_event
