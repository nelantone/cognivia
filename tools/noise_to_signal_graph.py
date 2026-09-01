"""LangGraph workflow for hybrid Noise-to-Signal decision routing."""

import logging
import re
from pathlib import Path
from typing import Any, Literal, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from tools.provider_config import get_provider_config, provider_api_key, provider_base_url
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field, ValidationError

try:
    from langsmith import traceable
except ImportError:  # pragma: no cover - LangSmith is optional.
    def traceable(*args, **kwargs):
        """Fallback decorator when LangSmith is unavailable."""

        def decorator(func):
            return func

        return decorator

from openrouter_client import DEFAULT_MODEL
from rag.config import DEFAULT_MIN_RELEVANCE_SCORE
from rag.retriever import retrieve_relevant_chunks
from tools.study_plan import (
    _clean_text,
    _is_informational_question,
    _rank_decision_options,
    _select_decision_focus,
    _summarize_reasoning_evidence,
    build_informational_answer as _legacy_build_informational_answer,
    generate_study_plan,
    guided_intake_entry_point_for_goal,
    summarize_retrieved_evidence,
)

logger = logging.getLogger(__name__)

SUPPORTED_DECISION_STATUSES = {
    "informational",
    "needs_clarification",
    "single_focus",
    "selected",
    "tie",
    "insufficient_evidence",
}

LLM_ROUTABLE_INTENTS = {
    "informational",
    "comparison",
    "single_focus",
    "needs_clarification",
}
EXPLANATION_QUESTION_PATTERNS = (
    re.compile(r"\b(?:can|could|would)\s+you\s+explain\b", re.IGNORECASE),
    re.compile(r"\b(?:explain|describe)\s+.+", re.IGNORECASE),
    re.compile(r"^what\s+is\s+.+", re.IGNORECASE),
)
AMBIGUOUS_GUIDANCE_PATTERNS = (
    re.compile(r"\bunsure\s+whether\b", re.IGNORECASE),
    re.compile(r"\bnot\s+sure\s+whether\b", re.IGNORECASE),
    re.compile(r"\btrying\s+to\s+decide\s+whether\b", re.IGNORECASE),
)
SELF_CONTAINED_INFORMATIONAL_QUESTION_PATTERNS = (
    re.compile(
        r"^why\s+(?:is|are)\s+.+\s+useful(?:\s+(?:for|to)\s+.+)?$",
        re.IGNORECASE,
    ),
    re.compile(
        r"^why\s+(?:is|are)\s+.+\s+important(?:\s+(?:for|to)\s+.+)?$",
        re.IGNORECASE,
    ),
    re.compile(r"^how\s+(?:does|do|is|are)\s+.+\s+work$", re.IGNORECASE),
    re.compile(r"^what\s+are\s+the\s+benefits\s+of\s+.+", re.IGNORECASE),
    re.compile(r"^what\s+is\s+the\s+purpose\s+of\s+.+", re.IGNORECASE),
)
QUESTION_SUPPORT_PATTERNS = {
    "benefit": re.compile(
        r"\b(?:useful|important|benefits?|because|helps?|enables?|allows?|"
        r"supports?|improves?|provides?|combines?|checks?|measures?|"
        r"quality|traceability|grounding|failure\s+analysis|control)\b",
        re.IGNORECASE,
    ),
    "definition": re.compile(
        r"\b(?:means|refers\s+to|framework|tool|method|process|"
        r"system|approach|technique|can|uses?|build|checks?|enables?|"
        r"supports?|provides?)\b",
        re.IGNORECASE,
    ),
}
AI_ENGINEERING_DOMAIN_PATTERNS = (
    re.compile(
        r"\b(?:ai|artificial\s+intelligence|machine\s+learning|ml)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:llms?|large\s+language\s+models?|rag|retrieval)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:agents?|langgraph|prompt(?:ing)?|embeddings?|vector\s+stores?)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:evaluation|evals?|grounding|hallucination|observability)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:software|programming|python|api|backend|frontend|database|db)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(?:data|analytics?|deployment|docker|cloud|mcp)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:career|job\s+market|portfolio|project\s+skills?)\b", re.IGNORECASE),
)
PROFICIENCY_LEVEL_INPUTS = {
    "beginner",
    "junior",
    "intermediate",
    "mid-level",
    "mid level",
    "senior",
    "advanced",
}
ROLE_LIKE_SUFFIXES = {
    "engineer",
    "developer",
    "scientist",
    "analyst",
    "architect",
    "manager",
    "designer",
    "specialist",
    "consultant",
    "researcher",
}
EXPLICIT_CONTEXT_REQUEST_PATTERNS = (
    re.compile(r"\b(?:i\s+want|i\s+need|help\s+me|create)\b", re.IGNORECASE),
    re.compile(r"\b(?:learn|study|prioriti[sz]e|choose|decide)\b", re.IGNORECASE),
    re.compile(r"\bshould\s+i\b", re.IGNORECASE),
    re.compile(r"\b(?:explain|describe|what|which|how|why|when)\b", re.IGNORECASE),
)
CONTEXT_FRAGMENT_PATTERNS = (
    re.compile(r"^for\s+.+", re.IGNORECASE),
    re.compile(r"^as\s+.+", re.IGNORECASE),
)


class AmbiguousIntentClassification(BaseModel):
    """Structured output for LLM-controlled routing of ambiguous requests."""

    intent: Literal[
        "informational",
        "comparison",
        "single_focus",
        "needs_clarification",
    ]
    confidence: float = Field(ge=0, le=1)
    reason: str = Field(min_length=1, max_length=240)
    selected_focus: str | None = None
    options: list[str] = Field(default_factory=list)


class NoiseToSignalState(TypedDict, total=False):
    """State carried through the Noise-to-Signal graph."""

    goal: str
    retrieved_docs: list[Any]
    evidence: dict[str, Any]
    reasoning_evidence: dict[str, Any]
    decision_status: str
    needs_clarification: bool
    options: list[str]
    ranked_options: list[dict[str, Any]]
    option_scores: list[dict[str, Any]]
    selected_focus: str | None
    tied_options: list[str]
    recommendation: str
    next_action: str
    decision_trace: list[str]
    study_plan: dict[str, Any] | None
    interaction_mode: str
    guided_intake_entry_point: str | None
    route_via_llm: bool
    routing_source: str
    routing_confidence: float | None
    routing_reason: str | None
    routing_attempts: int
    original_goal: str | None
    pending_clarification: bool
    clarification_context: str | None
    context_only_followup: bool
    retrieval_override: bool
    retrieval_required: bool
    retrieval_query: str | None
    retrieval_attempts: int
    query_reformulated: bool
    evidence_quality: str | None
    evidence_reason: str | None
    retrieval_trace: list[str]
    retrieval_error: str | None
    informational_answer: str | None


def _empty_reasoning_evidence() -> dict[str, Any]:
    return {
        "has_evidence": False,
        "items": [],
    }


def _empty_display_evidence() -> dict[str, Any]:
    return {
        "has_evidence": False,
        "summary": "No retrieved knowledge-base evidence was available.",
        "items": [],
        "claims": [],
    }


def _retrieval_error_code(error: Exception) -> str:
    message = str(error).lower()
    if "already accessed by another instance of qdrant client" in message:
        return "local_evidence_store_locked"
    if (
        "api key is missing" in message
        or "provider selected but" in message
        or "unsupported provider" in message
    ):
        return "provider_configuration_unavailable"

    return "retrieval_failed"


