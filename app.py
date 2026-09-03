# ruff: noqa: E402  # The startup cover must precede heavier application imports.

import html
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from functools import partial
from pathlib import Path

from dotenv import load_dotenv

import streamlit as st

from frontend.assets import (
    FOCUS_MODE_ENTER_ICON_PATH,  # noqa: F401 (app-level compatibility re-export)
    FOCUS_MODE_EXIT_ICON_PATH,  # noqa: F401 (app-level compatibility re-export)
    NOISE_TO_SIGNAL_INTRO_VIDEO_PATH,
    NOISE_TO_SIGNAL_LOGO_PATH,
    _asset_data_uri,
)

NOISE_TO_SIGNAL_INTRO_STATE_SESSION_KEY = "noise_to_signal_intro_state"

st.set_page_config(initial_sidebar_state="collapsed")

# This is intentionally the first Streamlit delta. It bridges the browser's
# startup surface to the video without allowing later layout deltas to show.
_startup_intro_requested = (
    st.session_state.get(NOISE_TO_SIGNAL_INTRO_STATE_SESSION_KEY) != "complete"
    or st.query_params.get("intro") == "1"
)
if _startup_intro_requested:
    _startup_logo_uri = _asset_data_uri(NOISE_TO_SIGNAL_LOGO_PATH)
    _startup_logo_markup = (
        f'<img src="{html.escape(_startup_logo_uri, quote=True)}" '
        'alt="Cognivia">'
        if _startup_logo_uri
        else '<span class="cognivia-startup-wordmark">Cognivia</span>'
    )
    st.markdown(
        f"""
        <style>
            #cognivia-startup-intro-cover {{
                position: fixed;
                inset: 0;
                z-index: 100003;
                display: grid;
                place-items: center;
                overflow: hidden;
                background: #0B132B;
                opacity: 1;
                visibility: visible;
                pointer-events: auto;
                transition:
                    opacity 480ms cubic-bezier(0.22, 1, 0.36, 1),
                    visibility 0s linear 480ms;
            }}

            #cognivia-startup-intro-cover.is-releasing {{
                opacity: 0;
                visibility: hidden;
                pointer-events: none;
            }}

            #cognivia-startup-intro-cover img {{
                display: block;
                width: min(58vw, 360px);
                height: auto;
            }}

            .cognivia-startup-wordmark {{
                color: #F4F7FA;
                font: 600 clamp(2rem, 7vw, 4rem) / 1 sans-serif;
                letter-spacing: 0.08em;
            }}
        </style>
        <div id="cognivia-startup-intro-cover" aria-hidden="true">
            {_startup_logo_markup}
        </div>
        """,
        unsafe_allow_html=True,
    )

from frontend.browser.controllers import (
    _install_app_rerender_stability_guard,
    _render_noise_to_signal_control_accessibility,
    _render_noise_to_signal_intro_video_controller,
)
from frontend.browser.styles import (
    APP_RERENDER_STABILITY_CSS,  # noqa: F401 (app-level compatibility re-export)
    NOISE_TO_SIGNAL_HELPER_TEXT_COLOR,  # noqa: F401 (app-level compatibility re-export)
    _render_noise_to_signal_styles,
)
from frontend.interview_coach.view import (
    INTERVIEW_MAX_TOKENS_OVERRIDDEN_SESSION_KEY,  # noqa: F401 (compatibility re-export)
    INTERVIEW_MAX_TOKENS_SESSION_KEY,  # noqa: F401 (compatibility re-export)
    INTERVIEW_MODEL_OPTIONS,  # noqa: F401 (compatibility re-export)
    INTERVIEW_MODEL_SESSION_KEY,  # noqa: F401 (compatibility re-export)
    INTERVIEW_MODEL_TEMPERATURE_POLICY,  # noqa: F401 (compatibility re-export)
    _interview_default_max_tokens,  # noqa: F401 (compatibility re-export)
    _interview_request_kwargs,  # noqa: F401 (compatibility re-export)
    _mark_interview_max_tokens_overridden,  # noqa: F401 (compatibility re-export)
    _render_interview_coach,
    _synchronize_interview_max_tokens,  # noqa: F401 (compatibility re-export)
)
from frontend.runtime.drawer import (
    _render_noise_to_signal_runtime_drawer,
    _render_runtime_status,
    _render_runtime_technical_details,  # noqa: F401 (app-level compatibility re-export)
    _render_secondary_project_drawer,
    _runtime_drawer_markup,  # noqa: F401 (app-level compatibility re-export)
    _runtime_presentation_data,  # noqa: F401 (app-level compatibility re-export)
    _runtime_technical_details,  # noqa: F401 (app-level compatibility re-export)
    _secondary_runtime_markup,  # noqa: F401 (app-level compatibility re-export)
)
from frontend.skill_compass.view import (
    _render_ai_skill_compass as _render_ai_skill_compass_view,
    _validate_compass_input,
    _validate_compass_long_input,
)
from langsmith_config import configure_langsmith
from memory import (
    NullMemoryStore,
    PostgresMemoryStore,
    build_learner_memory_export,
    learner_memory_export_to_json,
)
from rag.config import DEFAULT_MIN_RELEVANCE_SCORE
from rag.retriever import retrieve_relevant_chunks
from tools.guided_intake import (
    CURRENT_LEVEL_OPTIONS,
    ENTRY_POINTS,
    PREFERRED_WORK_STYLES,
    build_guided_intake_query,
    build_guided_intake_recommendation,
    build_learner_profile,
)
from tools.learning_direction import (
    LearningDirectionSchema,
    generate_learning_direction_schemas,
)
from tools.learning_exports import (
    _learning_path_map_steps,  # noqa: F401 (app-level compatibility re-export)
    _markdown_list,  # noqa: F401 (app-level compatibility re-export)
    _markdown_text,  # noqa: F401 (app-level compatibility re-export)
    _time_available_today,  # noqa: F401 (app-level compatibility re-export)
    build_full_learning_plan_document,
    build_learning_reflection_markdown,
)
from tools.recommendation_explanations import (
    explain_career_path,
    explain_direction,
    explain_direction_fit,
    explain_skill_gap,
    first_action_for_direction,
)
from tools.noise_to_signal_graph import run_noise_to_signal
from tools.study_plan import (
    format_evidence_label,
)

# Optional LangSmith tracing is disabled by default.
load_dotenv()
configure_langsmith()

logger = logging.getLogger(__name__)

MEMORY_STORE_SESSION_KEY = "cognivia_memory_store"
DEMO_LEARNER_ID_SESSION_KEY = "cognivia_demo_learner_id"
GUIDED_RECOMMENDATION_SESSION_KEY = "noise_to_signal_guided_recommendation"
GUIDED_RECOMMENDATION_GOAL_SESSION_KEY = "noise_to_signal_guided_recommendation_goal"
LEARNING_DIRECTION_SCHEMAS_SESSION_KEY = "noise_to_signal_learning_direction_schemas"
LEARNING_DIRECTION_GOAL_SESSION_KEY = "noise_to_signal_learning_direction_goal"
SELECTED_LEARNING_SCHEMA_SESSION_KEY = "noise_to_signal_selected_learning_schema_id"
LEARNING_NOTE_EXPORT_SESSION_KEY = "noise_to_signal_learning_note_export"
FULL_LEARNING_PLAN_MARKDOWN_SESSION_KEY = "noise_to_signal_full_learning_plan_markdown"
FULL_LEARNING_PLAN_DOWNLOAD_LABEL = "Download full learning plan"
FULL_LEARNING_PLAN_FILE_NAME = "cognivia-learning-plan.md"
REFLECTION_MARKDOWN_FILE_NAME = "cognivia-reflection.md"
MARKDOWN_DOWNLOAD_MIME = "text/markdown"
NOISE_TO_SIGNAL_FOCUS_MODE_SESSION_KEY = "noise_to_signal_focus_mode"
NOISE_TO_SIGNAL_EXAMPLES_OPEN_SESSION_KEY = "noise_to_signal_examples_open"
NOISE_TO_SIGNAL_RESULT_FOCUS_SESSION_KEY = "noise_to_signal_result_focus_requested"
NOISE_TO_SIGNAL_PROCESSING_SESSION_KEY = "noise_to_signal_processing"
LEARNING_PATH_BEST_WHEN_MAX_CHARS = 110
LEARNING_PATH_STEP_LABEL_MAX_CHARS = 36
LEARNING_PATH_FIRST_ACTION_MAX_CHARS = 90
LEARNING_PATH_CHECKPOINT_MAX_CHARS = 90
LEARNING_PATH_RISK_MAX_CHARS = 90
LEARNING_PATH_DETAIL_MAX_CHARS = 180
LEARNING_PATH_MAX_STEPS = 4
MEMORY_EVIDENCE_REF_FIELDS = {
    "source",
    "title",
    "section",
    "page",
    "chunk_id",
    "chunk_index",
    "authority",
    "source_authority",
    "relevance_score",
    "source_type",
    "document_role",
}

APP_MODES = [
    "Noise-to-Signal Agent",
    "AI Skill Compass",
    "Interview Coach",
]
RUNTIME_DETAIL_SESSION_KEYS = (
    "runtime_details",
    "secondary_runtime_technical_details",
)


def _app_mode_label(mode: str) -> str:
    if mode == "Noise-to-Signal Agent":
        return "Cognivia — From noise to clarity"
    return mode


def _reset_runtime_detail_expansion() -> None:
    for key in RUNTIME_DETAIL_SESSION_KEYS:
        st.session_state.pop(key, None)


app_mode = st.sidebar.radio(
    "App Mode",
    APP_MODES,
    format_func=_app_mode_label,
    on_change=_reset_runtime_detail_expansion,
)


