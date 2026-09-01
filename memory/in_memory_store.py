"""In-memory learner memory store for tests."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from memory.schema import (
    MAX_EVENT_LIMIT,
    LearningEvent,
    LearnerProfileSnapshot,
    normalize_learning_event,
    normalize_learner_profile,
)


class InMemoryMemoryStore:
    """Deterministic MemoryStore fake for tests and local wiring checks."""

    def __init__(self) -> None:
        self._profiles: dict[str, list[tuple[str, LearnerProfileSnapshot]]] = {}
        self._events: dict[str, list[tuple[str, LearningEvent]]] = {}

    def save_learner_profile(
        self,
        learner_id: str,
        profile: dict[str, Any],
        raw_form: dict[str, Any] | None = None,
    ) -> str | None:
        profile_id = str(uuid4())
        saved_profile = normalize_learner_profile(
            profile,
            raw_form,
            learner_id=learner_id,
        )
        self._profiles.setdefault(learner_id, []).append((profile_id, saved_profile))
        return profile_id

    def get_latest_learner_profile(
        self,
        learner_id: str,
    ) -> LearnerProfileSnapshot | None:
        profiles = self._profiles.get(learner_id, [])
        if not profiles:
            return None
        return profiles[-1][1]

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
        if learner_profile and not profile_id:
            profile_id = self.save_learner_profile(learner_id, learner_profile)

        event_id = str(uuid4())
        event = normalize_learning_event(
            learner_id=learner_id,
            profile_id=profile_id,
            event_type=event_type,
            user_goal=user_goal,
            selected_focus=selected_focus,
            recommended_direction=recommended_direction,
            recommendation=recommendation,
            next_action=next_action,
            evidence_refs=evidence_refs,
            decision_status=decision_status,
            interaction_mode=interaction_mode,
            decision_trace=decision_trace,
            metadata=metadata,
        )
        self._events.setdefault(learner_id, []).append((event_id, event))
        return event_id

    def get_recent_learning_events(
        self,
        learner_id: str,
        limit: int = 10,
    ) -> list[LearningEvent]:
        capped_limit = min(max(int(limit), 0), MAX_EVENT_LIMIT)
        if capped_limit == 0:
            return []

        events = self._events.get(learner_id, [])
        return [event for _, event in reversed(events[-capped_limit:])]

    def search_memory(
        self,
        learner_id: str,
        query: str,
        limit: int = 5,
    ) -> list[LearningEvent]:
        clean_query = " ".join(str(query or "").lower().split())
        if not clean_query:
            return self.get_recent_learning_events(learner_id, limit)

        capped_limit = min(max(int(limit), 0), MAX_EVENT_LIMIT)
        matches = []
        for event in self.get_recent_learning_events(learner_id, MAX_EVENT_LIMIT):
            searchable_text = " ".join(
                str(event.get(field) or "")
                for field in (
                    "user_goal",
                    "selected_focus",
                    "recommended_direction",
                    "recommendation",
                    "next_action",
                )
            ).lower()
            if clean_query in searchable_text:
                matches.append(event)

        return matches[:capped_limit]