def _retrieval_error_reason(error_code: str, decision_status: str | None) -> str:
    if error_code == "local_evidence_store_locked":
        if decision_status == "single_focus":
            return (
                "The local evidence store is busy, so this run used a "
                "deterministic study-plan fallback."
            )
        return (
            "The local evidence store is busy. Try again after the current "
            "retrieval finishes."
        )
    if error_code == "provider_configuration_unavailable":
        return (
            "Evidence retrieval unavailable. No embedding provider key is "
            "configured, so Cognivia cannot build or query the evidence index "
            "right now."
        )

    if decision_status == "single_focus":
        return "Retrieval failed; using a deterministic plan only."

    return "Retrieval failed; no evidence-safe answer is available."


def _accumulate_clarification_context(
    previous_context: str | None,
    latest_context: str,
) -> str:
    previous_items = [
        _clean_text(item)
        for item in str(previous_context or "").splitlines()
        if _clean_text(item)
    ]
    latest_item = _clean_text(latest_context)
    if not latest_item:
        return "\n".join(previous_items)

    normalized_items = {item.casefold() for item in previous_items}
    if latest_item.casefold() not in normalized_items:
        previous_items.append(latest_item)

    return "\n".join(previous_items)


def _format_clarification_context_for_display(clarification_context: str) -> str:
    return "; ".join(
        item
        for item in (
            _clean_text(context_item)
            for context_item in clarification_context.splitlines()
        )
        if item
    )


def _is_standalone_proficiency_level(goal: str) -> bool:
    normalized_goal = _clean_text(goal).casefold()
    normalized_goal = re.sub(r"\s*-\s*", "-", normalized_goal)
    return normalized_goal in PROFICIENCY_LEVEL_INPUTS


def _has_explicit_context_request(goal: str) -> bool:
    return any(pattern.search(goal) for pattern in EXPLICIT_CONTEXT_REQUEST_PATTERNS)


def _is_short_role_like_input(goal: str) -> bool:
    if _has_explicit_context_request(goal):
        return False

    normalized_goal = _clean_text(goal).strip(" .?!")
    terms = re.findall(r"[a-z]+", normalized_goal.casefold())
    if len(terms) < 2 or len(terms) > 4:
        return False

    return terms[-1] in ROLE_LIKE_SUFFIXES


def _is_context_fragment(goal: str) -> bool:
    return any(pattern.search(_clean_text(goal)) for pattern in CONTEXT_FRAGMENT_PATTERNS)


def _is_context_only_input(goal: str) -> bool:
    return (
        _is_standalone_proficiency_level(goal)
        or _is_short_role_like_input(goal)
        or _is_context_fragment(goal)
    )


def _base_clarification_context(original_goal: str, previous_context: str | None):
    if previous_context:
        return previous_context

    if _is_context_only_input(original_goal):
        return original_goal

    return None


def resolve_clarification_context(state: NoiseToSignalState) -> NoiseToSignalState:
    """Resolve checkpointed clarification without exposing orchestration text."""
    clean_goal = _clean_text(state.get("goal", ""))

    if state.get("pending_clarification"):
        original_goal = state.get("original_goal") or clean_goal
        if not _is_context_only_input(clean_goal):
            return {
                "goal": clean_goal,
                "original_goal": None,
                "pending_clarification": False,
                "clarification_context": None,
                "context_only_followup": False,
            }

        clarification_context = _accumulate_clarification_context(
            _base_clarification_context(
                original_goal,
                state.get("clarification_context"),
            ),
            clean_goal,
        )
        context_display = (
            _format_clarification_context_for_display(clarification_context)
            or clean_goal
        )
        return {
            "goal": context_display,
            "original_goal": original_goal,
            "pending_clarification": False,
            "clarification_context": clarification_context,
            "context_only_followup": True,
        }

    return {
        "goal": clean_goal,
        "original_goal": None,
        "pending_clarification": False,
        "clarification_context": None,
        "context_only_followup": False,
    }


def reset_retrieval_state(state: NoiseToSignalState) -> NoiseToSignalState:
    """Clear per-turn retrieval state while preserving conversation memory."""
    if state.get("retrieval_override"):
        retrieved_docs = state.get("retrieved_docs") or []
    else:
        retrieved_docs = []

    return {
        "retrieved_docs": retrieved_docs,
        "reasoning_evidence": _empty_reasoning_evidence(),
        "evidence": _empty_display_evidence(),
        "study_plan": None,
        "retrieval_required": False,
        "retrieval_query": None,
        "retrieval_attempts": 0,
        "query_reformulated": False,
        "evidence_quality": None,
        "evidence_reason": None,
        "retrieval_trace": [],
        "retrieval_error": None,
        "informational_answer": None,
    }


def prepare_evidence(state: NoiseToSignalState) -> NoiseToSignalState:
    """Build display and reasoning evidence from retrieved documents."""
    retrieved_docs = state.get("retrieved_docs") or []

    return {
        "retrieved_docs": retrieved_docs,
        "reasoning_evidence": _summarize_reasoning_evidence(retrieved_docs),
        "evidence": summarize_retrieved_evidence(retrieved_docs),
        "study_plan": None,
    }


def _is_known_clear_clarification_goal(goal: str) -> bool:
    return bool(guided_intake_entry_point_for_goal(goal))


def _interaction_mode_for_request(
    decision_status: str,
    guided_intake_entry_point: str | None,
) -> str:
    if guided_intake_entry_point:
        return "guided_intake"
    if decision_status == "needs_clarification":
        return "clarification"
    return "direct_decision"


def _is_clear_explanation_question(goal: str) -> bool:
    return any(pattern.search(goal) for pattern in EXPLANATION_QUESTION_PATTERNS)


def _is_ambiguous_guidance_goal(goal: str) -> bool:
    return any(pattern.search(goal) for pattern in AMBIGUOUS_GUIDANCE_PATTERNS)


def _is_self_contained_informational_question(goal: str) -> bool:
    clean_goal = _clean_text(goal)
    clean_goal = clean_goal.strip().rstrip("?!.")
    return (
        _is_clear_explanation_question(goal)
        or _is_informational_question(goal)
        or any(
            pattern.search(clean_goal)
            for pattern in SELF_CONTAINED_INFORMATIONAL_QUESTION_PATTERNS
        )
    )


def _should_route_ambiguous_intent(goal: str, decision_status: str) -> bool:
    if _is_ambiguous_guidance_goal(goal):
        return True

    if decision_status != "needs_clarification":
        return False

    if _is_known_clear_clarification_goal(goal):
        return False

    return "?" in goal


def determine_request_shape(state: NoiseToSignalState) -> NoiseToSignalState:
    """Determine enough request shape to decide whether retrieval is useful."""
    clean_goal = _clean_text(state.get("goal", ""))
    empty_evidence = _empty_reasoning_evidence()
    guided_intake_entry_point = guided_intake_entry_point_for_goal(clean_goal)

    if state.get("context_only_followup"):
        focus_decision = {
            "selected_focus": None,
            "options": [],
            "ranked_options": [],
            "decision_status": "needs_clarification",
            "tied_options": [],
        }
    elif guided_intake_entry_point:
        focus_decision = {
            "selected_focus": None,
            "options": [],
            "ranked_options": [],
            "decision_status": "needs_clarification",
            "tied_options": [],
        }
    elif _is_self_contained_informational_question(clean_goal):
        focus_decision = {
            "selected_focus": None,
            "options": [],
            "ranked_options": [],
            "decision_status": "informational",
            "tied_options": [],
        }
    elif _is_context_only_input(clean_goal):
        focus_decision = {
            "selected_focus": None,
            "options": [],
            "ranked_options": [],
            "decision_status": "needs_clarification",
            "tied_options": [],
        }
    else:
        focus_decision = _select_decision_focus(clean_goal, empty_evidence)

    decision_status = focus_decision["decision_status"]
    retrieval_required = decision_status != "needs_clarification"
    interaction_mode = _interaction_mode_for_request(
        decision_status,
        guided_intake_entry_point,
    )
    retrieval_trace = []
    if not retrieval_required and not state.get("retrieval_override"):
        retrieval_trace.append("Retrieval skipped: more context required.")

    return {
        "goal": clean_goal,
        "selected_focus": focus_decision["selected_focus"],
        "options": focus_decision["options"],
        "ranked_options": focus_decision["ranked_options"],
        "option_scores": focus_decision["ranked_options"],
        "decision_status": decision_status,
        "needs_clarification": decision_status == "needs_clarification",
        "interaction_mode": interaction_mode,
        "guided_intake_entry_point": guided_intake_entry_point,
        "tied_options": focus_decision["tied_options"],
        "retrieval_required": retrieval_required,
        "retrieval_query": clean_goal if retrieval_required else None,
        "evidence_quality": "not_required" if not retrieval_required else None,
        "evidence_reason": (
            "The request needs clarification before retrieval."
            if not retrieval_required
            else None
        ),
        "retrieval_trace": retrieval_trace,
        "route_via_llm": False,
        "routing_source": "deterministic",
        "routing_confidence": None,
        "routing_reason": "Deterministic routing handled a clear request.",
        "routing_attempts": 0,
    }