NOISE_TO_SIGNAL_STUDY_PLAN_FALLBACK_MESSAGES = {
    "needs_clarification": "No study plan was generated because more context is needed.",
    "informational": (
        "No study plan was generated because this was an informational question."
    ),
    "insufficient_evidence": (
        "No study plan was generated because the retrieved evidence does not "
        "directly support the question."
    ),
}
DEFAULT_NOISE_TO_SIGNAL_STUDY_PLAN_FALLBACK = (
    "No option-specific study plan was generated because the decision needs "
    "stronger evidence or clearer focus."
)
INSUFFICIENT_EVIDENCE_HEADING = (
    "Retrieved candidates — not sufficient to support the answer"
)
GUIDED_INTAKE_NO_EVIDENCE_HEADING = "Evidence status"
GUIDED_INTAKE_NO_EVIDENCE_MESSAGE = (
    "No knowledge-base evidence was attached to this guided recommendation.\n\n"
    "Treat this as a profile-based draft, not evidence-backed guidance."
)
LOCAL_EVIDENCE_STORE_BUSY_MESSAGE = (
    "The local evidence store is busy or unavailable. Try again after the "
    "current retrieval finishes."
)
EVIDENCE_RETRIEVAL_UNAVAILABLE_HEADING = "Evidence retrieval unavailable"
EVIDENCE_RETRIEVAL_UNAVAILABLE_MESSAGE = (
    "No embedding provider key is configured, so Cognivia cannot build or "
    "query the evidence index right now."
)
PROVIDER_NOT_CONFIGURED_HEADING = "Provider not configured"
PROVIDER_NOT_CONFIGURED_MESSAGE = (
    "The selected provider API key is missing. Cognivia will continue with "
    "deterministic guidance where possible."
)
NOISE_TO_SIGNAL_PROGRESS_MESSAGES = (
    "Searching local evidence. First run can take longer...",
    "Assessing whether the evidence directly supports this request...",
    "Preparing recommendation...",
)
DECISION_LABELS = {
    "needs_clarification": "Clarify",
    "informational": "Answered",
    "selected": "Selected",
    "insufficient_evidence": "Insufficient evidence",
}
EVIDENCE_LABELS = {
    "sufficient": "Sufficient",
    "contextual": "Contextual",
    "weak": "Limited",
    "failed": "Unavailable",
    "not_required": "Not needed",
}
MEMORY_EVENT_LABELS = {
    "guided_intake_recommendation": "Guided intake recommendation",
    "noise_to_signal_decision": "Noise-to-Signal decision",
    "learning_direction_generated": "Learning direction options",
    "learning_direction_selected": "Learning direction selected",
    "learning_note_saved": "Learning note",
    "study_plan_generated": "Study plan",
    "chat_followup": "Chat follow-up",
}
NOISE_TO_SIGNAL_EXAMPLE_PROMPTS = [
    "What should I learn next?",
    "Why is RAG evaluation useful for AI engineers?",
    "Should I learn LangGraph or RAG evaluation?",
    "How do I move from backend to AI engineering?",
]
NOISE_TO_SIGNAL_GUIDED_INTAKE_QUICK_PROMPT = "I don't know what to learn next"
NOISE_TO_SIGNAL_QUICK_PROMPTS = [
    NOISE_TO_SIGNAL_GUIDED_INTAKE_QUICK_PROMPT,
    "Should I learn LangGraph or RAG evaluation?",
    "Build a RAG roadmap",
    "Create a focused study plan",
    "Explain LangGraph",
]
LEARNING_OR_AI_CAREER_PROMPT_TERMS = {
    "ai engineer",
    "ai engineering",
    "agent",
    "agents",
    "career",
    "embedding",
    "embeddings",
    "evaluation",
    "interview",
    "job",
    "langgraph",
    "learn",
    "learning",
    "llm",
    "portfolio",
    "rag",
    "retrieval",
    "roadmap",
    "skill",
    "skills",
    "study",
    "vector database",
    "vector databases",
}
CLEAR_OUT_OF_SCOPE_PROMPT_TERMS = {
    "buy",
    "capital of",
    "deal",
    "deals",
    "football",
    "movie",
    "price",
    "recipe",
    "restaurant",
    "score",
    "scores",
    "shopping",
    "song",
    "taco",
    "tacos",
    "trivia",
    "weather",
    "who won",
}
OUT_OF_SCOPE_LEARNING_PATH_MESSAGE = (
    "No useful AI learning signal was detected for this prompt. Ask an AI "
    "learning, career, or study question to generate learning paths."
)
ENABLE_PIKO_IRI_TIPS = True
NOISE_TO_SIGNAL_SUBTITLE = (
    "Your AI learning compass — think clearly, learn intentionally."
)


def _noise_to_signal_study_plan_fallback_message(decision_status):
    return NOISE_TO_SIGNAL_STUDY_PLAN_FALLBACK_MESSAGES.get(
        decision_status,
        DEFAULT_NOISE_TO_SIGNAL_STUDY_PLAN_FALLBACK,
    )


def _should_display_noise_to_signal_evidence(decision_status):
    return decision_status != "needs_clarification"


def _noise_to_signal_evidence_heading(decision_status):
    if decision_status == "insufficient_evidence":
        return INSUFFICIENT_EVIDENCE_HEADING

    return "Retrieved evidence"


def _noise_to_signal_progress_messages():
    return NOISE_TO_SIGNAL_PROGRESS_MESSAGES


def is_learning_or_ai_career_prompt(prompt: object) -> bool:
    """Conservatively identify prompts that should receive learning paths."""
    clean_prompt = " ".join(str(prompt or "").lower().split())
    if not clean_prompt:
        return False

    if any(term in clean_prompt for term in LEARNING_OR_AI_CAREER_PROMPT_TERMS):
        return True

    if any(term in clean_prompt for term in CLEAR_OUT_OF_SCOPE_PROMPT_TERMS):
        return False

    return True


def _is_local_evidence_store_lock_error(error: Exception) -> bool:
    return "already accessed by another instance of qdrant client" in str(error).lower()


def _is_provider_configuration_error(error: Exception) -> bool:
    message = str(error).lower()
    return (
        "api key is missing" in message
        or "provider selected but" in message
        or "unsupported provider" in message
    )


def _render_provider_configuration_warning() -> None:
    st.warning(f"**{PROVIDER_NOT_CONFIGURED_HEADING}**")
    st.info(PROVIDER_NOT_CONFIGURED_MESSAGE)
    st.warning(f"**{EVIDENCE_RETRIEVAL_UNAVAILABLE_HEADING}**")
    st.info(EVIDENCE_RETRIEVAL_UNAVAILABLE_MESSAGE)


def _display_value(value):
    if value is None:
        return None
    if isinstance(value, str):
        clean_value = value.strip()
        return clean_value or None
    if isinstance(value, (list, tuple, set, dict)) and not value:
        return None
    return value


def _format_status_label(value, labels, default="Unknown"):
    display_value = _display_value(value)
    if display_value is None:
        return default
    if isinstance(display_value, str):
        return labels.get(
            display_value,
            display_value.replace("_", " ").strip().title() or default,
        )
    return str(display_value)


def _write_if_present(value, empty_message=None):
    display_value = _display_value(value)
    if display_value is None:
        if empty_message:
            st.info(empty_message)
        return False
    st.write(display_value)
    return True


def get_memory_store():
    """Return the configured learner memory store or a safe no-op fallback."""
    if MEMORY_STORE_SESSION_KEY in st.session_state:
        return st.session_state[MEMORY_STORE_SESSION_KEY]

    database_url = os.getenv("DATABASE_URL")
    store = PostgresMemoryStore(database_url) if database_url else NullMemoryStore()
    st.session_state[MEMORY_STORE_SESSION_KEY] = store
    return store


def get_or_create_demo_learner_id() -> str:
    """Return a stable local demo learner ID for the current Streamlit session."""
    learner_id = st.session_state.get(DEMO_LEARNER_ID_SESSION_KEY)
    if not learner_id:
        learner_id = str(uuid.uuid4())
        st.session_state[DEMO_LEARNER_ID_SESSION_KEY] = learner_id
    return learner_id


def build_evidence_refs(evidence_items):
    """Build memory-safe evidence references without storing full evidence text."""
    evidence_refs = []
    for item in evidence_items or []:
        if not isinstance(item, dict):
            continue

        evidence_ref = {
            field: item[field]
            for field in MEMORY_EVIDENCE_REF_FIELDS
            if item.get(field) is not None
        }
        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        if "chunk_id" not in evidence_ref and metadata.get("chunk_id") is not None:
            evidence_ref["chunk_id"] = metadata["chunk_id"]
        if "authority" not in evidence_ref and item.get("source_authority") is not None:
            evidence_ref["authority"] = item["source_authority"]

        if evidence_ref:
            evidence_refs.append(evidence_ref)

    return evidence_refs


def _save_guided_intake_memory(recommendation, interaction_mode):
    learner_id = get_or_create_demo_learner_id()
    store = get_memory_store()
    learner_profile = recommendation["learner_profile"]
    evidence_refs = build_evidence_refs(recommendation.get("evidence_used"))

    try:
        profile_id = store.save_learner_profile(
            learner_id,
            learner_profile,
            raw_form=learner_profile,
        )
        store.save_learning_event(
            learner_id=learner_id,
            event_type="guided_intake_recommendation",
            user_goal=learner_profile["goal"],
            learner_profile=learner_profile,
            profile_id=profile_id,
            recommended_direction=recommendation.get("recommended_direction"),
            recommendation=recommendation.get("recommended_direction"),
            next_action=recommendation.get("next_action"),
            evidence_refs=evidence_refs,
            interaction_mode=interaction_mode,
            metadata={
                "profile_id": profile_id,
                "possible_ai_career_paths": recommendation.get(
                    "possible_ai_career_paths",
                    [],
                ),
                "skill_gap": recommendation.get("skill_gap", []),
            },
        )
    except Exception:
        logger.exception("Failed to persist guided intake learner memory.")


def _should_save_noise_to_signal_memory(decision) -> bool:
    if decision.get("interaction_mode") == "guided_intake":
        return False
    if decision.get("decision_status") == "needs_clarification":
        return False
    return bool(_display_value(decision.get("recommendation")) or decision.get("next_action"))


