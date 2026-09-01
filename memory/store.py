"""MemoryStore protocol."""

from __future__ import annotations

from typing import Any, Protocol

from memory.schema import LearningEvent, LearnerProfileSnapshot


class MemoryStore(Protocol):
    """Small durable memory boundary used by app and graph code."""

    def save_learner_profile(
        self,
        learner_id: str,
        profile: dict[str, Any],
        raw_form: dict[str, Any] | None = None,
    ) -> str | None:
        """Persist one normalized learner profile snapshot."""

    def get_latest_learner_profile(
        self,
        learner_id: str,
    ) -> LearnerProfileSnapshot | None:
        """Return the newest profile snapshot for a learner."""

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
        """Append one learner memory event."""

    def get_recent_learning_events(
        self,
        learner_id: str,
        limit: int = 10,
    ) -> list[LearningEvent]:
        """Return recent learner memory events, newest first."""

    def search_memory(
        self,
        learner_id: str,
        query: str,
        limit: int = 5,
    ) -> list[LearningEvent]:
        """Search learner memory, falling back to simple local matching."""