def route_after_request_shape(state: NoiseToSignalState) -> str:
    """Skip retrieval for clarification-only input."""
    if not state.get("retrieval_required"):
        return "request_clarification"

    if state.get("retrieval_override"):
        return "prepare_evidence"

    return "retrieve_evidence"


def retrieve_evidence(
    state: NoiseToSignalState,
    retriever=retrieve_relevant_chunks,
) -> NoiseToSignalState:
    """Retrieve evidence through the injected retriever dependency."""
    query = _clean_text(state.get("retrieval_query") or state.get("goal", ""))
    attempts = int(state.get("retrieval_attempts") or 0) + 1
    trace = list(state.get("retrieval_trace") or [])

    try:
        retrieved_docs = retriever(
            query,
            k=20,
            min_relevance_score=DEFAULT_MIN_RELEVANCE_SCORE,
        )
    except Exception as error:
        error_code = _retrieval_error_code(error)
        if error_code == "provider_configuration_unavailable":
            logger.info("Noise-to-Signal retrieval skipped: provider is not configured.")
        else:
            logger.exception("Noise-to-Signal retrieval failed")
        trace.append(f"Retrieval attempt {attempts}: failed.")
        return {
            "retrieved_docs": [],
            "reasoning_evidence": _empty_reasoning_evidence(),
            "evidence": _empty_display_evidence(),
            "retrieval_attempts": attempts,
            "retrieval_error": error_code,
            "evidence_quality": "failed",
            "evidence_reason": "Retrieval failed before evidence could be assessed.",
            "retrieval_trace": trace,
        }

    return {
        "retrieved_docs": list(retrieved_docs or []),
        "retrieval_attempts": attempts,
        "retrieval_trace": trace,
    }


def _ranked_options_with_support(options: list[str], reasoning_evidence: dict[str, Any]):
    ranked_options = _rank_decision_options(options, reasoning_evidence)
    unsupported_options = [
        item["option"] for item in ranked_options if item["score"] <= 0
    ]
    return ranked_options, unsupported_options


def _comparison_state_from_ranked_options(ranked_options: list[dict[str, Any]]):
    best_option = ranked_options[0]
    best_score = best_option["score"]
    tied_options = [
        item["option"] for item in ranked_options if item["score"] == best_score
    ]

    if len(tied_options) > 1:
        return {
            "decision_status": "tie",
            "selected_focus": None,
            "tied_options": tied_options,
        }

    return {
        "decision_status": "selected",
        "selected_focus": best_option["option"],
        "tied_options": [],
    }


def _informational_question_shape(goal: str) -> tuple[str, str] | None:
    clean_goal = _clean_text(goal).strip(" ?.!:")
    patterns = (
        ("how", r"^how\s+(?:does|do|is|are)\s+(?P<topic>.+?)\s+work$"),
        ("benefit", r"^why\s+(?:is|are)\s+(?P<topic>.+?)\s+useful(?:\s+(?:for|to)\s+.+)?$"),
        ("benefit", r"^why\s+(?:is|are)\s+(?P<topic>.+?)\s+important(?:\s+(?:for|to)\s+.+)?$"),
        ("benefit", r"^what\s+are\s+the\s+benefits\s+of\s+(?P<topic>.+)$"),
        ("benefit", r"^what\s+is\s+the\s+purpose\s+of\s+(?P<topic>.+)$"),
        ("definition", r"^(?:can|could|would)\s+you\s+explain\s+(?P<topic>.+)$"),
        ("definition", r"^(?:describe|explain)\s+(?P<topic>.+)$"),
        ("definition", r"^what\s+is\s+(?P<topic>.+)$"),
    )
    for question_type, pattern in patterns:
        match = re.search(pattern, clean_goal, flags=re.IGNORECASE)
        if match:
            topic = _clean_text(match.group("topic")).strip(" ?.!:")
            return question_type, topic
    return None


def _topic_pattern(topic: str) -> str:
    return r"\b" + r"\s+".join(re.escape(part) for part in topic.split()) + r"\b"


def _is_ai_engineering_domain_focus(focus: str) -> bool:
    clean_focus = _clean_text(focus)
    return any(pattern.search(clean_focus) for pattern in AI_ENGINEERING_DOMAIN_PATTERNS)


def _evidence_directly_mentions_focus(
    focus: str,
    evidence_items: list[dict[str, Any]],
) -> bool:
    clean_focus = _clean_text(focus).strip(" .?!")
    if not clean_focus:
        return False

    focus_pattern = _topic_pattern(clean_focus)
    for item in evidence_items:
        evidence_text = _clean_text(
            " ".join(
                str(item.get(field, ""))
                for field in ("title", "excerpt", "claim", "full_text")
            )
        )
        if re.search(focus_pattern, evidence_text, flags=re.IGNORECASE):
            return True

    return False


def _single_focus_has_domain_or_direct_support(state: NoiseToSignalState) -> bool:
    focus = _clean_text(state.get("selected_focus") or state.get("goal", ""))
    return _is_ai_engineering_domain_focus(focus) or _evidence_directly_mentions_focus(
        focus,
        _reasoning_items_with_full_text(state),
    )


def _is_sentence_like_claim(sentence: str) -> bool:
    clean_sentence = _clean_text(sentence).strip(" -#*:;")
    words = clean_sentence.split()
    if len(words) < 7 or clean_sentence.endswith(":"):
        return False
    if not re.search(r"\b(?:is|are|can|does|do|works?|uses?|helps?|enables?|supports?|provides?|checks?|measures?|combines?|routes?)\b", clean_sentence, re.IGNORECASE):
        return False
    return bool(re.search(r"[.!?]$", clean_sentence))


def _clean_candidate_sentence(sentence: str) -> str:
    clean_sentence = _clean_text(sentence).strip(" -#*")
    clean_sentence = re.sub(r"\s+,", ",", clean_sentence)
    clean_sentence = re.sub(r"\s+([.!?])", r"\1", clean_sentence)
    if clean_sentence.endswith("..."):
        return ""
    if re.search(r"(?:,|:|;|\b(?:and|or))\s*[.!?]?$", clean_sentence, re.IGNORECASE):
        return ""
    return clean_sentence


