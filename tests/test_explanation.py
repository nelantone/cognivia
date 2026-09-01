"""Tests for explanation evaluation tool."""

import pytest

from tools.explanation import evaluate_explanation


def test_evaluate_explanation_returns_expected_keys():
    result = evaluate_explanation(
        user_explanation="RAG retrieves documents and uses them as context for the LLM.",
        target_concept="RAG",
        key_terms=["retrieval", "context", "LLM"],
    )

    assert "clarity_score" in result
    assert "missing_terms" in result
    assert "feedback" in result
    assert "next_step" in result
    assert "strengths" in result
    assert "improved_wording" in result


def test_evaluate_explanation_score_is_between_0_and_100():
    result = evaluate_explanation(
        user_explanation="RAG retrieves relevant context before generating an answer.",
        target_concept="RAG",
        key_terms=["retrieval", "context", "generation"],
    )

    assert 0 <= result["clarity_score"] <= 100


def test_evaluate_explanation_detects_missing_terms():
    result = evaluate_explanation(
        user_explanation="RAG helps the model answer better.",
        target_concept="RAG",
        key_terms=["retrieval", "context", "embeddings"],
    )

    assert "retrieval" in result["missing_terms"]
    assert "context" in result["missing_terms"]
    assert "embeddings" in result["missing_terms"]


def test_evaluate_explanation_rewards_key_terms():
    strong = evaluate_explanation(
        user_explanation="RAG uses retrieval to find relevant context and gives it to the LLM before generation.",
        target_concept="RAG",
        key_terms=["retrieval", "context", "LLM", "generation"],
    )

    weak = evaluate_explanation(
        user_explanation="RAG helps answer better.",
        target_concept="RAG",
        key_terms=["retrieval", "context", "LLM", "generation"],
    )

    assert strong["clarity_score"] > weak["clarity_score"]


def test_very_short_explanation_with_key_term_scores_low():
    result = evaluate_explanation(
        user_explanation="fsdf",
        target_concept="dfdf",
        key_terms=["sdf"],
    )

    assert result["clarity_score"] < 50
    assert "low quality" in result["feedback"].lower()


def test_short_explanation_is_capped_at_low_score():
    result = evaluate_explanation(
        user_explanation="RAG uses retrieval",
        target_concept="RAG",
        key_terms=["retrieval"],
    )

    assert result["clarity_score"] <= 30


def test_strong_explanation_still_scores_higher_than_weak_one():
    strong = evaluate_explanation(
        user_explanation=(
            "RAG retrieves relevant documents and uses them as context for the LLM before generation, "
            "which improves factual accuracy."
        ),
        target_concept="RAG",
        key_terms=["retrieval", "context", "LLM", "generation"],
    )

    weak = evaluate_explanation(
        user_explanation="RAG uses retrieval",
        target_concept="RAG",
        key_terms=["retrieval", "context", "LLM", "generation"],
    )

    assert strong["clarity_score"] > weak["clarity_score"]


def test_empty_explanation_raises_value_error():
    with pytest.raises(ValueError, match="cannot be empty"):
        evaluate_explanation(
            user_explanation="",
            target_concept="RAG",
            key_terms=["retrieval", "context"],
        )


def test_strengths_list_is_populated_for_good_explanation():
    result = evaluate_explanation(
        user_explanation="RAG uses retrieval to find relevant context and gives it to the LLM before generation.",
        target_concept="RAG",
        key_terms=["retrieval", "context", "LLM", "generation"],
    )

    assert isinstance(result["strengths"], list)
    assert len(result["strengths"]) > 0


def test_strengths_list_is_empty_for_weak_explanation():
    result = evaluate_explanation(
        user_explanation="RAG helps answer better.",
        target_concept="RAG",
        key_terms=["retrieval", "context", "LLM", "generation"],
    )

    assert isinstance(result["strengths"], list)
    assert len(result["strengths"]) == 0


def test_improved_wording_contains_original_text():
    original = "RAG helps answer better."
    result = evaluate_explanation(
        user_explanation=original,
        target_concept="RAG",
        key_terms=["retrieval", "context", "LLM", "generation"],
    )

    assert original in result["improved_wording"]


def test_improved_wording_suggests_missing_terms():
    result = evaluate_explanation(
        user_explanation="RAG helps answer better.",
        target_concept="RAG",
        key_terms=["retrieval", "context", "LLM", "generation"],
    )

    # Should suggest missing terms in improved_wording
    assert "retrieval" in result["improved_wording"]


def test_feedback_mentions_missing_terms_count():
    result = evaluate_explanation(
        user_explanation="RAG helps answer better.",
        target_concept="RAG",
        key_terms=["retrieval", "context", "embeddings"],
    )

    assert "3" in result["feedback"] or "important" in result["feedback"].lower()


def test_next_step_is_actionable_for_good_explanation():
    result = evaluate_explanation(
        user_explanation="RAG uses retrieval to find relevant context and gives it to the LLM before generation.",
        target_concept="RAG",
        key_terms=["retrieval", "context", "LLM", "generation"],
    )

    assert (
        "example" in result["next_step"].lower()
        or "concrete" in result["next_step"].lower()
    )


def test_next_step_is_actionable_for_partial_explanation():
    result = evaluate_explanation(
        user_explanation="RAG retrieves relevant context before generating an answer.",
        target_concept="RAG",
        key_terms=["retrieval", "context", "generation"],
    )

    assert len(result["next_step"]) > 10


def test_feedback_explains_why_missing_terms_matter():
    result = evaluate_explanation(
        user_explanation="RAG helps answer better.",
        target_concept="RAG",
        key_terms=["retrieval", "context", "embeddings"],
    )

    # Feedback should explain why the terms matter
    assert any(
        word in result["feedback"].lower()
        for word in ["precision", "technical", "vocabulary", "signals", "understand"]
    )
