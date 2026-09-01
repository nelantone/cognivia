"""JSON export helpers for durable learner memory."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

EXPORT_VERSION = "learner_memory.v1"
EXPORT_NOTE = (
    "This file contains local Cognivia learner memory: profile snapshots and "
    "learning events. It is not a full chat transcript and does not include "
    "full retrieved document text."
)
EXCLUDED_EXPORT_KEYS = {
    "api_key",
    "authorization",
    "content",
    "document",
    "full_text",
    "openai_api_key",
    "openrouter_api_key",
    "page_content",
    "password",
    "secret",
    "text",
    "token",
}
EXCLUDED_EXPORT_KEY_PARTS = ("api_key", "authorization", "password", "secret", "token")


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_excluded_key(key: object) -> bool:
    clean_key = str(key).lower()
    return clean_key in EXCLUDED_EXPORT_KEYS or any(
        key_part in clean_key for key_part in EXCLUDED_EXPORT_KEY_PARTS
    )


def sanitize_memory_export_value(value: Any) -> Any:
    """Remove full text and secret-like fields from memory export values."""
    if isinstance(value, dict):
        return {
            str(key): sanitize_memory_export_value(item)
            for key, item in value.items()
            if not _is_excluded_key(key)
        }

    if isinstance(value, list | tuple):
        return [sanitize_memory_export_value(item) for item in value]

    if isinstance(value, datetime):
        return value.isoformat()

    return value


def build_learner_memory_export(
    *,
    learner_id: str,
    latest_profile: dict[str, Any] | None,
    recent_learning_events: list[dict[str, Any]] | None,
    exported_at: str | None = None,
) -> dict[str, Any]:
    """Build the safe learner-memory JSON export payload."""
    return {
        "export_version": EXPORT_VERSION,
        "exported_at": exported_at or _utc_timestamp(),
        "learner_id": learner_id,
        "latest_profile": sanitize_memory_export_value(latest_profile)
        if latest_profile
        else None,
        "recent_learning_events": sanitize_memory_export_value(
            recent_learning_events or []
        ),
        "note": EXPORT_NOTE,
    }


def learner_memory_export_to_json(payload: dict[str, Any]) -> str:
    """Serialize a learner-memory export payload for download."""
    return json.dumps(payload, default=str, indent=2, sort_keys=True)