def _remove_markdown_headings(raw_text: str) -> str:
    lines = str(raw_text or "").splitlines()
    kept_lines = []
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped_line = line.strip()
        next_line = lines[index + 1].strip() if index + 1 < len(lines) else ""
        if re.match(r"^#{1,6}\s+\S", stripped_line):
            index += 1
            continue
        if next_line and re.match(r"^(?:=+|-+)\s*$", next_line):
            index += 2
            continue
        kept_lines.append(line)
        index += 1
    return "\n".join(kept_lines)


def _candidate_informational_sentences(item: dict[str, Any]) -> list[str]:
    raw_text = str(item.get("full_text", ""))
    text = (
        _remove_markdown_headings(raw_text)
        if raw_text
        else str(item.get("excerpt", "")) or str(item.get("claim", ""))
    )
    sentences = re.split(r"(?<=[.!?])\s+", _clean_text(text))
    return [
        clean_sentence
        for sentence in sentences
        if (clean_sentence := _clean_candidate_sentence(sentence))
    ]


def _sentence_supports_how_question(sentence: str, topic: str) -> bool:
    topic_pattern = _topic_pattern(topic)
    topic_then_mechanism = (
        rf"{topic_pattern}\b[^,.;:!?]{{0,120}}\b"
        r"(?:works?\s+by|uses?\s+[\w -]+\s+to|represents?|routes?|executes?|"
        r"orchestrates?|passes?\s+state|consists?\s+of)\b"
    )
    in_topic_clause = (
        rf"\bin\s+{topic_pattern}\b[^,.;:!?]{{0,160}}\b"
        r"(?:nodes?|edges?|routes?|executes?|passes?\s+state|operations?|steps?)\b"
    )
    return any(
        re.search(pattern, sentence, flags=re.IGNORECASE)
        for pattern in (topic_then_mechanism, in_topic_clause)
    )


def _sentence_supports_question(sentence: str, question_type: str, topic: str) -> bool:
    if not re.search(_topic_pattern(topic), sentence, flags=re.IGNORECASE):
        return False
    if not _is_sentence_like_claim(sentence):
        return False
    if question_type == "how":
        return _sentence_supports_how_question(sentence, topic)
    if question_type == "benefit" and not _sentence_supports_benefit_question(
        sentence,
        topic,
    ):
        return False
    support_pattern = QUESTION_SUPPORT_PATTERNS[question_type]
    return bool(support_pattern.search(sentence))


def _sentence_supports_benefit_question(sentence: str, topic: str) -> bool:
    topic_pattern = _topic_pattern(topic)
    topic_benefit = (
        rf"{topic_pattern}\b[^,.;:!?]{{0,140}}\b"
        r"(?:is\s+(?:useful|important|a\s+good\s+bridge\s+skill)|"
        r"helps?|supports?|enables?|allows?|improves?|provides?|combines?|"
        r"checks?|measures?)\b"
    )
    using_topic = (
        rf"\busing\s+{topic_pattern}\b[^,.;:!?]{{0,140}}\b"
        r"(?:helps?|supports?|enables?|allows?|improves?|provides?)\b"
    )
    return any(
        re.search(pattern, sentence, flags=re.IGNORECASE)
        for pattern in (topic_benefit, using_topic)
    )


def _is_duplicate_sentence(sentence: str, selected_sentences: list[str]) -> bool:
    sentence_terms = set(re.findall(r"[a-z0-9]+", sentence.casefold()))
    if not sentence_terms:
        return True
    for selected_sentence in selected_sentences:
        selected_terms = set(re.findall(r"[a-z0-9]+", selected_sentence.casefold()))
        if not selected_terms:
            continue
        if len(sentence_terms & selected_terms) / len(sentence_terms | selected_terms) >= 0.7:
            return True
    return False


def build_informational_answer(goal: str, reasoning_items, max_claims: int = 3) -> str:
    """Extract direct question-answering claims from retrieved evidence."""
    if max_claims <= 0:
        return ""

    shape = _informational_question_shape(goal)
    if not shape:
        return _legacy_build_informational_answer(goal, reasoning_items, max_claims)
    question_type, topic = shape

    selected_sentences = []
    for item in reasoning_items or []:
        for sentence in _candidate_informational_sentences(item):
            if not _sentence_supports_question(sentence, question_type, topic):
                continue
            clean_sentence = _clean_candidate_sentence(sentence)
            if not clean_sentence:
                continue
            if _is_duplicate_sentence(clean_sentence, selected_sentences):
                continue
            selected_sentences.append(clean_sentence.rstrip(".?!") + ".")
            if len(selected_sentences) == max_claims:
                return " ".join(selected_sentences)

    return " ".join(selected_sentences)


IDENTITY_FIELDS = ("source", "filename", "chunk_index", "page", "id", "_id", "point_id")


def _merged_identity_metadata(item: dict[str, Any]) -> dict[str, Any]:
    metadata = {}
    nested_metadata = item.get("metadata")
    if isinstance(nested_metadata, dict):
        metadata.update(nested_metadata)

    for field in IDENTITY_FIELDS:
        if item.get(field) is not None and item.get(field) != "N/A":
            metadata.setdefault(field, item[field])

    return metadata


def _document_identity_keys(metadata: dict[str, Any]) -> set[tuple[Any, ...]]:
    keys = set()
    qdrant_id = metadata.get("id") or metadata.get("_id") or metadata.get("point_id")
    if qdrant_id:
        keys.add(("id", qdrant_id))

    source = metadata.get("source")
    filename = metadata.get("filename") or (Path(str(source)).name if source else None)
    if source or filename:
        keys.add(
            (
                "meta",
                source,
                filename,
                metadata.get("chunk_index"),
                metadata.get("page"),
            )
        )

    return keys


def _reasoning_items_with_full_text(state: NoiseToSignalState) -> list[dict[str, Any]]:
    items = list(state.get("reasoning_evidence", {}).get("items", []))
    docs = list(state.get("retrieved_docs") or [])
    doc_texts = [str(getattr(doc, "page_content", "") or "") for doc in docs]
    doc_indexes_by_key: dict[tuple[Any, ...], set[int]] = {}
    for index, doc in enumerate(docs):
        for key in _document_identity_keys(getattr(doc, "metadata", {}) or {}):
            doc_indexes_by_key.setdefault(key, set()).add(index)

    enriched_items = []
    for item in items:
        enriched_item = dict(item)
        matched_indexes = set()
        has_ambiguous_key = False
        for key in _document_identity_keys(_merged_identity_metadata(item)):
            indexes = doc_indexes_by_key.get(key, set())
            if len(indexes) > 1:
                has_ambiguous_key = True
            matched_indexes.update(indexes)
        if not has_ambiguous_key and len(matched_indexes) == 1:
            matched_index = next(iter(matched_indexes))
            enriched_item["full_text"] = doc_texts[matched_index]
        enriched_items.append(enriched_item)
    return enriched_items


def build_informational_answer_from_state(
    state: NoiseToSignalState,
    goal: str,
) -> str:
    return build_informational_answer(goal, _reasoning_items_with_full_text(state))


