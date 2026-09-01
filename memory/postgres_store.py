"""PostgreSQL-backed learner memory store."""

from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from memory.schema import (
    MAX_EVENT_LIMIT,
    MEMORY_SCHEMA_SQL,
    OPTIONAL_MEMORY_EMBEDDINGS_SCHEMA_SQL,
    LearningEvent,
    LearnerProfileSnapshot,
    normalize_learning_event,
    normalize_learner_profile,
)

LOGGER = logging.getLogger(__name__)


class PostgresMemoryStore:
    """PostgreSQL MemoryStore implementation with soft failure behavior."""

    def __init__(self, database_url: str | None = None, engine: Engine | None = None):
        self._engine = engine
        self._database_url = database_url

    @property
    def engine(self) -> Engine | None:
        if self._engine is None and self._database_url:
            try:
                self._engine = create_engine(self._database_url, future=True)
            except Exception:
                LOGGER.exception("Failed to initialize learner memory database engine.")
                return None
        return self._engine

    def create_schema(self) -> bool:
        """Create the Phase 1 relational schema when a Postgres engine is available."""
        return self._execute_schema_sql(MEMORY_SCHEMA_SQL)

    def create_vector_schema(self) -> bool:
        """Create the optional pgvector memory table when pgvector is available."""
        return self._execute_schema_sql(OPTIONAL_MEMORY_EMBEDDINGS_SCHEMA_SQL)

    def _execute_schema_sql(self, schema_sql: str) -> bool:
        if self.engine is None:
            return False

        try:
            with self.engine.begin() as connection:
                for statement in schema_sql.split(";"):
                    if statement.strip():
                        connection.execute(text(statement))
            return True
        except Exception:
            LOGGER.exception("Failed to create learner memory schema.")
            return False

    def save_learner_profile(
        self,
        learner_id: str,
        profile: dict[str, Any],
        raw_form: dict[str, Any] | None = None,
    ) -> str | None:
        if self.engine is None:
            return None

        try:
            saved_profile = normalize_learner_profile(profile, raw_form)
            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO learners (id)
                        VALUES (:learner_id)
                        ON CONFLICT (id) DO UPDATE
                        SET updated_at = now()
                        """
                    ),
                    {"learner_id": learner_id},
                )
                profile_id = connection.execute(
                    text(
                        """
                        INSERT INTO learner_profiles (
                            learner_id,
                            entry_point,
                            current_level,
                            skills,
                            interests,
                            target_role_or_direction,
                            preferred_work_style,
                            available_learning_time_minutes,
                            motivation,
                            constraints_blockers,
                            preferred_next_action,
                            goal,
                            raw_form
                        )
                        VALUES (
                            :learner_id,
                            :entry_point,
                            :current_level,
                            CAST(:skills AS jsonb),
                            CAST(:interests AS jsonb),
                            :target_role_or_direction,
                            :preferred_work_style,
                            :available_learning_time_minutes,
                            :motivation,
                            :constraints_blockers,
                            :preferred_next_action,
                            :goal,
                            CAST(:raw_form AS jsonb)
                        )
                        RETURNING id
                        """
                    ),
                    {
                        **saved_profile,
                        "learner_id": learner_id,
                        "skills": json.dumps(saved_profile["skills"]),
                        "interests": json.dumps(saved_profile["interests"]),
                        "raw_form": json.dumps(saved_profile["raw_form"]),
                    },
                ).scalar_one()
            return str(profile_id)
        except Exception:
            LOGGER.exception("Failed to save learner profile.")
            return None

    def get_latest_learner_profile(
        self,
        learner_id: str,
    ) -> LearnerProfileSnapshot | None:
        if self.engine is None:
            return None

        try:
            with self.engine.begin() as connection:
                row = connection.execute(
                    text(
                        """
                        SELECT
                            learner_id,
                            entry_point,
                            current_level,
                            skills,
                            interests,
                            target_role_or_direction,
                            preferred_work_style,
                            available_learning_time_minutes,
                            motivation,
                            constraints_blockers,
                            preferred_next_action,
                            goal,
                            raw_form,
                            created_at
                        FROM learner_profiles
                        WHERE learner_id = :learner_id
                        ORDER BY created_at DESC
                        LIMIT 1
                        """
                    ),
                    {"learner_id": learner_id},
                ).mappings().first()

            if row is None:
                return None

            return LearnerProfileSnapshot(dict(row))
        except Exception:
            LOGGER.exception("Failed to fetch latest learner profile.")
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
        if self.engine is None:
            return None

        try:
            if learner_profile and not profile_id:
                profile_id = self.save_learner_profile(learner_id, learner_profile)

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

            with self.engine.begin() as connection:
                connection.execute(
                    text(
                        """
                        INSERT INTO learners (id)
                        VALUES (:learner_id)
                        ON CONFLICT (id) DO UPDATE
                        SET updated_at = now()
                        """
                    ),
                    {"learner_id": learner_id},
                )
                event_id = connection.execute(
                    text(
                        """
                        INSERT INTO learning_events (
                            learner_id,
                            profile_id,
                            event_type,
                            user_goal,
                            selected_focus,
                            recommended_direction,
                            recommendation,
                            next_action,
                            decision_status,
                            interaction_mode,
                            evidence_refs,
                            decision_trace,
                            metadata
                        )
                        VALUES (
                            :learner_id,
                            :profile_id,
                            :event_type,
                            :user_goal,
                            :selected_focus,
                            :recommended_direction,
                            :recommendation,
                            :next_action,
                            :decision_status,
                            :interaction_mode,
                            CAST(:evidence_refs AS jsonb),
                            CAST(:decision_trace AS jsonb),
                            CAST(:metadata AS jsonb)
                        )
                        RETURNING id
                        """
                    ),
                    {
                        **event,
                        "evidence_refs": json.dumps(event["evidence_refs"]),
                        "decision_trace": json.dumps(event["decision_trace"]),
                        "metadata": json.dumps(event["metadata"]),
                    },
                ).scalar_one()
            return str(event_id)
        except Exception:
            LOGGER.exception("Failed to save learning event.")
            return None

    def get_recent_learning_events(
        self,
        learner_id: str,
        limit: int = 10,
    ) -> list[LearningEvent]:
        if self.engine is None:
            return []

        capped_limit = min(max(int(limit), 0), MAX_EVENT_LIMIT)
        try:
            with self.engine.begin() as connection:
                rows = connection.execute(
                    text(
                        """
                        SELECT
                            learner_id,
                            profile_id,
                            event_type,
                            user_goal,
                            selected_focus,
                            recommended_direction,
                            recommendation,
                            next_action,
                            decision_status,
                            interaction_mode,
                            evidence_refs,
                            decision_trace,
                            metadata,
                            created_at
                        FROM learning_events
                        WHERE learner_id = :learner_id
                        ORDER BY created_at DESC
                        LIMIT :limit
                        """
                    ),
                    {"learner_id": learner_id, "limit": capped_limit},
                ).mappings()
                return [LearningEvent(dict(row)) for row in rows]
        except Exception:
            LOGGER.exception("Failed to fetch recent learning events.")
            return []

    def search_memory(
        self,
        learner_id: str,
        query: str,
        limit: int = 5,
    ) -> list[LearningEvent]:
        clean_query = " ".join(str(query or "").split())
        if not clean_query:
            return self.get_recent_learning_events(learner_id, limit)

        if self.engine is None:
            return []

        capped_limit = min(max(int(limit), 0), MAX_EVENT_LIMIT)
        try:
            with self.engine.begin() as connection:
                rows = connection.execute(
                    text(
                        """
                        SELECT
                            learner_id,
                            profile_id,
                            event_type,
                            user_goal,
                            selected_focus,
                            recommended_direction,
                            recommendation,
                            next_action,
                            decision_status,
                            interaction_mode,
                            evidence_refs,
                            decision_trace,
                            metadata,
                            created_at
                        FROM learning_events
                        WHERE learner_id = :learner_id
                        AND (
                            user_goal ILIKE :query
                            OR selected_focus ILIKE :query
                            OR recommended_direction ILIKE :query
                            OR recommendation ILIKE :query
                            OR next_action ILIKE :query
                        )
                        ORDER BY created_at DESC
                        LIMIT :limit
                        """
                    ),
                    {
                        "learner_id": learner_id,
                        "query": f"%{clean_query}%",
                        "limit": capped_limit,
                    },
                ).mappings()
                return [LearningEvent(dict(row)) for row in rows]
        except Exception:
            LOGGER.exception("Failed to search learner memory.")
            return self.get_recent_learning_events(learner_id, capped_limit)
