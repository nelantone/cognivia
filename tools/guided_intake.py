"""Guided learner intake helpers."""

from typing import Any, TypedDict

from tools.study_plan import generate_study_plan, summarize_retrieved_evidence

ENTRY_POINTS = (
    "I feel lost and need direction",
    "I know the role I want",
    "I want to choose what to learn next",
    "I want to study/practice a topic",
)
CURRENT_LEVEL_OPTIONS = ("beginner", "intermediate", "advanced")
PREFERRED_WORK_STYLES = (
    "Build useful AI products",
    "Automate workflows",
    "Evaluate and improve AI quality",
    "Build backend integrations",
    "Deploy reliable systems",
    "Improve code quality with AI",
    "Explore research and foundations",
)

ENTRY_POINT_DEFAULT_BRANCHES = {
    "I feel lost and need direction": "RAG / LLM Applications",
    "I know the role I want": "AI Backend / Integration",
    "I want to choose what to learn next": "RAG / LLM Applications",
    "I want to study/practice a topic": "AI Evaluation / Quality",
}

PREFERRED_WORK_STYLE_BRANCHES = {
    "Build useful AI products": "RAG / LLM Applications",
    "Automate workflows": "Agents / Workflow Automation",
    "Evaluate and improve AI quality": "AI Evaluation / Quality",
    "Build backend integrations": "AI Backend / Integration",
    "Deploy reliable systems": "MLOps / Deployment",
    "Improve code quality with AI": "Human-AI Coding / Code Quality",
    "Explore research and foundations": "AI Evaluation / Quality",
}

BRANCH_DATA = {
    "RAG / LLM Applications": {
        "terms": (
            "rag",
            "retrieval",
            "documents",
            "search",
            "chat",
            "llm application",
            "product",
            "question answering",
        ),
        "career_paths": (
            "AI Application Engineer",
            "LLM Application Developer",
            "AI Backend Engineer",
        ),
        "required_skills": (
            "prompting",
            "embeddings",
            "retrieval",
            "chunking",
            "citations",
            "RAG evaluation",
        ),
    },
    "Agents / Workflow Automation": {
        "terms": (
            "agent",
            "automation",
            "workflow",
            "tool calling",
            "multi-step",
            "orchestration",
        ),
        "career_paths": (
            "Agentic Workflow Engineer",
            "AI Automation Engineer",
            "Developer Productivity Engineer",
        ),
        "required_skills": (
            "tool calling",
            "state management",
            "routing",
            "guardrails",
            "workflow evaluation",
        ),
    },
    "AI Evaluation / Quality": {
        "terms": (
            "evaluation",
            "eval",
            "quality",
            "testing",
            "reliability",
            "hallucination",
            "grounding",
        ),
        "career_paths": (
            "AI Evaluation Engineer",
            "AI Quality Engineer",
            "Responsible AI Engineer",
        ),
        "required_skills": (
            "evaluation rubrics",
            "test datasets",
            "groundedness checks",
            "failure analysis",
            "regression tests",
        ),
    },
    "AI Backend / Integration": {
        "terms": (
            "backend",
            "api",
            "integration",
            "python",
            "service",
            "data flow",
            "provider",
        ),
        "career_paths": (
            "AI Backend Engineer",
            "AI Application Engineer",
            "AI Platform Engineer",
        ),
        "required_skills": (
            "Python APIs",
            "input validation",
            "provider integration",
            "safe error handling",
            "logging",
        ),
    },
    "MLOps / Deployment": {
        "terms": (
            "deployment",
            "mlops",
            "operations",
            "monitoring",
            "docker",
            "cloud",
            "production",
            "ci",
        ),
        "career_paths": (
            "MLOps Engineer",
            "AI Platform Engineer",
            "AI Backend Engineer",
        ),
        "required_skills": (
            "deployment",
            "configuration",
            "CI checks",
            "monitoring",
            "health checks",
        ),
    },
    "Human-AI Coding / Code Quality": {
        "terms": (
            "code quality",
            "review",
            "refactor",
            "maintainable",
            "coding assistant",
            "ai-generated code",
            "clean code",
        ),
        "career_paths": (
            "Developer Productivity Engineer",
            "AI Quality Engineer",
            "Software Engineer, AI Products",
        ),
        "required_skills": (
            "code review",
            "refactoring",
            "tests",
            "debugging AI output",
            "maintainability",
        ),
    },
}