def assess_evidence(state: NoiseToSignalState) -> NoiseToSignalState:
    """Assess retrieved evidence for the current request shape."""
    trace = list(state.get("retrieval_trace") or [])
    attempts = int(state.get("retrieval_attempts") or 0)
    decision_status = state.get("decision_status")
    reasoning_evidence = state.get("reasoning_evidence", {})
    options = state.get("options", [])
    is_retrieval_override = bool(state.get("retrieval_override"))
    attempt_label = (
        "Explicit evidence"
        if is_retrieval_override
        else f"Retrieval attempt {attempts}"
    )

    if state.get("retrieval_error"):
        trace.append("Stopped after retrieval failure.")
        evidence_reason = _retrieval_error_reason(
            state.get("retrieval_error", "retrieval_failed"),
            decision_status,
        )
        if decision_status == "single_focus":
            return {
                "evidence_quality": "failed",
                "evidence_reason": evidence_reason,
                "retrieval_trace": trace,
            }
        return {
            "decision_status": "insufficient_evidence",
            "needs_clarification": False,
            "evidence_quality": "failed",
            "evidence_reason": evidence_reason,
            "retrieval_trace": trace,
        }

    if decision_status == "informational":
        evidence_answer = build_informational_answer_from_state(state, state["goal"])
        if evidence_answer:
            if not is_retrieval_override:
                trace.append(f"{attempt_label}: sufficient.")
            return {
                "informational_answer": evidence_answer,
                "evidence_quality": "sufficient",
                "evidence_reason": "Retrieved evidence contains a direct answer claim.",
                "retrieval_trace": trace,
            }

        if not is_retrieval_override:
            trace.append(f"{attempt_label}: weak - no direct answer claim.")
        if attempts >= 2:
            trace.append("Stopped after maximum retrieval attempts.")
        return {
            "decision_status": (
                "insufficient_evidence"
                if (
                    attempts >= 2
                    or state.get("query_reformulated")
                    or is_retrieval_override
                )
                else decision_status
            ),
            "evidence_quality": "weak",
            "evidence_reason": "No direct answer claim was found.",
            "retrieval_trace": trace,
        }

    if options:
        ranked_options, unsupported_options = _ranked_options_with_support(
            options,
            reasoning_evidence,
        )
        if not unsupported_options:
            if not is_retrieval_override:
                trace.append(f"{attempt_label}: sufficient.")
            return {
                **_comparison_state_from_ranked_options(ranked_options),
                "ranked_options": ranked_options,
                "option_scores": ranked_options,
                "evidence_quality": "sufficient",
                "evidence_reason": "Every comparison option has positive support.",
                "retrieval_trace": trace,
            }

        missing_support = ", ".join(unsupported_options)
        if not is_retrieval_override:
            trace.append(
                f"{attempt_label}: weak - missing support for {missing_support}."
            )
        if attempts >= 2:
            trace.append("Stopped after maximum retrieval attempts.")
        return {
            "decision_status": (
                "insufficient_evidence"
                if (
                    attempts >= 2
                    or state.get("query_reformulated")
                    or is_retrieval_override
                )
                else decision_status
            ),
            "ranked_options": ranked_options,
            "option_scores": ranked_options,
            "selected_focus": None,
            "tied_options": [],
            "evidence_quality": "weak",
            "evidence_reason": f"Missing support for {missing_support}.",
            "retrieval_trace": trace,
        }

    if decision_status == "single_focus":
        if not _single_focus_has_domain_or_direct_support(state):
            if not is_retrieval_override:
                trace.append(
                    f"{attempt_label}: weak - focus is outside scope and not "
                    "directly supported."
                )
            return {
                "decision_status": "insufficient_evidence",
                "needs_clarification": False,
                "selected_focus": None,
                "evidence_quality": "weak",
                "evidence_reason": (
                    "The focus appears outside the AI Engineering learning scope, "
                    "and retrieved evidence does not directly support the topic."
                ),
                "retrieval_trace": trace,
            }

        if reasoning_evidence.get("has_evidence"):
            if not is_retrieval_override:
                trace.append(f"{attempt_label}: contextual.")
            return {
                "evidence_quality": "contextual",
                "evidence_reason": "Retrieved evidence can support the study-plan context.",
                "retrieval_trace": trace,
            }

        if not is_retrieval_override:
            trace.append(f"{attempt_label}: weak - no study-plan evidence.")
        if attempts >= 2:
            trace.append("Stopped after maximum retrieval attempts.")
        return {
            "evidence_quality": "weak",
            "evidence_reason": "No study-plan evidence was found.",
            "retrieval_trace": trace,
        }

    if not is_retrieval_override:
        trace.append(f"{attempt_label}: insufficient.")
    if attempts >= 2:
        trace.append("Stopped after maximum retrieval attempts.")
    return {
        "decision_status": "insufficient_evidence",
        "evidence_quality": "weak",
        "evidence_reason": "Retrieved evidence did not support the request.",
        "retrieval_trace": trace,
    }


def _informational_reformulation(goal: str) -> str:
    topic = re.sub(
        r"^(?:can|could|would)\s+you\s+explain\s+",
        "",
        goal,
        flags=re.IGNORECASE,
    )
    topic = re.sub(r"^(?:explain|describe|what\s+is)\s+", "", topic, flags=re.IGNORECASE)
    topic = _clean_text(topic).strip(" .?!")
    return f"{topic} definition purpose how it works" if topic else ""


def _comparison_reformulation(state: NoiseToSignalState) -> str:
    options = state.get("options", [])
    unsupported_options = []
    for item in state.get("ranked_options", []):
        if item.get("score", 0) <= 0:
            unsupported_options.append(item["option"])

    query_options = unsupported_options or options
    if not query_options:
        return ""

    return f"{' '.join(query_options)} skills prerequisites learning tradeoffs"


def _single_focus_reformulation(state: NoiseToSignalState) -> str:
    selected_focus = _clean_text(state.get("selected_focus") or state.get("goal", ""))
    return f"{selected_focus} skills prerequisites learning roadmap" if selected_focus else ""


def reformulate_retrieval_query(state: NoiseToSignalState) -> NoiseToSignalState:
    """Create one deterministic evidence-gap-driven retry query."""
    decision_status = state.get("decision_status")
    if state.get("options"):
        reformulated_query = _comparison_reformulation(state)
    elif decision_status == "informational":
        reformulated_query = _informational_reformulation(state["goal"])
    elif decision_status == "single_focus":
        reformulated_query = _single_focus_reformulation(state)
    else:
        reformulated_query = ""

    current_query = _clean_text(state.get("retrieval_query") or "")
    reformulated_query = _clean_text(reformulated_query)
    trace = list(state.get("retrieval_trace") or [])

    if not reformulated_query or reformulated_query.casefold() == current_query.casefold():
        trace.append("Retrieval retry skipped: reformulated query was not useful.")
        return {
            "decision_status": (
                "single_focus"
                if decision_status == "single_focus"
                else "insufficient_evidence"
            ),
            "query_reformulated": True,
            "retrieval_required": False,
            "retrieval_trace": trace,
        }

    trace.append(f"Query reformulated: {state.get('evidence_reason')}")
    return {
        "retrieval_query": reformulated_query,
        "retrieval_required": True,
        "query_reformulated": True,
        "retrieval_trace": trace,
    }


def route_after_reformulation(state: NoiseToSignalState) -> str:
    """Retry only when reformulation produced a useful query."""
    if state.get("retrieval_required"):
        return "retrieve_evidence"

    return route_by_decision_status(state)


def route_after_evidence_assessment(state: NoiseToSignalState) -> str:
    """Route after evidence assessment with a hard retrieval limit."""
    if (
        state.get("evidence_quality") == "weak"
        and int(state.get("retrieval_attempts") or 0) < 2
        and not state.get("query_reformulated")
        and not state.get("retrieval_override")
    ):
        return "reformulate_retrieval_query"

    if state.get("evidence_quality") in {"weak", "failed"}:
        if state.get("retrieval_override") and state.get("decision_status") == "single_focus":
            return "classify_deterministic_intent"
        return route_by_decision_status(state)

    return "classify_deterministic_intent"


