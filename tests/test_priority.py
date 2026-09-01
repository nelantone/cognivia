"""Tests for priority scoring tool."""

import pytest

from tools.priority import calculate_market_relevance, calculate_priority_score


class TestCalculateMarketRelevance:
    """Tests for the market relevance calculation from RAG context."""

    def test_returns_expected_keys(self):
        """Result includes score, reason, market_relevance_score, and market_signals."""
        result = calculate_market_relevance(
            topic="RAG",
            retrieved_context=["RAG is in high demand and hiring"],
        )

        assert "score" in result
        assert "reason" in result
        assert "market_relevance_score" in result
        assert "market_signals" in result

    def test_empty_context_returns_low_score(self):
        """Empty context returns low relevance (score 1) since topic not mentioned."""
        result = calculate_market_relevance(
            topic="RAG",
            retrieved_context=[],
        )

        assert result["score"] == 1
        assert result["market_relevance_score"] == 1
        assert result["market_signals"] == []

    def test_empty_list_context_returns_low_score(self):
        """Empty list context returns low relevance."""
        result = calculate_market_relevance(
            topic="RAG",
            retrieved_context=[],
        )

        assert result["score"] == 1
        assert (
            "not found" in result["reason"].lower()
            or "not mentioned" in result["reason"].lower()
        )

    def test_no_context_returns_low_score(self):
        """No context provided returns low relevance since topic not mentioned."""
        result = calculate_market_relevance(
            topic="RAG",
            retrieved_context=None,
        )

        assert result["score"] == 1

    def test_topic_not_in_context_returns_low_score(self):
        """Topic not appearing in context gives low relevance (score 1)."""
        result = calculate_market_relevance(
            topic="Bachata Sensual",
            retrieved_context=["This skill is in high demand for jobs"],
        )

        assert result["score"] == 1
        assert (
            "not found" in result["reason"].lower()
            or "not mentioned" in result["reason"].lower()
        )
        # Should show placeholder message, not generic signals
        assert result["market_signals"] == [
            "No direct market signals found for this topic in the knowledge base."
        ]

    def test_generic_market_words_without_topic_match_do_not_inflate_score(self):
        """Generic market words without topic match keep score low."""
        result = calculate_market_relevance(
            topic="Bachata Sensual",
            retrieved_context=[
                "This skill is in high demand and hiring",
                "salary for dancers is competitive",
                "essential skill for performers",
            ],
        )

        # Topic not mentioned = score should be 1, not inflated by signals
        assert result["score"] == 1
        # Should show placeholder message, not generic signals
        assert result["market_signals"] == [
            "No direct market signals found for this topic in the knowledge base."
        ]

    def test_topic_mentioned_once_gives_modest_score(self):
        """Topic mentioned once gives modest relevance (score 3)."""
        result = calculate_market_relevance(
            topic="RAG",
            retrieved_context=["RAG is mentioned in passing"],
        )

        assert result["score"] == 3

    def test_topic_mentioned_multiple_times_with_signals_returns_high_score(self):
        """Topic mentioned multiple times with career signals gives high relevance."""
        result = calculate_market_relevance(
            topic="RAG",
            retrieved_context=[
                "RAG is in high demand for jobs",
                "hiring managers require RAG skills",
                "salary for RAG engineers is competitive",
            ],
        )

        assert result["score"] == 5
        assert len(result["market_signals"]) >= 2

    def test_topic_mentioned_multiple_times_without_signals_returns_score_3(self):
        """Topic mentioned multiple times but few signals gives moderate score."""
        result = calculate_market_relevance(
            topic="RAG",
            retrieved_context=[
                "RAG is used in this context",
                "RAG is also mentioned here",
            ],
        )

        assert result["score"] == 3

    def test_relevant_ai_topic_gets_higher_market_relevance(self):
        """Relevant AI topic like RAG with career context gets higher relevance."""
        result = calculate_market_relevance(
            topic="RAG",
            retrieved_context=[
                "RAG (Retrieval Augmented Generation) is in high demand",
                "hiring managers require RAG skills for AI positions",
                "salary for RAG engineers is competitive",
            ],
        )

        assert result["score"] >= 4
        assert "RAG" in result["reason"]

    def test_unrelated_topic_like_bachata_gets_low_market_relevance(self):
        """Unrelated topic like Bachata Sensual gets low market relevance."""
        # Topic "Bachata Sensual" does not appear in context about Python careers
        result = calculate_market_relevance(
            topic="Bachata Sensual",
            retrieved_context=[
                "Python is in high demand",
                "hiring for Python developers",
                "salary for Python engineers is high",
            ],
        )

        # Topic not mentioned = score should be 1, not inflated by career signals
        assert result["score"] == 1
        # Should show placeholder message, not generic signals
        assert result["market_signals"] == [
            "No direct market signals found for this topic in the knowledge base."
        ]

    def test_market_signals_list_contains_detected_keywords(self):
        """Market signals list contains detected signal keywords."""
        result = calculate_market_relevance(
            topic="RAG",
            retrieved_context=["RAG is in high demand and hiring"],
        )

        assert isinstance(result["market_signals"], list)
        assert (
            "demand" in result["market_signals"] or "hiring" in result["market_signals"]
        )