def _save_noise_to_signal_memory(decision, user_goal=None):
    if not _should_save_noise_to_signal_memory(decision):
        return

    learner_id = get_or_create_demo_learner_id()
    store = get_memory_store()
    evidence_refs = build_evidence_refs((decision.get("evidence") or {}).get("items"))

    try:
        store.save_learning_event(
            learner_id=learner_id,
            event_type="noise_to_signal_decision",
            user_goal=decision.get("goal") or user_goal or "",
            selected_focus=decision.get("selected_focus"),
            recommended_direction=decision.get("selected_focus"),
            recommendation=decision.get("recommendation"),
            next_action=decision.get("next_action"),
            evidence_refs=evidence_refs,
            decision_status=decision.get("decision_status"),
            interaction_mode=decision.get("interaction_mode"),
            decision_trace=decision.get("decision_trace") or [],
            metadata={
                "evidence_quality": decision.get("evidence_quality"),
                "retrieval_attempts": decision.get("retrieval_attempts"),
                "query_reformulated": decision.get("query_reformulated"),
            },
        )
    except Exception:
        logger.exception("Failed to persist Noise-to-Signal learner memory.")


def _learning_direction_event_payload(
    schema: LearningDirectionSchema,
    goal: str,
    event_type: str,
    *,
    generated_schemas: list[LearningDirectionSchema] | None = None,
    note_title: str | None = None,
    note_body: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, object]:
    metadata: dict[str, object] = {}
    if generated_schemas is None:
        metadata["schema"] = schema
    else:
        metadata["schemas"] = generated_schemas
        metadata["schema_ids"] = [item["id"] for item in generated_schemas]
        metadata["schema_count"] = len(generated_schemas)
    if note_title:
        metadata["note_title"] = note_title
    if note_body:
        metadata["note_body"] = note_body
    if tags:
        metadata["tags"] = tags

    recommendation = schema["fit_reason"]
    if note_title:
        recommendation = f"{note_title}: {schema['fit_reason']}"

    return {
        "learner_id": get_or_create_demo_learner_id(),
        "event_type": event_type,
        "user_goal": goal,
        "selected_focus": schema["title"],
        "recommended_direction": schema["title"],
        "recommendation": recommendation,
        "next_action": schema["first_action"],
        "interaction_mode": "learning_direction_schema",
        "decision_trace": [
            f"Learning direction schema: {schema['title']}",
        ],
        "metadata": metadata,
    }


def _save_learning_direction_event(
    schema: LearningDirectionSchema,
    goal: str,
    event_type: str,
    *,
    generated_schemas: list[LearningDirectionSchema] | None = None,
    note_title: str | None = None,
    note_body: str | None = None,
    tags: list[str] | None = None,
) -> bool:
    store = get_memory_store()

    try:
        store.save_learning_event(
            **_learning_direction_event_payload(
                schema,
                goal,
                event_type,
                generated_schemas=generated_schemas,
                note_title=note_title,
                note_body=note_body,
                tags=tags,
            )
        )
    except Exception:
        logger.exception("Failed to persist learning direction memory.")
        return False

    return True


def _save_learning_direction_generated_once(
    schemas: list[LearningDirectionSchema],
    goal: str,
) -> None:
    if not schemas:
        return

    generation_key = "noise_to_signal_learning_direction_generated_for"
    if st.session_state.get(generation_key) == goal:
        return

    st.session_state[generation_key] = goal
    _save_learning_direction_event(
        schemas[0],
        goal,
        "learning_direction_generated",
        generated_schemas=schemas,
    )


def _clear_learning_direction_state() -> None:
    st.session_state.pop(LEARNING_DIRECTION_SCHEMAS_SESSION_KEY, None)
    st.session_state.pop(LEARNING_DIRECTION_GOAL_SESSION_KEY, None)
    st.session_state.pop(SELECTED_LEARNING_SCHEMA_SESSION_KEY, None)
    st.session_state.pop("noise_to_signal_learning_direction_generated_for", None)
    st.session_state.pop("noise_to_signal_learning_note_title", None)
    st.session_state.pop("noise_to_signal_learning_note_body", None)
    st.session_state.pop("noise_to_signal_learning_note_tags", None)
    st.session_state.pop(LEARNING_NOTE_EXPORT_SESSION_KEY, None)
    st.session_state.pop(FULL_LEARNING_PLAN_MARKDOWN_SESSION_KEY, None)


def _clear_guided_recommendation_state() -> None:
    st.session_state.pop(GUIDED_RECOMMENDATION_SESSION_KEY, None)
    st.session_state.pop(GUIDED_RECOMMENDATION_GOAL_SESSION_KEY, None)


def _store_learning_direction_schemas(
    schemas: list[LearningDirectionSchema],
    goal: str,
) -> list[LearningDirectionSchema]:
    stored_goal = st.session_state.get(LEARNING_DIRECTION_GOAL_SESSION_KEY)
    if stored_goal != goal:
        _clear_learning_direction_state()

    st.session_state[LEARNING_DIRECTION_GOAL_SESSION_KEY] = goal
    st.session_state[LEARNING_DIRECTION_SCHEMAS_SESSION_KEY] = schemas
    return schemas


def _learner_memory_snapshot(limit=5):
    """Read learner memory for display/export without making memory required."""
    learner_id = get_or_create_demo_learner_id()
    store = get_memory_store()

    try:
        latest_profile = store.get_latest_learner_profile(learner_id)
        events = store.get_recent_learning_events(learner_id, limit=limit)
    except Exception:
        logger.exception("Failed to read learner memory history.")
        return learner_id, None, []

    return learner_id, latest_profile, events


def _memory_event_label(event):
    return _format_status_label(
        event.get("event_type"),
        MEMORY_EVENT_LABELS,
        default="Learning event",
    )


def _memory_event_timestamp(event):
    created_at = _display_value(event.get("created_at"))
    if not isinstance(created_at, str):
        return created_at
    return created_at.replace("T", " ").replace("+00:00", " UTC")


def _memory_event_direction(event):
    return _display_value(event.get("recommended_direction")) or _display_value(
        event.get("selected_focus")
    )


def _memory_event_note_title(event):
    metadata = event.get("metadata") if isinstance(event.get("metadata"), dict) else {}
    return _display_value(metadata.get("note_title"))


def _render_learner_memory_history():
    learner_id, latest_profile, events = _learner_memory_snapshot(limit=5)
    if not latest_profile and not events:
        return

    latest_event = events[0] if events else {}
    latest_direction = _memory_event_direction(latest_event)
    latest_next_action = _display_value(latest_event.get("next_action"))

    st.subheader("Learner memory")
    if latest_direction or latest_next_action:
        st.markdown("**Current direction**")
        if latest_direction:
            st.write(latest_direction)
        if latest_next_action:
            st.caption("Next action")
            st.write(latest_next_action)

    if events:
        with st.expander(
            "Recent learning history",
            key="recent_learning_history",
            on_change="ignore",
        ):
            for event in events:
                label = _memory_event_label(event)
                timestamp = _memory_event_timestamp(event)
                user_goal = _display_value(event.get("user_goal"))
                direction = _memory_event_direction(event)
                next_action = _display_value(event.get("next_action"))
                note_title = _memory_event_note_title(event)

                st.markdown(f"**{label}**")
                if timestamp:
                    st.caption(str(timestamp))
                if user_goal:
                    st.write(f"Goal: {user_goal}")
                if direction:
                    st.write(f"Direction: {direction}")
                if note_title:
                    st.write(f"Note: {note_title}")
                if next_action:
                    st.write(f"Next action: {next_action}")

    export_payload = build_learner_memory_export(
        learner_id=learner_id,
        latest_profile=latest_profile,
        recent_learning_events=events,
    )
    st.download_button(
        "Download learner memory JSON",
        data=learner_memory_export_to_json(export_payload),
        file_name="cognivia-learner-memory.json",
        mime="application/json",
        key="download_learner_memory_json",
    )


def _noise_to_signal_recommendation_text(decision):
    recommendation = _display_value(decision.get("recommendation"))
    evidence_reason = _display_value(decision.get("evidence_reason"))
    selected_focus = _display_value(decision.get("selected_focus"))

    if (
        decision.get("decision_status") == "insufficient_evidence"
        and selected_focus is None
        and evidence_reason
        and "outside the ai engineering learning scope" in evidence_reason.lower()
    ):
        return evidence_reason

    return recommendation


def _render_noise_to_signal_header() -> None:
    logo_uri = (
        _asset_data_uri(NOISE_TO_SIGNAL_LOGO_PATH)
        if NOISE_TO_SIGNAL_LOGO_PATH is not None
        else None
    )

    with st.container(key="noise_to_signal_header"):
        if logo_uri:
            brand_markup = (
                '<div class="nts-brand">'
                f'<img src="{logo_uri}" alt="Cognivia logo">'
                "</div>"
            )
        else:
            brand_markup = (
                '<div class="nts-brand">'
                '<div class="nts-brand-fallback">Cognivia</div>'
                "</div>"
            )

        st.markdown(brand_markup, unsafe_allow_html=True)

        st.markdown(
            f'<div class="nts-brand-tagline">'
            f"{html.escape(NOISE_TO_SIGNAL_SUBTITLE)}</div>",
            unsafe_allow_html=True,
        )


def _render_noise_to_signal_metrics(decision):
    decision_label = _format_status_label(
        decision.get("decision_status"),
        DECISION_LABELS,
    )
    evidence_label = _format_status_label(
        decision.get("evidence_quality"),
        EVIDENCE_LABELS,
    )
    retrieval_attempts = _display_value(decision.get("retrieval_attempts"))
    selected_focus = _display_value(decision.get("selected_focus")) or "Not needed"

    if (
        decision_label == "Unknown"
        and evidence_label == "Unknown"
        and retrieval_attempts is None
        and selected_focus == "Not needed"
    ):
        return

    with st.expander(
        "Why Cognivia recommended this",
        expanded=False,
        key="noise_to_signal_recommendation_reasoning",
        on_change="ignore",
    ):
        st.caption("Decision")
        st.markdown(f"**{decision_label}**")
        st.caption("Evidence")
        st.markdown(f"**{evidence_label}**")
        st.caption("Selected focus")
        st.markdown(f"**{selected_focus}**")
        st.caption("Retrieval attempts")
        attempt_label = retrieval_attempts if retrieval_attempts is not None else "Not run"
        st.markdown(f"**{attempt_label}**")