def classify_deterministic_intent(state: NoiseToSignalState) -> NoiseToSignalState:
    """Classify the cleaned goal with the existing deterministic decision logic."""
    clean_goal = _clean_text(state.get("goal", ""))
    reasoning_evidence = state.get("reasoning_evidence", {})
    if state.get("context_only_followup"):
        focus_decision = {
            "selected_focus": None,
            "options": [],
            "ranked_options": [],
            "decision_status": "needs_clarification",
            "tied_options": [],
        }
    elif _is_self_contained_informational_question(clean_goal):
        focus_decision = {
            "selected_focus": None,
            "options": [],
            "ranked_options": [],
            "decision_status": "informational",
            "tied_options": [],
        }
    elif _is_context_only_input(clean_goal):
        focus_decision = {
            "selected_focus": None,
            "options": [],
            "ranked_options": [],
            "decision_status": "needs_clarification",
            "tied_options": [],
        }
    else:
        focus_decision = _select_decision_focus(clean_goal, reasoning_evidence)

    decision_status = focus_decision["decision_status"]
    evidence_answer = None

    if decision_status == "informational":
        evidence_answer = state.get("informational_answer")
        if not evidence_answer:
            evidence_answer = build_informational_answer_from_state(state, clean_goal)
        if not evidence_answer:
            decision_status = "insufficient_evidence"

    return {
        "goal": clean_goal,
        "selected_focus": focus_decision["selected_focus"],
        "options": focus_decision["options"],
        "ranked_options": focus_decision["ranked_options"],
        "option_scores": focus_decision["ranked_options"],
        "decision_status": decision_status,
        "needs_clarification": decision_status == "needs_clarification",
        "tied_options": focus_decision["tied_options"],
        "route_via_llm": _should_route_ambiguous_intent(clean_goal, decision_status),
        "routing_source": "deterministic",
        "routing_confidence": None,
        "routing_reason": "Deterministic routing handled a clear request.",
        "routing_attempts": 0,
        "informational_answer": evidence_answer,
    }


classify_intent = classify_deterministic_intent


def _build_llm_intent_classifier():
    provider_config = get_provider_config()
    api_key = provider_api_key(provider_config)
    if provider_config.error or not api_key:
        raise RuntimeError(provider_config.error or "The selected provider API key is missing.")

    kwargs = {
        "model": DEFAULT_MODEL.removeprefix("openai/"),
        "api_key": api_key,
        "temperature": 0,
        "timeout": 20,
    }
    if provider_base_url(provider_config):
        kwargs["base_url"] = provider_base_url(provider_config)
    chat_model = ChatOpenAI(**kwargs)
    return chat_model.with_structured_output(AmbiguousIntentClassification)


def _classify_with_default_llm(goal: str, evidence: dict[str, Any]):
    classifier = _build_llm_intent_classifier()
    evidence_summary = evidence.get("summary") or "No retrieved evidence was available."
    messages = [
        {
            "role": "system",
            "content": (
                "Classify an ambiguous learning-assistant request for routing. "
                "Return only the structured schema. Use informational for requests "
                "asking for facts or summaries, comparison only when the user is "
                "choosing between explicit alternatives, single_focus only when a "
                "concrete learning topic is clear, and needs_clarification when "
                "the request lacks enough information."
            ),
        },
        {
            "role": "user",
            "content": (
                f"User goal: {goal}\n\n"
                f"Retrieved evidence summary: {evidence_summary}\n\n"
                "If you choose comparison, include the explicit options. If you "
                "choose single_focus, include selected_focus."
            ),
        },
    ]
    return classifier.invoke(messages)


def _fallback_to_clarification(
    reason: str,
    routing_attempts: int = 0,
) -> NoiseToSignalState:
    return {
        "decision_status": "needs_clarification",
        "needs_clarification": True,
        "selected_focus": None,
        "options": [],
        "ranked_options": [],
        "option_scores": [],
        "tied_options": [],
        "route_via_llm": False,
        "routing_source": "fallback",
        "routing_confidence": 0.0,
        "routing_reason": reason,
        "routing_attempts": routing_attempts,
    }


def _normalize_llm_options(options):
    return [
        _clean_text(option).strip(" .?!")
        for option in options
        if _clean_text(option).strip(" .?!")
    ]


def _llm_classification_retry_reason(
    classification: AmbiguousIntentClassification,
) -> str | None:
    if classification.intent == "single_focus":
        selected_focus = _clean_text(classification.selected_focus)
        if not selected_focus:
            return "LLM selected a single-focus route without a usable focus."

    if classification.intent == "comparison":
        options = _normalize_llm_options(classification.options)
        if len(options) < 2:
            return "LLM selected a comparison route without enough explicit options."

    return None


def _apply_llm_intent_to_state(
    classification: AmbiguousIntentClassification,
    state: NoiseToSignalState,
    routing_attempts: int = 0,
) -> NoiseToSignalState:
    goal = state["goal"]
    reasoning_evidence = state.get("reasoning_evidence", {})

    if classification.intent == "needs_clarification":
        return {
            **_fallback_to_clarification(classification.reason),
            "routing_source": "llm",
            "routing_confidence": classification.confidence,
            "routing_attempts": routing_attempts,
        }

    if classification.intent == "informational":
        decision_status = "informational"
        evidence_answer = state.get("informational_answer")
        if not evidence_answer:
            evidence_answer = build_informational_answer_from_state(state, goal)
        if not evidence_answer:
            decision_status = "insufficient_evidence"

        return {
            "decision_status": decision_status,
            "needs_clarification": False,
            "selected_focus": None,
            "options": [],
            "ranked_options": [],
            "option_scores": [],
            "tied_options": [],
            "route_via_llm": False,
            "routing_source": "llm",
            "routing_confidence": classification.confidence,
            "routing_reason": classification.reason,
            "routing_attempts": routing_attempts,
            "informational_answer": evidence_answer,
        }

    if classification.intent == "single_focus":
        selected_focus = _clean_text(classification.selected_focus)

        return {
            "decision_status": "single_focus",
            "needs_clarification": False,
            "selected_focus": selected_focus,
            "options": [],
            "ranked_options": [],
            "option_scores": [],
            "tied_options": [],
            "route_via_llm": False,
            "routing_source": "llm",
            "routing_confidence": classification.confidence,
            "routing_reason": classification.reason,
            "routing_attempts": routing_attempts,
        }

    options = _normalize_llm_options(classification.options)
    ranked_options = _rank_decision_options(options, reasoning_evidence)
    best_option = ranked_options[0]
    best_score = best_option["score"]
    selected_focus = None
    decision_status = "insufficient_evidence"
    tied_options = []
    unsupported_options = [
        item["option"] for item in ranked_options if item["score"] <= 0
    ]

    if best_score > 0 and not unsupported_options:
        tied_options = [
            item["option"]
            for item in ranked_options
            if item["score"] == best_score
        ]
        if len(tied_options) > 1:
            decision_status = "tie"
        else:
            selected_focus = best_option["option"]
            decision_status = "selected"

    return {
        "decision_status": decision_status,
        "needs_clarification": False,
        "selected_focus": selected_focus,
        "options": options,
        "ranked_options": ranked_options,
        "option_scores": ranked_options,
        "tied_options": tied_options,
        "route_via_llm": False,
        "routing_source": "llm",
        "routing_confidence": classification.confidence,
        "routing_reason": classification.reason,
        "routing_attempts": routing_attempts,
    }


