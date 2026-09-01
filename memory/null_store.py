"""No-op durable memory fallback."""

from __future__ import annotations

from typing import Any

from memory.schema import LearningEvent, LearnerProfileSnapshot


class NullMemoryStore:
    """MemoryStore implementation used when durable memory is unavailable."""

    def save_learner_profile(
        self,
        learner_id: str,
        profile: dict[str, Any],
        raw_form: dict[str, Any] | None = None,
    ) -> str | None:
        return None

    def get_latest_learner_profile(
        self,
        learner_id: str,
    ) -> LearnerProfileSnapshot | None:
        return None

    def save_learning_event(
        self,
        *,
        learner_id: str,
        user_goal: str,
        learner_profile: dict[str, Any] | None = None,
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
        event_type: str = "learning_event",
    ) -> str | None:
        return None

    def get_recent_learning_events(
        self,
        learner_id: str,
        limit: int = 10,
    ) -> list[LearningEvent]:
        return []

    def search_memory(
        self,
        learner_id: str,
        query: str,
        limit: int = 5,
    ) -> list[LearningEvent]:
        return []
