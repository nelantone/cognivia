"""Tests for guided learner intake helpers."""

import pytest
from langchain_core.documents import Document

from tools.guided_intake import (
    ENTRY_POINTS,
    PREFERRED_WORK_STYLES,
    build_guided_intake_query,
    build_guided_intake_recommendation,
    build_learner_profile,
    estimate_skill_gap,
    recommend_direction,
)


def _profile(**overrides):
    values = {
        "entry_point": ENTRY_POINTS[0],
        "current_level": "beginner",
        "current_skills": "Python, APIs, basic prompting",
        "interests": "document Q&A, useful AI products",
        "preferred_work_style": PREFERRED_WORK_STYLES[0],
        "target_role": "AI Application Engineer",
        "goal": "I feel lost and want a practical AI learning path",
        "time_available_minutes": 60,
    }
    values.update(overrides)
    return build_learner_profile(**values)


def test_build_learner_profile_normalizes_structured_fields():
    profile = _profile(
        current_level=" Beginner ",
        current_skills=" Python,  APIs\nRAG ",
        interests=" documents, reliable answers ",
        target_role="  ",
        goal="  I feel lost  ",
    )

    assert profile == {
        "entry_point": ENTRY_POINTS[0],
        "current_level": "beginner",
        "current_skills": ["Python", "APIs", "RAG"],
        "interests": ["documents", "reliable answers"],
        "preferred_work_style": PREFERRED_WORK_STYLES[0],
        "target_role": None,
        "goal": "I feel lost",
        "time_available_minutes": 60,
    }


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("entry_point", "other", "entry_point"),
        ("current_level", "expert", "current_level"),
        ("preferred_work_style", "other", "preferred_work_style"),
        ("current_skills", " ", "current_skills"),
        ("interests", " ", "interests"),
        ("goal", " ", "goal"),
        ("time_available_minutes", 0, "time_available_minutes"),
    ],
)
def test_build_learner_profile_validates_required_fields(field, value, match):
    with pytest.raises(ValueError, match=match):
        _profile(**{field: value})


def test_guided_intake_query_includes_profile_context():
    profile = _profile()

    query = build_guided_intake_query(profile)

    assert "AI engineering learning path" in query
    assert "Current skills: Python, APIs, basic prompting" in query
    assert "Target role or direction: AI Application Engineer" in query
    assert "skill gaps" in query


def test_recommend_direction_uses_profile_signals():
    profile = _profile(
        preferred_work_style="Evaluate and improve AI quality",
        interests="testing, hallucination checks, evaluation rubrics",
        goal="I want to learn how to evaluate RAG answers",
    )

    assert recommend_direction(profile) == "AI Evaluation / Quality"


def test_estimate_skill_gap_omits_current_skills():
    profile = _profile(
        current_skills="Python APIs, input validation, logging",
        target_role="AI Backend Engineer",
    )

    skill_gap = estimate_skill_gap(profile, "AI Backend / Integration")

    assert "Python APIs" not in skill_gap
    assert "input validation" not in skill_gap
    assert "safe error handling" in skill_gap


def test_guided_intake_recommendation_attaches_retrieved_evidence():
    profile = _profile()
    docs = [
        Document(
            page_content=(
                "RAG systems combine retrieval, citations, and evaluation for "
                "practical AI application work."
            ),
            metadata={
                "source": "ai_engineering_learning_paths.md",
                "chunk_index": 3,
                "source_type": "markdown",
                "document_role": "derived_summary",
                "source_authority": "derived_official",
                "title": "AI Engineering Learning Paths",
            },
        )
    ]

    recommendation = build_guided_intake_recommendation(profile, docs)

    assert recommendation["learner_profile"] == profile
    assert recommendation["recommended_direction"] == "RAG / LLM Applications"
    assert "AI Application Engineer" in recommendation["possible_ai_career_paths"]
    assert "chunking" in recommendation["skill_gap"]
    assert recommendation["next_action"] == recommendation["learning_path_outline"][0]
    assert "recommended direction is based on the learner profile" in recommendation[
        "evidence_note"
    ]
    assert "evidence was used to support and frame the learning path" in recommendation[
        "evidence_note"
    ]
    assert "not hiring guarantees" in recommendation["evidence_note"]
    assert recommendation["evidence_used"][0]["title"] == "AI Engineering Learning Paths"


def test_guided_intake_recommendation_is_honest_without_evidence():
    recommendation = build_guided_intake_recommendation(_profile(), [])

    assert recommendation["evidence_used"] == []
    assert "not evidence-backed" in recommendation["evidence_note"]