class TestCalculatePriorityScore:
    """Tests for the priority score calculation."""

    def test_returns_expected_keys(self):
        """Result includes score, reason, market_relevance_score, and market_signals."""
        result = calculate_priority_score(
            topic="RAG",
            interest=4,
            difficulty=3,
            urgency=5,
            retrieved_context=["RAG is in high demand"],
        )

        assert "score" in result
        assert "reason" in result
        assert "market_relevance_score" in result
        assert "market_signals" in result

    def test_score_is_between_0_and_100(self):
        """Score is always between 0 and 100."""
        result = calculate_priority_score(
            topic="LangChain",
            interest=3,
            difficulty=3,
            urgency=3,
            retrieved_context=["LangChain is important"],
        )

        assert 0 <= result["score"] <= 100

    def test_high_priority_inputs_return_higher_score_than_low_priority_inputs(self):
        """Higher inputs produce higher priority scores."""
        high = calculate_priority_score(
            topic="RAG",
            interest=5,
            difficulty=2,
            urgency=5,
            retrieved_context=["RAG is in high demand required hiring"],
        )

        low = calculate_priority_score(
            topic="Random topic",
            interest=1,
            difficulty=5,
            urgency=1,
            retrieved_context=["some random context"],
        )

        assert high["score"] > low["score"]

    def test_invalid_rating_raises_value_error(self):
        """Rating outside 1-5 range raises ValueError."""
        with pytest.raises(ValueError) as error:
            calculate_priority_score(
                topic="RAG",
                interest=6,
                difficulty=3,
                urgency=3,
                retrieved_context=[],
            )
        assert "between 1 and 5" in str(error.value)

    def test_market_relevance_score_derived_from_context(self):
        """Market relevance score comes from retrieved context."""
        result = calculate_priority_score(
            topic="RAG",
            interest=3,
            difficulty=3,
            urgency=3,
            retrieved_context=[
                "RAG is in high demand required hiring salary competitive"
            ],
        )

        # With many signals, score should be 4 or 5
        assert result["market_relevance_score"] >= 4

    def test_market_signals_from_context(self):
        """Market signals list comes from context analysis."""
        result = calculate_priority_score(
            topic="RAG",
            interest=3,
            difficulty=3,
            urgency=3,
            retrieved_context=["RAG is in high demand and hiring"],
        )

        assert isinstance(result["market_signals"], list)

    def test_reason_mentions_market_relevance(self):
        """Reason explains that market relevance was calculated from knowledge base."""
        result = calculate_priority_score(
            topic="RAG",
            interest=3,
            difficulty=3,
            urgency=3,
            retrieved_context=["RAG skills are in demand"],
        )

        assert (
            "market relevance" in result["reason"].lower()
            or "knowledge base" in result["reason"].lower()
        )
