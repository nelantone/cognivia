"""Deterministic learning direction schema helpers."""

from __future__ import annotations

from typing import Any, TypedDict


class LearningDirectionSchema(TypedDict):
    """User-facing learning path option shown in the app."""

    id: str
    title: str
    subtitle: str
    current_state: str
    target_outcome: str
    fit_reason: str
    nodes: list[str]
    first_action: str
    checkpoint: str
    risk_or_gap: str


def _clean_text(value: object) -> str:
    return " ".join(str(value or "").split())


def _focus_from_goal(goal: str) -> str:
    clean_goal = _clean_text(goal)
    lower_goal = clean_goal.lower()

    has_langgraph = "langgraph" in lower_goal
    has_rag_evaluation = "rag evaluation" in lower_goal or (
        "rag" in lower_goal and "evaluat" in lower_goal
    )
    has_backend = "backend" in lower_goal
    has_ai_engineering = "ai engineering" in lower_goal or "ai engineer" in lower_goal

    if has_langgraph and has_rag_evaluation:
        return (
            "LangGraph vs RAG evaluation for AI engineering decisions: "
            "workflow orchestration, evaluation metrics, and a bridge path"
        )
    if has_rag_evaluation:
        return (
            "RAG evaluation: retrieval relevance, answer quality, "
            "source grounding, and production confidence"
        )
    if has_backend and has_ai_engineering:
        return (
            "backend-to-AI engineering transition: Python APIs, LLM app "
            "integration, RAG, and evaluation"
        )
    if has_langgraph:
        return "LangGraph stateful AI workflows and tool orchestration"
    if has_backend:
        return "backend-to-AI application engineering transition"
    if "what should i learn next" in lower_goal or "what to learn next" in lower_goal:
        return (
            "diagnosing your next AI engineering skill from goals, strengths, "
            "and constraints"
        )

    return clean_goal


def _focus_from_decision(decision: dict[str, Any] | None, goal: str) -> str:
    prompt_focus = _focus_from_goal(goal)
    if prompt_focus and prompt_focus != _clean_text(goal):
        return prompt_focus

    if not decision:
        return prompt_focus or goal

    for key in ("selected_focus", "recommended_direction", "recommendation", "next_action"):
        value = _clean_text(decision.get(key))
        if value:
            return value

    return prompt_focus or goal


def _current_state(decision: dict[str, Any] | None, goal: str) -> str:
    if not decision:
        return f"You are starting from the goal: {goal}."

    status = _clean_text(decision.get("decision_status")).replace("_", " ")
    evidence_quality = _clean_text(decision.get("evidence_quality")).replace("_", " ")
    if status and evidence_quality:
        return f"Current decision: {status}; evidence: {evidence_quality}."
    if status:
        return f"Current decision: {status}."
    return f"You are starting from the goal: {goal}."


def _is_backend_ai_transition(focus: str) -> bool:
    lower_focus = focus.lower()
    return "backend" in lower_focus and (
        "ai engineering" in lower_focus
        or "ai engineer" in lower_focus
        or "llm" in lower_focus
        or "rag" in lower_focus
    )