def classify_ambiguous_intent_with_llm(
    state: NoiseToSignalState,
    intent_classifier=None,
) -> NoiseToSignalState:
    """Use one structured LLM classification for genuinely ambiguous routing."""
    classifier = intent_classifier or _classify_with_default_llm
    fallback_reason = "LLM intent classification failed; asking for clarification."

    for attempt in range(1, 3):
        try:
            raw_result = classifier(state["goal"], state.get("evidence", {}))
        except Exception:
            fallback_reason = "LLM intent classification failed; asking for clarification."
            continue

        try:
            classification = AmbiguousIntentClassification.model_validate(raw_result)
        except ValidationError:
            fallback_reason = (
                "LLM returned invalid structured output; asking for clarification."
            )
            continue

        if classification.intent not in LLM_ROUTABLE_INTENTS:
            fallback_reason = "LLM returned an unsupported intent; asking for clarification."
            continue

        retry_reason = _llm_classification_retry_reason(classification)
        if retry_reason:
            fallback_reason = retry_reason
            continue

        return _apply_llm_intent_to_state(
            classification,
            state,
            routing_attempts=attempt,
        )

    return _fallback_to_clarification(fallback_reason, routing_attempts=2)


def route_after_deterministic_intent(state: NoiseToSignalState) -> str:
    """Route clear deterministic requests or send ambiguous ones to the LLM node."""
    if state.get("route_via_llm"):
        return "classify_ambiguous_intent_with_llm"

    return route_by_decision_status(state)


def route_by_decision_status(state: NoiseToSignalState) -> str:
    """Return the output node for the current decision status."""
    decision_status = state.get("decision_status")

    if decision_status not in SUPPORTED_DECISION_STATUSES:
        raise ValueError(f"Unknown decision status: {decision_status}")

    if decision_status == "informational":
        return "answer_informational"

    if decision_status == "needs_clarification":
        return "request_clarification"

    if decision_status == "single_focus":
        return "plan_for_focus"

    if decision_status in {"selected", "tie"}:
        return "respond_comparison"

    return "respond_insufficient"


def _with_trace(
    state: NoiseToSignalState,
    reasoning: str,
    recommendation: str,
    next_action: str,
) -> NoiseToSignalState:
    selected_focus = state.get("selected_focus")
    decision_status = state["decision_status"]

    return {
        "recommendation": recommendation,
        "next_action": next_action,
        "decision_trace": [
            f"User goal: {state['goal']}",
            *list(state.get("retrieval_trace") or []),
            f"Decision status: {decision_status}",
            f"Interpreted focus: {selected_focus or 'none'}",
            f"Short evidence-based reasoning: {reasoning}",
            f"Selected focus: {selected_focus or 'none'}",
            f"Next action: {next_action}",
        ],
    }


def _build_study_plan_for_focus(state: NoiseToSignalState):
    evidence = state.get("evidence", {})
    evidence_summary = (
        " ".join(evidence["claims"])
        if evidence.get("has_evidence") and evidence.get("claims")
        else None
    )

    return generate_study_plan(
        topic=state["selected_focus"],
        available_time=60,
        energy_level="medium",
        current_level="intermediate",
        evidence_summary=evidence_summary,
    )


def answer_informational(state: NoiseToSignalState) -> NoiseToSignalState:
    """Answer an informational question from retrieved evidence."""
    evidence_answer = state.get("informational_answer")
    if not evidence_answer:
        evidence_answer = build_informational_answer_from_state(state, state["goal"])

    if not evidence_answer:
        raise ValueError("Informational route requires a usable evidence answer.")

    reasoning = (
        "The user asked an informational question, so the response answers "
        "from retrieved evidence instead of selecting a study focus."
    )
    recommendation = f"Based on the retrieved evidence: {evidence_answer}"
    next_action = (
        "Choose one identified skill to compare against your current goals, or "
        "ask for a study plan for that specific skill."
    )
    return _with_trace(state, reasoning, recommendation, next_action)


def request_clarification(state: NoiseToSignalState) -> NoiseToSignalState:
    """Ask for a clearer learning target when no focus can be inferred."""
    reasoning = (
        "The goal is too broad to turn into a concrete study topic without more "
        "context."
    )
    clarification_context = state.get("clarification_context")
    goal = _clean_text(state.get("goal", ""))
    guided_intake_entry_point = state.get("guided_intake_entry_point")
    if guided_intake_entry_point:
        recommendation = (
            "I need a little learner profile context before choosing a "
            "learning path."
        )
        next_action = (
            "Add your current level, current skills, interests, preferred work "
            "style, target role if known, and available learning time."
        )
    elif clarification_context:
        context_display = _format_clarification_context_for_display(
            clarification_context
        )
        recommendation = (
            f'For the context "{context_display}," please add a concrete '
            "skill, domain, project, or learning decision."
        )
        next_action = (
            "Add a concrete skill, domain, project, or comparison you want help "
            "prioritizing, then rerun the decision."
        )
    elif _is_standalone_proficiency_level(goal):
        recommendation = (
            f"{goal} in which skill or domain? Please add the technology, role, "
            "or project you want to improve."
        )
        next_action = (
            "Add the skill, domain, role, or project this level refers to, then "
            "rerun the decision."
        )
    elif _is_short_role_like_input(goal):
        recommendation = (
            f"Is {goal} your target role? Add a concrete skill, project, or "
            "learning decision you want help prioritizing."
        )
        next_action = (
            "Add a concrete skill, project, or learning decision for this role, "
            "then rerun the decision."
        )
    else:
        recommendation = (
            "Please provide a target role, project, or skill area before choosing a "
            "study plan."
        )
        next_action = (
            "Add a target role, project, or skill area, then rerun the decision."
        )
    return {
        **_with_trace(state, reasoning, recommendation, next_action),
        "original_goal": state.get("original_goal") or state["goal"],
        "pending_clarification": True,
        "clarification_context": clarification_context,
    }


def plan_for_focus(state: NoiseToSignalState) -> NoiseToSignalState:
    """Respond when the user already supplied one concrete learning focus."""
    selected_focus = state.get("selected_focus")
    reasoning = (
        f"The user provided one explicit topic: {selected_focus}. The app can "
        "generate a study plan, but the retrieved evidence is not being used to "
        "choose between alternatives."
    )
    recommendation = (
        f"Build a study plan for {selected_focus}. This plan is not strongly "
        "evidence-grounded unless retrieved evidence is shown below."
    )
    next_action = (
        "Use the plan as a learning scaffold, then retrieve stronger evidence "
        "before treating it as a market-priority decision."
    )
    return {
        **_with_trace(state, reasoning, recommendation, next_action),
        "study_plan": _build_study_plan_for_focus(state),
    }


def respond_comparison(state: NoiseToSignalState) -> NoiseToSignalState:
    """Respond to selected-option or tied comparison decisions."""
    decision_status = state["decision_status"]

    if decision_status == "tie":
        tied_options = ", ".join(state.get("tied_options", []))
        reasoning = (
            f"Retrieved evidence gives equal positive support to: {tied_options}. "
            "Choosing the first option would hide a real tie."
        )
        recommendation = (
            f"Evidence is tied between {tied_options}. Choose a tie-breaking "
            "criterion before creating a study plan."
        )
        next_action = (
            "Pick a tie-breaker such as immediate project value, job-market "
            "relevance, or available learning time, then rerun the decision."
        )
        return _with_trace(state, reasoning, recommendation, next_action)

    if decision_status != "selected":
        raise ValueError(f"Comparison response cannot handle status: {decision_status}")

    selected_focus = state.get("selected_focus")
    ranked_options = state.get("ranked_options", [])
    other_options = [item["option"] for item in ranked_options[1:]]
    comparison = (
        f" It ranks above {', '.join(other_options)} because the retrieved "
        "evidence contains stronger matching signals for this option."
        if other_options
        else " Retrieved evidence is not strong enough to separate the options clearly."
    )
    reasoning = (
        f"Retrieved evidence gives {selected_focus} the strongest deterministic "
        f"score among the listed options.{comparison}"
    )
    recommendation = (
        f"Focus on {selected_focus}. Prioritize one practical skill path that is "
        "supported by the retrieved evidence and can produce a portfolio-ready "
        "result this week."
    )
    next_action = (
        "Choose one small implementation task, complete a 60-minute practice "
        "session, and write down the evidence-backed reason for choosing it."
    )
    return {
        **_with_trace(state, reasoning, recommendation, next_action),
        "study_plan": _build_study_plan_for_focus(state),
    }