class LearnerProfile(TypedDict):
    """Structured learner intake fields."""

    entry_point: str
    current_level: str
    current_skills: list[str]
    interests: list[str]
    preferred_work_style: str
    target_role: str | None
    goal: str
    time_available_minutes: int


class GuidedIntakeRecommendation(TypedDict):
    """Structured guided intake output for the app."""

    learner_profile: LearnerProfile
    rag_query: str
    recommended_direction: str
    possible_ai_career_paths: list[str]
    skill_gap: list[str]
    learning_path_outline: list[str]
    next_action: str
    evidence_note: str
    evidence_used: list[dict[str, Any]]


def _clean_text(value: object) -> str:
    return " ".join(str(value or "").split())


def _split_items(value: str | list[str] | tuple[str, ...]) -> list[str]:
    if isinstance(value, str):
        raw_items = value.replace("\n", ",").split(",")
    else:
        raw_items = value

    return [clean_item for item in raw_items if (clean_item := _clean_text(item))]


def build_learner_profile(
    entry_point: str,
    current_level: str,
    current_skills: str | list[str] | tuple[str, ...],
    interests: str | list[str] | tuple[str, ...],
    preferred_work_style: str,
    target_role: str | None,
    goal: str,
    time_available_minutes: int,
) -> LearnerProfile:
    """Build and validate the structured learner profile from intake fields."""
    clean_entry_point = _clean_text(entry_point)
    clean_current_level = _clean_text(current_level).lower()
    clean_work_style = _clean_text(preferred_work_style)
    clean_goal = _clean_text(goal)
    clean_target_role = _clean_text(target_role)
    clean_current_skills = _split_items(current_skills)
    clean_interests = _split_items(interests)

    if clean_entry_point not in ENTRY_POINTS:
        raise ValueError("entry_point must be one of the guided intake options.")

    if clean_current_level not in CURRENT_LEVEL_OPTIONS:
        raise ValueError("current_level must be beginner, intermediate, or advanced.")

    if clean_work_style not in PREFERRED_WORK_STYLES:
        raise ValueError("preferred_work_style must be one of the guided options.")

    if not clean_current_skills:
        raise ValueError("current_skills is required.")

    if not clean_interests:
        raise ValueError("interests is required.")

    if not clean_goal:
        raise ValueError("goal is required.")

    if time_available_minutes <= 0:
        raise ValueError("time_available_minutes must be greater than 0.")

    return {
        "entry_point": clean_entry_point,
        "current_level": clean_current_level,
        "current_skills": clean_current_skills,
        "interests": clean_interests,
        "preferred_work_style": clean_work_style,
        "target_role": clean_target_role or None,
        "goal": clean_goal,
        "time_available_minutes": int(time_available_minutes),
    }


def build_guided_intake_query(profile: LearnerProfile) -> str:
    """Build a retrieval query from the learner profile."""
    skills = ", ".join(profile["current_skills"]) or "unspecified skills"
    interests = ", ".join(profile["interests"]) or "unspecified interests"
    target_role = profile["target_role"] or "unknown target role"

    return (
        "AI engineering learning path and career skill evidence for "
        f"{profile['goal']}. Entry point: {profile['entry_point']}. "
        f"Current level: {profile['current_level']}. "
        f"Current skills: {skills}. Interests: {interests}. "
        f"Preferred work style: {profile['preferred_work_style']}. "
        f"Target role or direction: {target_role}. Include role direction, "
        "skill gaps, learning path, next action, and evidence."
    )


def _profile_text(profile: LearnerProfile) -> str:
    return " ".join(
        [
            profile["entry_point"],
            profile["current_level"],
            " ".join(profile["current_skills"]),
            " ".join(profile["interests"]),
            profile["preferred_work_style"],
            profile["target_role"] or "",
            profile["goal"],
        ]
    ).lower()