def _render_noise_to_signal_retrieval_warning(decision):
    if decision.get("retrieval_error") == "local_evidence_store_locked":
        st.warning(LOCAL_EVIDENCE_STORE_BUSY_MESSAGE)
    if decision.get("retrieval_error") == "provider_configuration_unavailable":
        _render_provider_configuration_warning()


def _render_noise_to_signal_evidence(decision):
    if not _should_display_noise_to_signal_evidence(decision.get("decision_status")):
        return

    evidence = decision.get("evidence") or {}
    items = evidence.get("items") or []
    evidence_heading = _noise_to_signal_evidence_heading(
        decision.get("decision_status")
    )
    with st.expander(
        evidence_heading,
        key="noise_to_signal_evidence",
        on_change="ignore",
    ):
        if items:
            for index, item in enumerate(items, start=1):
                evidence_label = format_evidence_label(item)
                with st.expander(
                    f"Evidence {index}: {evidence_label}",
                    key=f"noise_to_signal_evidence_item_{index}",
                    on_change="ignore",
                ):
                    type_label = _display_value(item.get("type_label"))
                    page = _display_value(item.get("page"))
                    excerpt = _display_value(item.get("excerpt"))
                    if type_label:
                        st.caption(f"Type: {type_label}")
                    if page is not None:
                        st.caption(f"Page: {page}")
                    if excerpt:
                        st.text(excerpt)
                    else:
                        st.info("No excerpt is available for this evidence item.")
        else:
            st.info("No relevant evidence was retrieved from the knowledge base.")


def _render_noise_to_signal_study_plan(decision, study_plan):
    if study_plan and _display_value(study_plan.get("plan")):
        plan_text = study_plan["plan"]
        if len(plan_text) > 700:
            with st.expander(
                "Focused study sprint",
                key="noise_to_signal_focused_study_sprint",
                on_change="ignore",
            ):
                st.write(plan_text)
        else:
            st.subheader("Focused study sprint")
            st.write(plan_text)
        return


def _short_summary_text(value: object, fallback: str) -> str:
    clean_value = _display_value(value)
    if not clean_value:
        return fallback

    first_sentence = clean_value.split(". ", 1)[0].strip()
    if first_sentence and not first_sentence.endswith((".", "!", "?")):
        first_sentence = f"{first_sentence}."
    return first_sentence or fallback


def _noise_to_signal_reason(decision) -> str | None:
    trace = decision.get("decision_trace") or []
    return next(
        (
            item.removeprefix("Short evidence-based reasoning:").strip()
            for item in trace
            if isinstance(item, str)
            and item.startswith("Short evidence-based reasoning:")
        ),
        None,
    )


def _helper_tip_markup(character: str, text: str) -> str:
    if not ENABLE_PIKO_IRI_TIPS:
        return ""

    icon_files = {
        "piko": Path("assets/piko.png"),
        "iri": Path("assets/iri.png"),
    }
    character_key = character.lower()
    label = "Piko" if character_key == "piko" else "Iri"
    icon_uri = _asset_data_uri(icon_files.get(character_key, icon_files["iri"]))
    icon_markup = (
        '<img '
        f'src="{html.escape(icon_uri, quote=True)}" '
        f'alt="{label}" '
        'style="width:32px;height:32px;object-fit:contain;flex:0 0 auto;">'
        if icon_uri
        else ""
    )
    return (
        '<div class="nts-helper-tip" '
        'style="display:flex;align-items:center;gap:0.45rem;'
        'margin:0.35rem 0 0.1rem;color:var(--nts-helper-text);'
        'font-size:0.86rem;line-height:1.35;">'
        f"{icon_markup}"
        f'<span><strong>{label} tip:</strong> {html.escape(text)}</span>'
        "</div>"
    )


def _render_helper_tip(character: str, text: str) -> None:
    markup = _helper_tip_markup(character, text)
    if markup:
        st.markdown(markup, unsafe_allow_html=True)


def _render_recommendation_summary(
    direction: object,
    reason: object,
    next_action: object,
    *,
    key: str = "noise_to_signal_recommendation_summary",
    show_piko_tip: bool = True,
) -> None:
    clean_direction = _display_value(direction) or "Next learning direction"
    summary_reason = _short_summary_text(
        reason,
        "Cognivia used the available learner context and evidence signals to size the next step.",
    )
    clean_next_action = _display_value(next_action) or "Choose one of the learning paths below."

    with st.container(key=key):
        st.subheader("Recommendation summary")
        st.markdown(f"**Direction:** {clean_direction}")
        st.markdown(f"**Why:** {summary_reason}")
        st.markdown(f"**Next:** {clean_next_action}")
        if show_piko_tip:
            _render_helper_tip(
                "piko",
                "Turn this recommendation into one small study task for today.",
            )


def _render_results_compact_callout(message: str) -> None:
    st.markdown(
        f'<div class="nts-results-compact-callout">{html.escape(message)}</div>',
        unsafe_allow_html=True,
    )