def respond_insufficient(state: NoiseToSignalState) -> NoiseToSignalState:
    """Respond when evidence cannot support the requested answer or comparison."""
    if _is_informational_question(state["goal"]) or not state.get("options"):
        reasoning = (
            "The user asked an informational question, but no usable "
            "knowledge-base evidence was retrieved."
        )
        recommendation = (
            "The retrieved evidence is insufficient to answer this question reliably. "
            "Refine the question or add evidence that directly addresses the topic."
        )
        next_action = (
            "Try a more specific source, report section, role, or skill area, "
            "then retrieve evidence again."
        )
    else:
        reasoning = (
            "The retrieved evidence does not give positive support to any listed "
            "option, so selecting the first option would be arbitrary."
        )
        recommendation = (
            "Evidence is insufficient to choose among the listed options. Refine the "
            "query or retrieve stronger evidence before creating an option-specific "
            "study plan."
        )
        next_action = (
            "Rewrite the goal with a clearer role, project outcome, or evidence "
            "source, then retrieve evidence again."
        )

    return _with_trace(state, reasoning, recommendation, next_action)


def _build_graph(
    intent_classifier=None,
    retriever=retrieve_relevant_chunks,
    checkpointer=None,
):
    graph = StateGraph(NoiseToSignalState)
    graph.add_node("reset_retrieval_state", reset_retrieval_state)
    graph.add_node("resolve_clarification_context", resolve_clarification_context)
    graph.add_node("determine_request_shape", determine_request_shape)
    graph.add_node(
        "retrieve_evidence",
        lambda state: retrieve_evidence(state, retriever),
    )
    graph.add_node("prepare_evidence", prepare_evidence)
    graph.add_node("assess_evidence", assess_evidence)
    graph.add_node("reformulate_retrieval_query", reformulate_retrieval_query)
    graph.add_node("classify_deterministic_intent", classify_deterministic_intent)
    graph.add_node(
        "classify_ambiguous_intent_with_llm",
        lambda state: classify_ambiguous_intent_with_llm(state, intent_classifier),
    )
    graph.add_node("answer_informational", answer_informational)
    graph.add_node("request_clarification", request_clarification)
    graph.add_node("plan_for_focus", plan_for_focus)
    graph.add_node("respond_comparison", respond_comparison)
    graph.add_node("respond_insufficient", respond_insufficient)

    graph.add_edge(START, "reset_retrieval_state")
    graph.add_edge("reset_retrieval_state", "resolve_clarification_context")
    graph.add_edge("resolve_clarification_context", "determine_request_shape")
    graph.add_conditional_edges(
        "determine_request_shape",
        route_after_request_shape,
        {
            "request_clarification": "request_clarification",
            "retrieve_evidence": "retrieve_evidence",
            "prepare_evidence": "prepare_evidence",
        },
    )
    graph.add_edge("retrieve_evidence", "prepare_evidence")
    graph.add_edge("prepare_evidence", "assess_evidence")
    graph.add_conditional_edges(
        "assess_evidence",
        route_after_evidence_assessment,
        {
            "reformulate_retrieval_query": "reformulate_retrieval_query",
            "classify_deterministic_intent": "classify_deterministic_intent",
            "answer_informational": "answer_informational",
            "request_clarification": "request_clarification",
            "plan_for_focus": "plan_for_focus",
            "respond_comparison": "respond_comparison",
            "respond_insufficient": "respond_insufficient",
        },
    )
    graph.add_conditional_edges(
        "reformulate_retrieval_query",
        route_after_reformulation,
        {
            "retrieve_evidence": "retrieve_evidence",
            "answer_informational": "answer_informational",
            "request_clarification": "request_clarification",
            "plan_for_focus": "plan_for_focus",
            "respond_comparison": "respond_comparison",
            "respond_insufficient": "respond_insufficient",
        },
    )
    graph.add_conditional_edges(
        "classify_deterministic_intent",
        route_after_deterministic_intent,
        {
            "classify_ambiguous_intent_with_llm": "classify_ambiguous_intent_with_llm",
            "answer_informational": "answer_informational",
            "request_clarification": "request_clarification",
            "plan_for_focus": "plan_for_focus",
            "respond_comparison": "respond_comparison",
            "respond_insufficient": "respond_insufficient",
        },
    )
    graph.add_conditional_edges(
        "classify_ambiguous_intent_with_llm",
        route_by_decision_status,
        {
            "answer_informational": "answer_informational",
            "request_clarification": "request_clarification",
            "plan_for_focus": "plan_for_focus",
            "respond_comparison": "respond_comparison",
            "respond_insufficient": "respond_insufficient",
        },
    )
    graph.add_edge("answer_informational", END)
    graph.add_edge("request_clarification", END)
    graph.add_edge("plan_for_focus", END)
    graph.add_edge("respond_comparison", END)
    graph.add_edge("respond_insufficient", END)

    return graph.compile(checkpointer=checkpointer)


NOISE_TO_SIGNAL_CHECKPOINTER = MemorySaver()
NOISE_TO_SIGNAL_GRAPH = _build_graph()


@traceable(name="skill_compass_noise_to_signal")
def run_noise_to_signal(
    goal,
    retrieved_docs=None,
    intent_classifier=None,
    retriever=retrieve_relevant_chunks,
    thread_id: str | None = None,
    checkpointer=None,
):
    """Run the Noise-to-Signal graph for a cleaned goal.

    Args:
        goal: User learning goal or decision question as a string.
        retrieved_docs: Optional explicit evidence document override. When omitted,
            the graph retrieves internally through the configured retriever.
        intent_classifier: Optional test seam for ambiguous intent routing. When
            omitted, the graph uses the configured OpenRouter chat model.
        retriever: Optional retrieval dependency seam. Production uses the existing
            Qdrant-backed retriever; tests can pass a fake callable.
        thread_id: Optional LangGraph checkpoint thread ID for short-term memory.
        checkpointer: Optional test seam for isolated checkpoint memory.

    Returns:
        Final graph state as a plain dictionary compatible with the app renderer.

    Raises:
        TypeError: If goal is not a string or retrieved_docs is not a supported
            document collection.
        ValueError: If the cleaned goal is empty or the graph sees an unsupported
            decision status.
    """
    if not isinstance(goal, str):
        raise TypeError("goal must be a string")

    clean_goal = _clean_text(goal)
    if not clean_goal:
        raise ValueError("goal must not be empty")

    if retrieved_docs is not None and not isinstance(retrieved_docs, (list, tuple)):
        raise TypeError("retrieved_docs must be a list or tuple")

    retrieval_override = retrieved_docs is not None
    retrieved_docs_list = list(retrieved_docs or [])

    if thread_id:
        graph = _build_graph(
            intent_classifier=intent_classifier,
            retriever=retriever,
            checkpointer=checkpointer or NOISE_TO_SIGNAL_CHECKPOINTER,
        )
        config = {"configurable": {"thread_id": thread_id}}
    else:
        graph = (
            _build_graph(intent_classifier=intent_classifier, retriever=retriever)
            if intent_classifier or retriever is not retrieve_relevant_chunks
            else NOISE_TO_SIGNAL_GRAPH
        )
        config = None

    result = graph.invoke(
        {
            "goal": clean_goal,
            "retrieved_docs": retrieved_docs_list,
            "retrieval_override": retrieval_override,
        },
        config=config,
    )
    return dict(result)