def _backend_ai_transition_schemas(current_state: str) -> list[LearningDirectionSchema]:
    return [
        {
            "id": "foundation_first",
            "title": "Foundation-first path",
            "subtitle": "Map your backend strengths to AI gaps",
            "current_state": current_state,
            "target_outcome": (
                "Know how your backend experience transfers into a backend-to-AI "
                "engineering transition and which AI-specific gaps to close first."
            ),
            "fit_reason": (
                "Best when you already have production backend experience and need "
                "a focused bridge into LLM APIs, embeddings, retrieval, RAG, and evaluation."
            ),
            "nodes": [
                "Backend experience",
                "Map transferable skills",
                "Identify AI gaps",
                "Choose one build target",
                "Checkpoint",
            ],
            "first_action": (
                "Map your backend skills in APIs, databases, testing, deployment, "
                "and observability to the AI application stack, then identify the "
                "three highest-priority gaps."
            ),
            "checkpoint": (
                "You can explain which backend skills transfer directly and which "
                "AI gaps need practice: LLM APIs, embeddings, retrieval, RAG, evaluation, "
                "safety, or agent patterns."
            ),
            "risk_or_gap": (
                "May stay too theoretical unless you quickly connect the map to a "
                "small AI application."
            ),
        },
        {
            "id": "project_first",
            "title": "Project-first path",
            "subtitle": "Learn by shipping an AI backend",
            "current_state": current_state,
            "target_outcome": (
                "Build a deployable AI-enabled backend slice that integrates a model "
                "API, validation, and one evaluation check."
            ),
            "fit_reason": (
                "Best when you learn fastest by extending familiar backend workflows "
                "into practical AI application engineering."
            ),
            "nodes": [
                "Backend service",
                "Add LLM API integration",
                "Validate structured output or RAG",
                "Add evaluation",
                "Checkpoint",
            ],
            "first_action": (
                "Build a minimal AI-enabled backend endpoint using an LLM API, "
                "input validation, structured output or RAG, and one evaluation check."
            ),
            "checkpoint": (
                "You have a runnable endpoint with a clear request/response contract, "
                "basic validation, a small evaluation case, and notes on deployment "
                "or observability trade-offs."
            ),
            "risk_or_gap": (
                "Can hide missing AI fundamentals if the endpoint ships without "
                "evaluation, grounding checks, or safety constraints."
            ),
        },
        {
            "id": "interview_practical",
            "title": "Interview/practical path",
            "subtitle": "Prepare transition-ready examples",
            "current_state": current_state,
            "target_outcome": (
                "Explain how backend production skills apply to AI systems and show "
                "credible examples of RAG, evaluation, safety, and observability trade-offs."
            ),
            "fit_reason": (
                "Best when your near-term goal is role transition clarity, interview "
                "readiness, or job-facing portfolio language."
            ),
            "nodes": [
                "Backend production example",
                "AI system design trade-off",
                "Evaluation and safety story",
                "Portfolio explanation",
                "Checkpoint",
            ],
            "first_action": (
                "Draft one transition story that connects a backend system you know "
                "to an AI application with model integration, retrieval or structured "
                "outputs, evaluation, deployment, and observability."
            ),
            "checkpoint": (
                "You can describe a backend-to-AI architecture, the failure modes you "
                "would test, and how you would monitor it in production."
            ),
            "risk_or_gap": (
                "May become interview-only practice unless paired with a small shipped artifact."
            ),
        },
    ]


def generate_learning_direction_schemas(
    goal: str,
    decision: dict[str, Any] | None = None,
) -> list[LearningDirectionSchema]:
    """Create deterministic, offline-safe learning direction schemas."""
    clean_goal = _clean_text(goal) or "your learning goal"
    focus = _focus_from_decision(decision, clean_goal)
    current_state = _current_state(decision, clean_goal)

    if _is_backend_ai_transition(focus):
        return _backend_ai_transition_schemas(current_state)

    return [
        {
            "id": "foundation_first",
            "title": "Foundation-first path",
            "subtitle": "Build the basics first",
            "current_state": current_state,
            "target_outcome": f"Understand the core concepts behind {focus}.",
            "fit_reason": (
                "Best when the topic still feels fuzzy or you need stronger "
                "vocabulary before building."
            ),
            "nodes": [
                "You are here",
                "Name the core gap",
                "Learn one key concept",
                "Explain it in your own words",
                "Checkpoint",
            ],
            "first_action": f"Write a five-sentence plain-language summary of {focus}.",
            "checkpoint": "You can explain the concept and one practical use case.",
            "risk_or_gap": "May feel slow if you already understand the basics.",
        },
        {
            "id": "project_first",
            "title": "Project-first path",
            "subtitle": "Learn by shipping",
            "current_state": current_state,
            "target_outcome": f"Turn {focus} into a small working artifact.",
            "fit_reason": (
                "Best when you learn by building and need portfolio evidence "
                "rather than more reading."
            ),
            "nodes": [
                "You are here",
                "Pick a tiny scope",
                "Build one working slice",
                "Document trade-offs",
                "Checkpoint",
            ],
            "first_action": f"Define a one-hour mini project that uses {focus}.",
            "checkpoint": "You have a runnable demo or notebook plus short notes.",
            "risk_or_gap": "Can hide missing foundations if the project is too broad.",
        },
        {
            "id": "interview_practical",
            "title": "Interview/practical path",
            "subtitle": "Prepare to explain tradeoffs",
            "current_state": current_state,
            "target_outcome": f"Use {focus} in job-facing explanations and decisions.",
            "fit_reason": (
                "Best when your near-term goal is interview readiness, clearer "
                "trade-off language, or practical workplace use."
            ),
            "nodes": [
                "You are here",
                "Identify one practical scenario",
                "Practice a trade-off answer",
                "Apply it to a role task",
                "Checkpoint",
            ],
            "first_action": f"Draft one interview-style answer about when to use {focus}.",
            "checkpoint": "You can explain benefits, limits, and a concrete example.",
            "risk_or_gap": "May skip deeper practice if you only rehearse answers.",
        },
    ]