def _score_branch(branch_name: str, profile: LearnerProfile) -> int:
    profile_text = _profile_text(profile)
    branch_data = BRANCH_DATA[branch_name]
    score = 0

    if PREFERRED_WORK_STYLE_BRANCHES[profile["preferred_work_style"]] == branch_name:
        score += 6

    if ENTRY_POINT_DEFAULT_BRANCHES[profile["entry_point"]] == branch_name:
        score += 2

    for term in branch_data["terms"]:
        if term in profile_text:
            score += 2 if " " in term else 1

    for career_path in branch_data["career_paths"]:
        if career_path.lower() in profile_text:
            score += 4

    return score


def recommend_direction(profile: LearnerProfile) -> str:
    """Choose a practical AI learning direction from profile signals."""
    default_branch = ENTRY_POINT_DEFAULT_BRANCHES[profile["entry_point"]]
    scored_branches = sorted(
        (
            (_score_branch(branch_name, profile), branch_name)
            for branch_name in BRANCH_DATA
        ),
        key=lambda item: (-item[0], item[1]),
    )

    best_score, best_branch = scored_branches[0]
    if best_score <= 0:
        return default_branch

    return best_branch


def _skill_terms(skill_name: str) -> set[str]:
    return {
        term
        for term in skill_name.lower().replace("/", " ").split()
        if len(term) > 2
    }


def _profile_has_skill(profile: LearnerProfile, skill_name: str) -> bool:
    current_skill_text = " ".join(profile["current_skills"]).lower()
    return any(term in current_skill_text for term in _skill_terms(skill_name))


def estimate_skill_gap(profile: LearnerProfile, direction: str) -> list[str]:
    """Return branch skills not already signaled in the learner profile."""
    required_skills = BRANCH_DATA[direction]["required_skills"]
    missing_skills = [
        skill for skill in required_skills if not _profile_has_skill(profile, skill)
    ]

    if missing_skills:
        return list(missing_skills[:4])

    return [
        "Turn the current skills into a small portfolio artifact with an "
        "evidence-backed reflection."
    ]


def _build_learning_path_outline(
    profile: LearnerProfile,
    direction: str,
    evidence_summary: str | None,
) -> list[str]:
    topic = direction
    if profile["entry_point"] == "I want to study/practice a topic":
        topic = profile["goal"]

    plan = generate_study_plan(
        topic=topic,
        available_time=profile["time_available_minutes"],
        energy_level="medium",
        current_level=profile["current_level"],
        evidence_summary=evidence_summary,
    )

    return [step["step"] for step in plan["steps"]]


def _build_evidence_note(evidence: dict[str, Any]) -> str:
    if not evidence["has_evidence"]:
        return (
            "No retrieved knowledge-base evidence was available for this profile. "
            "Treat this as a profile-based draft, not evidence-backed guidance."
        )

    return (
        "The recommended direction is based on the learner profile. "
        "Retrieved knowledge-base evidence was used to support and frame the "
        "learning path. "
        "Career paths are directional signals, not hiring guarantees."
    )


def build_guided_intake_recommendation(
    profile: LearnerProfile,
    retrieved_docs: list[Any] | None = None,
) -> GuidedIntakeRecommendation:
    """Build the structured guided intake recommendation from profile and RAG docs."""
    evidence = summarize_retrieved_evidence(retrieved_docs or [])
    direction = recommend_direction(profile)
    evidence_summary = evidence["summary"] if evidence["has_evidence"] else None
    learning_path_outline = _build_learning_path_outline(
        profile,
        direction,
        evidence_summary,
    )

    return {
        "learner_profile": profile,
        "rag_query": build_guided_intake_query(profile),
        "recommended_direction": direction,
        "possible_ai_career_paths": list(BRANCH_DATA[direction]["career_paths"]),
        "skill_gap": estimate_skill_gap(profile, direction),
        "learning_path_outline": learning_path_outline,
        "next_action": learning_path_outline[0],
        "evidence_note": _build_evidence_note(evidence),
        "evidence_used": evidence["items"],
    }