def _render_guided_intake_context_callout(placeholder) -> None:
    placeholder.markdown(
        """
        <div class="nts-results-compact-callout">
            <strong>A little more context is needed</strong><br>
            Add your current level, skills, interests, work style, target role,
            and available learning time.
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_out_of_scope_learning_path_empty_state() -> None:
    _render_results_compact_callout(OUT_OF_SCOPE_LEARNING_PATH_MESSAGE)


def _render_guided_intake_evidence(recommendation):
    evidence_used = recommendation["evidence_used"]

    if not evidence_used:
        st.subheader(GUIDED_INTAKE_NO_EVIDENCE_HEADING)
        st.info(GUIDED_INTAKE_NO_EVIDENCE_MESSAGE)
        return

    st.subheader("Evidence used")
    st.write(recommendation["evidence_note"])
    for index, item in enumerate(evidence_used, start=1):
        evidence_label = format_evidence_label(item)
        with st.expander(
            f"Evidence {index}: {evidence_label}",
            key=f"noise_to_signal_guided_evidence_item_{index}",
            on_change="ignore",
        ):
            type_label = item.get("type_label")
            page = item.get("page")
            excerpt = item.get("excerpt")

            if type_label:
                st.caption(f"Type: {type_label}")
            if page is not None:
                st.caption(f"Page: {page}")
            if excerpt:
                st.text(excerpt)
            else:
                st.info("No excerpt is available for this evidence item.")


def _render_recommended_direction(
    title: object,
    *,
    why_this_fits: object = None,
    first_action: object = None,
) -> None:
    clean_title = _display_value(title)
    if not clean_title:
        return

    st.subheader("Recommended direction")
    st.markdown(f"**{clean_title}**")
    st.caption("What this means")
    st.write(explain_direction(clean_title))
    st.caption("Why this fits")
    st.write(_display_value(why_this_fits) or explain_direction_fit(clean_title))
    st.caption("First action")
    st.write(first_action_for_direction(clean_title, first_action))


def _render_career_path_explanations(career_paths) -> None:
    visible_paths = [
        career_path
        for career_path in career_paths or []
        if _display_value(career_path)
    ]
    if not visible_paths:
        return

    st.subheader("Possible AI career paths")
    for career_path in visible_paths:
        clean_path = _display_value(career_path)
        st.markdown(f"**{clean_path}**")
        st.write(explain_career_path(clean_path))


def _render_skill_gap_explanations(skills) -> None:
    visible_skills = [skill for skill in skills or [] if _display_value(skill)]
    if not visible_skills:
        return

    st.subheader("Skill gaps to practice")
    for skill in visible_skills:
        clean_skill = _display_value(skill)
        st.markdown(f"**{clean_skill}**")
        st.write(explain_skill_gap(clean_skill))


def _render_guided_intake_recommendation(
    recommendation,
    next_action_heading="Next guided action",
):
    goal = _display_value(recommendation["learner_profile"].get("goal")) or ""
    schemas = _prepare_learning_direction_schemas(recommendation, goal)
    guided_reason = (
        "This fits the learner profile and turns the intake answers into "
        "a concrete AI engineering direction."
    )
    summary_values = _learning_direction_summary_values(
        schemas,
        fallback_direction=recommendation.get("recommended_direction"),
        fallback_reason=guided_reason,
        fallback_next_action=recommendation.get("next_action"),
    )

    _render_recommendation_summary(
        *summary_values,
        key="noise_to_signal_guided_recommendation_summary",
    )

    overview_tab, paths_tab, note_tab, technical_tab = st.tabs(
        ["Overview", "Learning paths", "Study note", "Evidence / technical"]
    )

    with overview_tab:
        _render_recommended_direction(
            recommendation.get("recommended_direction"),
            why_this_fits=guided_reason,
            first_action=recommendation.get("next_action"),
        )
        _render_career_path_explanations(recommendation.get("possible_ai_career_paths"))
        _render_skill_gap_explanations(recommendation.get("skill_gap"))

        st.subheader("Learning path outline")
        for index, step in enumerate(recommendation["learning_path_outline"], start=1):
            st.write(f"{index}. {step}")

        st.subheader(next_action_heading)
        st.write(recommendation["next_action"])

    with paths_tab:
        _render_learning_direction_schema_options(schemas, goal)

    with note_tab:
        _render_learning_direction_note_form(schemas, goal, recommendation)

    with technical_tab:
        with st.expander(
            "View captured learner profile JSON",
            expanded=False,
            key="noise_to_signal_guided_profile_json",
            on_change="ignore",
        ):
            st.caption("Captured learner profile JSON")
            st.json(recommendation["learner_profile"])
        _render_guided_intake_evidence(recommendation)


def _limit_learning_path_text(value: object, max_chars: int) -> str:
    """Normalize whitespace and shorten text without splitting a word."""
    clean_value = " ".join(str(value or "").split())
    if len(clean_value) <= max_chars:
        return clean_value

    available_chars = max(1, max_chars - 1)
    retained_words: list[str] = []
    retained_length = 0
    for word in clean_value.split():
        separator_length = 1 if retained_words else 0
        if retained_length + separator_length + len(word) > available_chars:
            break
        retained_words.append(word)
        retained_length += separator_length + len(word)

    if not retained_words:
        return "…"
    retained_text = " ".join(retained_words).rstrip(" ,;:-.")
    return f"{retained_text}…"


def _normalize_learning_direction_for_display(
    schema: LearningDirectionSchema,
) -> dict[str, object]:
    """Create a bounded presentation view without changing the stored schema."""
    best_when = " ".join(str(schema["fit_reason"] or "").split())
    if best_when.casefold().startswith("best when"):
        best_when = best_when[len("best when") :].lstrip(" :—-")

    steps: list[str] = []
    seen_steps: set[str] = set()
    for node in schema["nodes"]:
        compact_node = _limit_learning_path_text(
            node,
            LEARNING_PATH_STEP_LABEL_MAX_CHARS,
        )
        normalized_node = compact_node.casefold()
        if compact_node and normalized_node not in seen_steps:
            steps.append(compact_node)
            seen_steps.add(normalized_node)
        if len(steps) == LEARNING_PATH_MAX_STEPS:
            break

    compact_values = {
        *steps,
        _limit_learning_path_text(
            schema["first_action"],
            LEARNING_PATH_FIRST_ACTION_MAX_CHARS,
        ),
        _limit_learning_path_text(
            schema["checkpoint"],
            LEARNING_PATH_CHECKPOINT_MAX_CHARS,
        ),
        _limit_learning_path_text(
            schema["risk_or_gap"],
            LEARNING_PATH_RISK_MAX_CHARS,
        ),
    }
    detail_candidates = (
        ("Starting context", schema["current_state"]),
        ("Intended outcome", schema["target_outcome"]),
    )
    details = [
        (label, detail)
        for label, value in detail_candidates
        if (
            detail := _limit_learning_path_text(
                value,
                LEARNING_PATH_DETAIL_MAX_CHARS,
            )
        )
        and detail not in compact_values
    ]

    return {
        "best_when": _limit_learning_path_text(
            best_when,
            LEARNING_PATH_BEST_WHEN_MAX_CHARS,
        ),
        "steps": steps,
        "first_action": _limit_learning_path_text(
            schema["first_action"],
            LEARNING_PATH_FIRST_ACTION_MAX_CHARS,
        ),
        "checkpoint": _limit_learning_path_text(
            schema["checkpoint"],
            LEARNING_PATH_CHECKPOINT_MAX_CHARS,
        ),
        "risk": _limit_learning_path_text(
            schema["risk_or_gap"],
            LEARNING_PATH_RISK_MAX_CHARS,
        ),
        "details": details,
    }


def _render_learning_direction_schema(schema: LearningDirectionSchema) -> None:
    compact = _normalize_learning_direction_for_display(schema)
    st.markdown(f"**Best when:** {compact['best_when']}")
    _render_learning_path_map(compact["steps"])
    st.markdown(f"**First action:** {compact['first_action']}")
    st.markdown(f"**Checkpoint:** {compact['checkpoint']}")
    st.markdown(f"**Risk:** {compact['risk']}")

    details = compact["details"]
    if details:
        _render_learning_path_details(schema["id"], details)


def _render_learning_path_details(
    schema_id: str,
    details: list[tuple[str, str]],
) -> None:
    """Render text-only path details without a Streamlit widget lifecycle."""
    escaped_schema_id = html.escape(str(schema_id), quote=True)
    rendered_details = "".join(
        (
            "<li>"
            f"<strong>{html.escape(label)}:</strong> {html.escape(value)}"
            "</li>"
        )
        for label, value in details
    )
    st.markdown(
        '<details class="nts-learning-path-details" '
        f'id="noise-to-signal-learning-path-details-{escaped_schema_id}" '
        f'data-cognivia-learning-path-details="{escaped_schema_id}">'
        "<summary>See step details</summary>"
        f'<ul class="nts-learning-path-detail-list">{rendered_details}</ul>'
        "</details>",
        unsafe_allow_html=True,
    )


def _render_learning_path_map(steps: list[str]) -> None:
    """Render a compact, deterministic visual map for one learning path."""
    rendered_steps = []
    step_count = len(steps)
    for index, step in enumerate(steps, start=1):
        escaped_step = html.escape(step)
        accessible_label = html.escape(
            f"Step {index} of {step_count}: {step}",
            quote=True,
        )
        rendered_steps.append(
            (
                '<li class="nts-learning-path-step" '
                f'aria-label="{accessible_label}">'
                '<span class="nts-learning-path-step-index" '
                f'aria-hidden="true">{index}</span>'
                f'<span class="nts-learning-path-step-text">{escaped_step}</span>'
                "</li>"
            )
        )

    st.markdown(
        '<div class="nts-learning-path-map" '
        'data-cognivia-learning-path-map="true" '
        f'data-step-count="{step_count}" aria-label="Learning path map">'
        '<p class="nts-learning-path-map-title">Learning path map</p>'
        '<ol class="nts-learning-path-steps" '
        f'style="--nts-step-count: {step_count}">'
        + "".join(rendered_steps)
        + "</ol></div>",
        unsafe_allow_html=True,
    )


def _selected_learning_note_context(
    title: str,
    body: str,
    tags: list[str],
) -> dict[str, object] | None:
    clean_title = title.strip()
    clean_body = body.strip()
    if clean_title or clean_body or tags:
        return {
            "title": clean_title,
            "reflection": clean_body,
            "tags": tags,
        }

    stored_export = st.session_state.get(LEARNING_NOTE_EXPORT_SESSION_KEY)
    if not isinstance(stored_export, dict):
        return None
    note = stored_export.get("note")
    return note if isinstance(note, dict) else None


def build_full_learning_plan_markdown(
    *,
    goal: str,
    decision: dict[str, object] | None,
    selected_schema: LearningDirectionSchema,
    note: dict[str, object] | None = None,
) -> str:
    """Build a learning plan through the Streamlit composition root."""
    normalized_decision = decision or {}
    return build_full_learning_plan_document(
        goal=goal,
        decision=normalized_decision,
        selected_schema=selected_schema,
        note=note,
        evidence_reason=_noise_to_signal_reason(normalized_decision),
    )


def _parse_learning_note_tags(raw_tags: str) -> list[str]:
    tags = []
    for raw_tag in raw_tags.replace("\n", ",").split(","):
        tag = raw_tag.strip()
        if tag:
            tags.append(tag[:40])
    return tags[:8]


def _learning_note_export_payload(
    schema: LearningDirectionSchema,
    goal: str,
    title: str,
    body: str,
    tags: list[str],
) -> dict[str, object]:
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "app": "Cognivia",
        "goal": goal,
        "selected_path": {
            "id": schema["id"],
            "title": schema["title"],
            "subtitle": schema["subtitle"],
        },
        "note": {
            "title": title,
            "reflection": body,
            "tags": tags,
        },
        "first_action": schema["first_action"],
        "checkpoint": schema["checkpoint"],
    }


def _render_learning_note_exports(payload: dict[str, object]) -> None:
    selected_path = payload["selected_path"]
    note = payload["note"]
    if not isinstance(selected_path, dict) or not isinstance(note, dict):
        return

    markdown_content = build_learning_reflection_markdown(payload)
    json_content = json.dumps(payload, indent=2, sort_keys=True, default=str)
    st.caption("Markdown export and JSON export for your selected path.")
    st.download_button(
        "Download reflection Markdown",
        data=markdown_content,
        file_name=REFLECTION_MARKDOWN_FILE_NAME,
        mime=MARKDOWN_DOWNLOAD_MIME,
        key="download_learning_reflection_markdown",
        on_click="ignore",
    )
    st.download_button(
        "Download reflection JSON",
        data=json_content,
        file_name="cognivia-reflection.json",
        mime="application/json",
        key="download_learning_reflection_json",
        on_click="ignore",
    )


def _selected_learning_direction_schema(
    schemas: list[LearningDirectionSchema],
) -> LearningDirectionSchema | None:
    selected_id = st.session_state.get(SELECTED_LEARNING_SCHEMA_SESSION_KEY)
    for schema in schemas:
        if schema["id"] == selected_id:
            return schema
    return None


def _learning_direction_summary_values(
    schemas: list[LearningDirectionSchema],
    *,
    fallback_direction: object,
    fallback_reason: object,
    fallback_next_action: object,
) -> tuple[object, object, object]:
    selected_schema = _selected_learning_direction_schema(schemas)
    if not selected_schema:
        return fallback_direction, fallback_reason, fallback_next_action
    return (
        selected_schema["title"],
        selected_schema["fit_reason"],
        selected_schema["first_action"],
    )


def _render_full_learning_plan_download(
    *,
    goal: str,
    decision: dict[str, object] | None,
    selected_schema: LearningDirectionSchema,
    note: dict[str, object] | None,
) -> None:
    full_plan_markdown = build_full_learning_plan_markdown(
        goal=goal,
        decision=decision,
        selected_schema=selected_schema,
        note=note,
    )
    st.session_state[FULL_LEARNING_PLAN_MARKDOWN_SESSION_KEY] = full_plan_markdown
    st.download_button(
        FULL_LEARNING_PLAN_DOWNLOAD_LABEL,
        data=full_plan_markdown,
        file_name=FULL_LEARNING_PLAN_FILE_NAME,
        mime=MARKDOWN_DOWNLOAD_MIME,
        key="download_full_learning_plan_markdown",
        on_click="ignore",
        use_container_width=True,
    )


def _render_learning_direction_note_form(
    schemas: list[LearningDirectionSchema],
    goal: str,
    decision: dict[str, object] | None = None,
) -> None:
    selected_schema = _selected_learning_direction_schema(schemas)
    if not selected_schema:
        _render_results_compact_callout(
            "Choose a learning path first to unlock the mini notebook and exports."
        )
        return

    st.subheader("Save a reflection for this path")
    st.caption(
        "Selected path context is included in the Markdown and JSON exports after saving."
    )
    st.write(
        "Use this mini notebook to capture why this path fits and what you "
        "will do next."
    )
    _render_helper_tip(
        "iri",
        "Compare the path rationale with your next action before saving.",
    )
    note_title = st.text_input(
        "Note title",
        key="noise_to_signal_learning_note_title",
        placeholder="e.g., Why this path fits now",
    )
    note_body = st.text_area(
        "Reflection",
        key="noise_to_signal_learning_note_body",
        placeholder="What makes this path useful, and what will you do first?",
        height=100,
    )
    raw_tags = st.text_input(
        "Tags (optional)",
        key="noise_to_signal_learning_note_tags",
        placeholder="e.g., rag, portfolio, interview",
    )
    note_tags = _parse_learning_note_tags(raw_tags)
    _render_full_learning_plan_download(
        goal=goal,
        decision=decision,
        selected_schema=selected_schema,
        note=_selected_learning_note_context(note_title, note_body, note_tags),
    )

    if not st.button(
        "Save note",
        key="noise_to_signal_save_learning_note",
        use_container_width=True,
    ):
        stored_export = st.session_state.get(LEARNING_NOTE_EXPORT_SESSION_KEY)
        if isinstance(stored_export, dict):
            _render_learning_note_exports(stored_export)
        return

    title = note_title.strip()
    body = note_body.strip()
    if not title:
        st.error("Note title cannot be empty.")
        return
    if not body:
        st.error("Reflection cannot be empty.")
        return

    is_valid, error_message = _validate_compass_input(title, "Note title")
    if not is_valid:
        st.error(error_message)
        return
    is_valid, error_message = _validate_compass_long_input(body, "Reflection")
    if not is_valid:
        st.error(error_message)
        return

    for tag in note_tags:
        is_valid, error_message = _validate_compass_input(tag, "Tag")
        if not is_valid:
            st.error(error_message)
            return

    saved = _save_learning_direction_event(
        selected_schema,
        goal,
        "learning_note_saved",
        note_title=title,
        note_body=body,
        tags=note_tags,
    )
    export_payload = _learning_note_export_payload(
        selected_schema,
        goal,
        title,
        body,
        note_tags,
    )
    st.session_state[LEARNING_NOTE_EXPORT_SESSION_KEY] = export_payload
    if saved:
        st.success("Saved to learner memory.")
        st.caption("View recent notes in Recent learner memory / Memory history.")
    else:
        st.info(
            "Saved to local session memory. Configure DATABASE_URL for durable memory."
        )
        st.caption("Export this note below; it is not in durable memory history.")
    _render_learning_note_exports(export_payload)


def _prepare_learning_direction_schemas(
    decision,
    goal: str,
    *,
    recommended_subject: str | None = None,
) -> list[LearningDirectionSchema]:
    schemas = generate_learning_direction_schemas(goal, decision)
    if recommended_subject:
        evidence_quality = _display_value(decision.get("evidence_quality"))
        evidence_context = (
            f"; evidence: {str(evidence_quality).replace('_', ' ')}"
            if evidence_quality
            else ""
        )
        current_state = f"Recommended focus: {recommended_subject}{evidence_context}."
        schemas = [
            {
                **schema,
                "current_state": current_state,
            }
            for schema in schemas
        ]
    schemas = _store_learning_direction_schemas(schemas, goal)
    _save_learning_direction_generated_once(schemas, goal)
    return schemas


def _structured_learning_subject(decision) -> str | None:
    selected_focus = _display_value(decision.get("selected_focus"))
    if selected_focus:
        return str(selected_focus)

    recommended_direction = _display_value(decision.get("recommended_direction"))
    return str(recommended_direction) if recommended_direction else None


def _select_learning_direction_schema(
    schema: LearningDirectionSchema,
    goal: str,
) -> None:
    st.session_state[SELECTED_LEARNING_SCHEMA_SESSION_KEY] = schema["id"]
    _save_learning_direction_event(
        schema,
        goal,
        "learning_direction_selected",
    )


def _render_learning_direction_schema_options(
    schemas: list[LearningDirectionSchema],
    goal: str,
) -> None:
    st.subheader("Learning direction schemas")
    st.caption("Choose the path that best fits how you want to move next.")

    selected_schema = _selected_learning_direction_schema(schemas)
    if selected_schema:
        selected_index = schemas.index(selected_schema) + 1
        st.success(
            "Selected path: "
            f"{selected_index}. {selected_schema['title']} — {selected_schema['subtitle']}"
        )

    for index, schema in enumerate(schemas, start=1):
        selected = selected_schema and selected_schema["id"] == schema["id"]
        card_title = f"{index}. {schema['title']} — {schema['subtitle']}"
        with st.container(key=f"noise_to_signal_learning_schema_card_{schema['id']}"):
            st.markdown(f"**{card_title}**")
            if selected:
                st.success("This path is selected.")
            _render_learning_direction_schema(schema)
            st.button(
                "Choose this path",
                key=f"noise_to_signal_select_learning_schema_{schema['id']}",
                on_click=_select_learning_direction_schema,
                args=(schema, goal),
                use_container_width=True,
            )


def _render_learning_direction_schemas(decision, goal: str) -> None:
    schemas = _prepare_learning_direction_schemas(decision, goal)
    _render_learning_direction_schema_options(schemas, goal)
    _render_learning_direction_note_form(schemas, goal, decision)


def _render_noise_to_signal_guided_intake(decision, original_goal):
    if decision.get("interaction_mode") != "guided_intake":
        return

    stored_recommendation = st.session_state.get(GUIDED_RECOMMENDATION_SESSION_KEY)
    has_generated_recommendation = bool(
        stored_recommendation
        and st.session_state.get(GUIDED_RECOMMENDATION_GOAL_SESSION_KEY)
        == original_goal
    )
    context_callout = st.empty()
    if not has_generated_recommendation:
        _render_guided_intake_context_callout(context_callout)

    entry_point = decision.get("guided_intake_entry_point") or ENTRY_POINTS[0]
    entry_point_index = ENTRY_POINTS.index(entry_point) if entry_point in ENTRY_POINTS else 0
    entry_point_key = "noise_to_signal_guided_entry_point"
    entry_point_source_key = "noise_to_signal_guided_entry_point_source"

    if st.session_state.get(entry_point_source_key) != entry_point:
        st.session_state[entry_point_key] = entry_point
        st.session_state[entry_point_source_key] = entry_point

    st.subheader("Guided intake")
    st.write(
        "Cognivia needs learner profile context before choosing a learning path."
    )
    st.caption(f"Entry point: {entry_point}")

    with st.container(key="noise_to_signal_guided_intake"):
        intake_entry_point = st.selectbox(
            "Entry point",
            ENTRY_POINTS,
            index=entry_point_index,
            key=entry_point_key,
        )
        current_level = st.selectbox(
            "Current level",
            CURRENT_LEVEL_OPTIONS,
            key="noise_to_signal_guided_current_level",
        )
        current_skills = st.text_area(
            "Current skills",
            placeholder="e.g., Python, APIs, basic prompting",
            height=80,
            key="noise_to_signal_guided_current_skills",
        )
        interests = st.text_area(
            "Interests",
            placeholder="e.g., useful AI apps, clean code, reliable answers",
            height=80,
            key="noise_to_signal_guided_interests",
        )
        preferred_work_style = st.selectbox(
            "Preferred work style",
            PREFERRED_WORK_STYLES,
            key="noise_to_signal_guided_work_style",
        )
        target_role = st.text_input(
            "Target role or direction, if known",
            placeholder="e.g., AI Backend Engineer",
            key="noise_to_signal_guided_target_role",
        )
        time_available = st.number_input(
            "Study time available today (minutes)",
            min_value=1,
            max_value=480,
            value=60,
            step=10,
            help=(
                "Used to size the first action and checkpoint. "
                "Example: 60 minutes."
            ),
            key="noise_to_signal_guided_time_available",
        )

        if st.button(
            "Generate guided learning path",
            key="noise_to_signal_generate_guided_path",
            use_container_width=True,
        ):
            text_fields = {
                "Current skills": current_skills,
                "Interests": interests,
                "Target role or direction": target_role,
                "Learning goal": original_goal,
            }
            validation_errors = []

            for field_label, field_value in text_fields.items():
                if not field_value or not field_value.strip():
                    continue

                if field_label in {"Current skills", "Interests", "Learning goal"}:
                    is_valid, error_message = _validate_compass_long_input(
                        field_value.strip(),
                        field_label,
                    )
                else:
                    is_valid, error_message = _validate_compass_input(
                        field_value.strip(),
                        field_label,
                    )

                if not is_valid:
                    validation_errors.append(error_message)

            if validation_errors:
                st.error(validation_errors[0])
                return

            try:
                learner_profile = build_learner_profile(
                    entry_point=intake_entry_point,
                    current_level=current_level,
                    current_skills=current_skills,
                    interests=interests,
                    preferred_work_style=preferred_work_style,
                    target_role=target_role,
                    goal=original_goal,
                    time_available_minutes=int(time_available),
                )
                rag_query = build_guided_intake_query(learner_profile)
                retrieved_docs = []

                try:
                    with st.spinner("Searching local evidence for guidance..."):
                        retrieved_docs = retrieve_relevant_chunks(
                            rag_query,
                            k=4,
                            min_relevance_score=DEFAULT_MIN_RELEVANCE_SCORE,
                        )
                except Exception as error:
                    if _is_provider_configuration_error(error):
                        logger.info(
                            "Guided intake evidence retrieval skipped: provider is not configured."
                        )
                        _render_provider_configuration_warning()
                    elif _is_local_evidence_store_lock_error(error):
                        logger.info("Guided intake evidence retrieval skipped: Qdrant is busy.")
                        st.warning(LOCAL_EVIDENCE_STORE_BUSY_MESSAGE)
                    else:
                        logger.exception(
                            "Error retrieving evidence for Noise-to-Signal guided intake"
                        )

                recommendation = build_guided_intake_recommendation(
                    learner_profile,
                    retrieved_docs,
                )
            except ValueError as e:
                st.error(str(e))
            except Exception:
                logger.exception("Error in Noise-to-Signal guided intake")
                st.error(
                    "Unable to build a guided learning path right now. "
                    "Please try again later."
                )
            else:
                st.session_state[GUIDED_RECOMMENDATION_SESSION_KEY] = recommendation
                st.session_state[GUIDED_RECOMMENDATION_GOAL_SESSION_KEY] = original_goal
                context_callout.empty()
                _save_guided_intake_memory(
                    recommendation,
                    interaction_mode="noise_to_signal_guided_intake",
                )
    stored_recommendation = st.session_state.get(GUIDED_RECOMMENDATION_SESSION_KEY)
    if (
        stored_recommendation
        and st.session_state.get(GUIDED_RECOMMENDATION_GOAL_SESSION_KEY) == original_goal
    ):
        _render_guided_intake_recommendation(stored_recommendation)


def _render_noise_to_signal_trace(decision):
    trace = decision.get("decision_trace") or []
    visible_trace = [
        display_item
        for trace_item in trace
        if (display_item := _display_value(trace_item)) is not None
    ]

    if not visible_trace:
        return

    with st.expander(
        "Decision trace",
        expanded=False,
        key="noise_to_signal_decision_trace",
        on_change="ignore",
    ):
        for index, display_item in enumerate(visible_trace, start=1):
            st.markdown(f"**{index}. {display_item}**")


def _render_noise_to_signal_technical_details(decision):
    query_reformulated = decision.get("query_reformulated")
    retrieval_trace = decision.get("retrieval_trace") or []
    evidence_reason = _display_value(decision.get("evidence_reason"))
    routing_source = _display_value(decision.get("routing_source"))
    routing_reason = _display_value(decision.get("routing_reason"))

    has_query_reformulation = query_reformulated is not None
    visible_retrieval_trace = [
        display_item
        for trace_item in retrieval_trace
        if (display_item := _display_value(trace_item)) is not None
    ]

    if not any(
        [
            has_query_reformulation,
            visible_retrieval_trace,
            evidence_reason,
            routing_source,
            routing_reason,
        ]
    ):
        return

    with st.expander(
        "Technical details",
        expanded=False,
        key="noise_to_signal_technical_details",
        on_change="ignore",
    ):
        if has_query_reformulation:
            with st.expander(
                "Query reformulation",
                key="noise_to_signal_query_reformulation",
                on_change="ignore",
            ):
                if query_reformulated:
                    st.write("A single retrieval query reformulation was used.")
                else:
                    st.write("No retrieval query reformulation was used.")

        if visible_retrieval_trace:
            with st.expander(
                "Retrieval trace",
                key="noise_to_signal_retrieval_trace",
                on_change="ignore",
            ):
                for display_item in visible_retrieval_trace:
                    st.write(display_item)

        if evidence_reason:
            st.write(f"Evidence reason: {evidence_reason}")
        if routing_source:
            st.write(f"Routing source: {routing_source}")
        if routing_reason:
            st.write(f"Routing reason: {routing_reason}")


def _render_noise_to_signal_result(decision, study_plan, goal: str | None = None):
    _render_noise_to_signal_metrics(decision)
    _render_noise_to_signal_retrieval_warning(decision)

    assistant_label = (
        "Answer" if decision.get("decision_status") == "informational" else "Priority now"
    )
    why_now = _noise_to_signal_reason(decision)
    result_goal = _display_value(goal) or _display_value(decision.get("goal")) or ""

    if decision.get("interaction_mode") == "guided_intake":
        _render_noise_to_signal_guided_intake(decision, result_goal)
        return

    overview_tab, paths_tab, note_tab, technical_tab = st.tabs(
        ["Overview", "Learning paths", "Study note", "Evidence / technical"]
    )
    recommended_direction = _display_value(
        decision.get("selected_focus") or decision.get("recommended_direction")
    )
    prompt_is_in_scope = is_learning_or_ai_career_prompt(result_goal)

    if not prompt_is_in_scope:
        _clear_learning_direction_state()
        with overview_tab:
            _render_out_of_scope_learning_path_empty_state()
            with st.chat_message("assistant"):
                st.markdown(f"**{assistant_label}**")
                _write_if_present(
                    _noise_to_signal_recommendation_text(decision),
                    "No recommendation was returned.",
                )

            st.subheader("Why now")
            _write_if_present(why_now, "No short reasoning was returned.")

            st.subheader("Next action")
            _write_if_present(
                decision.get("next_action"),
                "Ask an AI learning, career, or study question.",
            )

        with paths_tab:
            _render_out_of_scope_learning_path_empty_state()

        with note_tab:
            _render_results_compact_callout(
                "Choose a generated learning path before saving a study note."
            )

        with technical_tab:
            _render_noise_to_signal_evidence(decision)
            _render_noise_to_signal_trace(decision)
            _render_noise_to_signal_technical_details(decision)
        return

    recommended_subject = _structured_learning_subject(decision)
    learning_subject = recommended_subject or result_goal
    schemas = _prepare_learning_direction_schemas(
        decision,
        learning_subject,
        recommended_subject=recommended_subject,
    )
    show_piko_tip = bool(schemas) and decision.get("decision_status") not in {
        "needs_clarification",
        "insufficient_evidence",
        "informational",
    }
    summary_values = _learning_direction_summary_values(
        schemas,
        fallback_direction=(
            recommended_direction or decision.get("recommendation")
        ),
        fallback_reason=why_now or decision.get("recommendation"),
        fallback_next_action=decision.get("next_action"),
    )

    _render_recommendation_summary(
        *summary_values,
        show_piko_tip=show_piko_tip,
    )

    with overview_tab:
        with st.chat_message("assistant"):
            st.markdown(f"**{assistant_label}**")
            _write_if_present(
                _noise_to_signal_recommendation_text(decision),
                "No recommendation was returned.",
            )

        st.subheader("Why now")
        _write_if_present(why_now, "No short reasoning was returned.")

        st.subheader("Next action")
        _write_if_present(decision.get("next_action"), "No next action was returned.")

        if recommended_direction:
            _render_recommended_direction(
                recommended_direction,
                why_this_fits=why_now,
                first_action=decision.get("next_action"),
            )

        _render_noise_to_signal_study_plan(decision, study_plan)

    with paths_tab:
        _render_learning_direction_schema_options(schemas, learning_subject)

    with note_tab:
        _render_learning_direction_note_form(schemas, learning_subject, decision)

    with technical_tab:
        _render_noise_to_signal_evidence(decision)
        _render_noise_to_signal_trace(decision)
        _render_noise_to_signal_technical_details(decision)


def _reset_noise_to_signal_result() -> None:
    st.session_state.pop("noise_to_signal_last_decision", None)
    st.session_state.pop("noise_to_signal_last_goal", None)
    _clear_guided_recommendation_state()
    _clear_learning_direction_state()


def _start_new_noise_to_signal_conversation() -> None:
    st.session_state["noise_to_signal_thread_id"] = str(uuid.uuid4())
    st.session_state["noise_to_signal_goal"] = ""
    _reset_noise_to_signal_result()


def _set_noise_to_signal_example_prompt(prompt: str) -> None:
    st.session_state["noise_to_signal_goal"] = prompt
    _reset_noise_to_signal_result()


def _complete_noise_to_signal_intro() -> None:
    st.session_state[NOISE_TO_SIGNAL_INTRO_STATE_SESSION_KEY] = "complete"


def _noise_to_signal_intro_is_complete() -> bool:
    return st.session_state.get(NOISE_TO_SIGNAL_INTRO_STATE_SESSION_KEY) == "complete"


def _noise_to_signal_intro_replay_requested() -> bool:
    return st.query_params.get("intro") == "1"


def _set_noise_to_signal_focus_mode(enabled: bool) -> None:
    st.session_state[NOISE_TO_SIGNAL_FOCUS_MODE_SESSION_KEY] = bool(enabled)


def _toggle_noise_to_signal_examples() -> None:
    examples_open = bool(
        st.session_state.get(NOISE_TO_SIGNAL_EXAMPLES_OPEN_SESSION_KEY)
    )
    st.session_state[NOISE_TO_SIGNAL_EXAMPLES_OPEN_SESSION_KEY] = not examples_open


def _noise_to_signal_loading_markup() -> str:
    return """
        <div class="nts-loading-card" data-cognivia-loading="true"
             role="status" aria-live="polite" aria-atomic="true">
            <p class="nts-loading-title">
                <span>Finding the signal…</span>
                <span class="nts-loading-dots" aria-hidden="true">
                    <span></span><span></span><span></span>
                </span>
            </p>
            <p class="nts-loading-copy">
                Reviewing evidence and shaping your recommendation.
            </p>
        </div>
    """


def _render_noise_to_signal_loading() -> None:
    st.markdown(
        _noise_to_signal_loading_markup(),
        unsafe_allow_html=True,
    )


def _submit_noise_to_signal_goal(goal: str) -> None:
    if st.session_state.get(NOISE_TO_SIGNAL_PROCESSING_SESSION_KEY):
        return

    if not goal.strip():
        st.error("Please enter a learning goal or decision.")
        return

    is_valid, error_message = _validate_compass_long_input(
        goal.strip(),
        "Learning goal",
    )
    if not is_valid:
        st.error(error_message)
        return

    st.session_state[NOISE_TO_SIGNAL_PROCESSING_SESSION_KEY] = True
    loading_placeholder = st.empty()
    loading_placeholder.markdown(
        _noise_to_signal_loading_markup(),
        unsafe_allow_html=True,
    )
    try:
        decision = run_noise_to_signal(
            goal.strip(),
            thread_id=st.session_state["noise_to_signal_thread_id"],
        )
        _clear_guided_recommendation_state()
        _clear_learning_direction_state()
        st.session_state["noise_to_signal_last_goal"] = goal.strip()
        st.session_state["noise_to_signal_last_decision"] = decision
        _save_noise_to_signal_memory(decision, user_goal=goal.strip())
    except ValueError:
        logger.exception(
            "Validation or retrieval setup error in Noise-to-Signal Agent mode"
        )
        st.error(
            "Could not generate the decision trace. Please check your inputs and try again."
        )
    except Exception:
        logger.exception("Error in Noise-to-Signal Agent mode")
        st.error(
            "An error occurred while generating the decision trace. Please try again."
        )
    finally:
        loading_placeholder.empty()
        st.session_state[NOISE_TO_SIGNAL_PROCESSING_SESSION_KEY] = False


def _submit_noise_to_signal_quick_prompt(prompt: str) -> None:
    st.session_state[NOISE_TO_SIGNAL_EXAMPLES_OPEN_SESSION_KEY] = False
    st.session_state["noise_to_signal_goal"] = prompt
    if prompt == NOISE_TO_SIGNAL_GUIDED_INTAKE_QUICK_PROMPT:
        _reset_noise_to_signal_result()
        return

    st.session_state[NOISE_TO_SIGNAL_RESULT_FOCUS_SESSION_KEY] = True
    _submit_noise_to_signal_goal(prompt)


def _start_noise_to_signal_guided_intake(goal: str) -> None:
    _clear_guided_recommendation_state()
    _clear_learning_direction_state()
    st.session_state[NOISE_TO_SIGNAL_RESULT_FOCUS_SESSION_KEY] = True
    st.session_state["noise_to_signal_last_goal"] = goal
    st.session_state["noise_to_signal_last_decision"] = {
        "goal": goal,
        "decision_status": "needs_clarification",
        "interaction_mode": "guided_intake",
        "guided_intake_entry_point": ENTRY_POINTS[2],
        "evidence_quality": "not_required",
        "retrieval_attempts": 0,
        "selected_focus": None,
        "recommendation": (
            "I need a little learner profile context before choosing a learning path."
        ),
        "next_action": (
            "Add your current level, current skills, interests, preferred work style, "
            "target role if known, and available learning time."
        ),
        "decision_trace": [],
        "evidence": {"items": []},
        "study_plan": None,
        "query_reformulated": False,
        "retrieval_trace": ["Retrieval skipped: more context required."],
    }


def _noise_to_signal_intro_video_markup() -> str | None:
    video_uri = _asset_data_uri(NOISE_TO_SIGNAL_INTRO_VIDEO_PATH)
    if not video_uri:
        return None
    # Activate the opaque overlay in its first DOM frame, before landing deltas paint.
    return (
        '<div class="nts-intro-video-layer is-playing" aria-hidden="true">'
        f'<video id="nts-intro-video" src="{html.escape(video_uri, quote=True)}" '
        "autoplay muted playsinline preload=\"auto\"></video>"
        "</div>"
    )


def _render_noise_to_signal_intro() -> None:
    markup = _noise_to_signal_intro_video_markup()
    if markup:
        st.markdown(markup, unsafe_allow_html=True)
    # The controller also releases the startup cover through its DOM failsafe
    # when the video asset cannot be rendered.
    _render_noise_to_signal_intro_video_controller()
    _complete_noise_to_signal_intro()


def _render_noise_to_signal_focus_mode_control() -> None:
    focus_enabled = bool(st.session_state.get(NOISE_TO_SIGNAL_FOCUS_MODE_SESSION_KEY))
    if focus_enabled:
        st.markdown(
            '<div class="nts-focus-mode-active" aria-hidden="true"></div>',
            unsafe_allow_html=True,
        )
        st.button(
            "Exit Focus Mode",
            key="noise_to_signal_focus_mode_exit",
            help="Exit Focus Mode",
            on_click=_set_noise_to_signal_focus_mode,
            args=(False,),
        )
        return

    st.button(
        "Enter Focus Mode",
        key="noise_to_signal_focus_mode_enter",
        help="Enter Focus Mode",
        on_click=_set_noise_to_signal_focus_mode,
        args=(True,),
    )


_render_ai_skill_compass = partial(
    _render_ai_skill_compass_view,
    LOCAL_EVIDENCE_STORE_BUSY_MESSAGE=LOCAL_EVIDENCE_STORE_BUSY_MESSAGE,
    _is_local_evidence_store_lock_error=_is_local_evidence_store_lock_error,
    _save_guided_intake_memory=_save_guided_intake_memory,
    _render_guided_intake_recommendation=_render_guided_intake_recommendation,
)


def _render_noise_to_signal_home(last_goal: str | None, last_decision) -> None:
    is_processing = bool(
        st.session_state.get(NOISE_TO_SIGNAL_PROCESSING_SESSION_KEY)
    )
    with st.container(key="noise_to_signal_home_shell"):
        with st.container(key="noise_to_signal_landing_card"):
            st.markdown(
                '<h1 class="nts-home-question">What&apos;s your next decision?</h1>',
                unsafe_allow_html=True,
            )
            with st.container(key="noise_to_signal_search_shell"):
                st.button(
                    "Toggle Try examples",
                    key="noise_to_signal_examples_toggle",
                    help="Try examples",
                    on_click=_toggle_noise_to_signal_examples,
                    type="tertiary",
                    disabled=is_processing,
                )
                goal = st.text_input(
                    "Learning decision",
                    placeholder="Help me decide what to learn next...",
                    key="noise_to_signal_goal",
                    label_visibility="collapsed",
                )
                submitted = st.button(
                    "↵",
                    key="generate_noise_to_signal_decision",
                    help="Submit learning decision",
                    use_container_width=True,
                    disabled=is_processing,
                )
            if submitted:
                _submit_noise_to_signal_goal(goal)
            elif is_processing:
                _render_noise_to_signal_loading()

            st.button(
                "Try examples",
                key="noise_to_signal_examples_row_toggle",
                help="Toggle Try examples",
                on_click=_toggle_noise_to_signal_examples,
                type="tertiary",
                use_container_width=True,
                disabled=is_processing,
            )
            if st.session_state.get(NOISE_TO_SIGNAL_EXAMPLES_OPEN_SESSION_KEY):
                with st.container(key="noise_to_signal_quick_prompts"):
                    for index, prompt in enumerate(NOISE_TO_SIGNAL_QUICK_PROMPTS):
                        st.button(
                            prompt,
                            key=f"noise_to_signal_quick_prompt_{index}",
                            on_click=_submit_noise_to_signal_quick_prompt,
                            args=(prompt,),
                            use_container_width=True,
                            disabled=is_processing,
                        )
            if (
                goal == NOISE_TO_SIGNAL_GUIDED_INTAKE_QUICK_PROMPT
                and not last_decision
            ):
                st.button(
                    "Start guided intake",
                    key="noise_to_signal_start_guided_intake",
                    on_click=_start_noise_to_signal_guided_intake,
                    args=(goal,),
                    use_container_width=True,
                    disabled=is_processing,
                )
            st.markdown(
                '<p class="nts-home-support">Let&apos;s find the '
                '<span>signal</span> together.</p>',
                unsafe_allow_html=True,
            )


_install_app_rerender_stability_guard()
if app_mode == "Noise-to-Signal Agent":
    _render_runtime_status()
else:
    _render_secondary_project_drawer()


if app_mode == "Interview Coach":
    _render_interview_coach()
elif app_mode == "Noise-to-Signal Agent":
    _render_noise_to_signal_styles()
    if "noise_to_signal_thread_id" not in st.session_state:
        st.session_state["noise_to_signal_thread_id"] = str(uuid.uuid4())
    if "noise_to_signal_last_decision" not in st.session_state:
        st.session_state["noise_to_signal_last_decision"] = None
    if "noise_to_signal_last_goal" not in st.session_state:
        st.session_state["noise_to_signal_last_goal"] = ""
    if NOISE_TO_SIGNAL_INTRO_STATE_SESSION_KEY not in st.session_state:
        st.session_state[NOISE_TO_SIGNAL_INTRO_STATE_SESSION_KEY] = "pending"
    if NOISE_TO_SIGNAL_FOCUS_MODE_SESSION_KEY not in st.session_state:
        st.session_state[NOISE_TO_SIGNAL_FOCUS_MODE_SESSION_KEY] = False
    if NOISE_TO_SIGNAL_EXAMPLES_OPEN_SESSION_KEY not in st.session_state:
        st.session_state[NOISE_TO_SIGNAL_EXAMPLES_OPEN_SESSION_KEY] = False
    if NOISE_TO_SIGNAL_PROCESSING_SESSION_KEY not in st.session_state:
        st.session_state[NOISE_TO_SIGNAL_PROCESSING_SESSION_KEY] = False

    last_goal = _display_value(st.session_state.get("noise_to_signal_last_goal"))
    last_decision = st.session_state.get("noise_to_signal_last_decision")
    if (
        not _noise_to_signal_intro_is_complete()
        or _noise_to_signal_intro_replay_requested()
    ):
        _render_noise_to_signal_intro()
    _render_noise_to_signal_runtime_drawer()
    _render_noise_to_signal_header()
    _render_noise_to_signal_focus_mode_control()
    _render_noise_to_signal_home(last_goal, last_decision)
    last_goal = _display_value(st.session_state.get("noise_to_signal_last_goal"))
    last_decision = st.session_state.get("noise_to_signal_last_decision")
    focus_results = bool(
        st.session_state.pop(NOISE_TO_SIGNAL_RESULT_FOCUS_SESSION_KEY, False)
    )
    if last_goal and last_decision:
        with st.container(key="noise_to_signal_results_panel"):
            st.button(
                "New search",
                key="noise_to_signal_start_new",
                help="Start a new search",
                on_click=_start_new_noise_to_signal_conversation,
                type="tertiary",
            )
            with st.container(key="noise_to_signal_query_summary"):
                with st.chat_message("user"):
                    st.write(last_goal)
            _render_noise_to_signal_result(
                last_decision,
                last_decision.get("study_plan"),
                last_goal,
            )
    _render_noise_to_signal_control_accessibility(
        focus_results=focus_results and bool(last_goal and last_decision),
    )
    _render_learner_memory_history()

elif app_mode == "AI Skill Compass":
    _render_ai_skill_compass()
