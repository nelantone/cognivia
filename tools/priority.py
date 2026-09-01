"""Priority scoring tool."""


def _validate_rating(value, name):
    """Validate that a rating is between 1 and 5."""
    if not 1 <= value <= 5:
        raise ValueError(f"{name} must be between 1 and 5.")


def calculate_market_relevance(topic, retrieved_context):
    """
    Calculate market relevance score from RAG context.

    Market relevance depends PRIMARILY on whether the topic itself appears
    in the retrieved context. Generic market words alone do not create
    high relevance unless the topic is also present.

    Scoring logic:
    - If topic does NOT appear in context: score 1 (low relevance)
    - If topic appears once: modest relevance (2-3/5)
    - If topic appears multiple times AND has career/job/skill signals: higher relevance (4-5/5)

    Args:
        topic: The learning topic string.
        retrieved_context: List of context chunks from RAG retrieval.

    Returns:
        dict with keys:
            - score (int): 1-5 market relevance rating
            - reason (str): Explanation of the score
            - market_relevance_score (int): Same as score
            - market_signals (list): Detected signal keywords
    """
    if not retrieved_context:
        return {
            "score": 1,
            "reason": f"No market context found for '{topic}'. Topic not mentioned.",
            "market_relevance_score": 1,
            "market_signals": [],
        }

    # Combine all context into lowercase for matching
    combined_context = " ".join(retrieved_context).lower()
    topic_lower = topic.lower()

    # Count how many times topic appears in context
    topic_count = combined_context.count(topic_lower)
    topic_mentioned = topic_count > 0

    # Define career/job/skill signal patterns
    career_signals = [
        "hiring",
        "demand",
        "required",
        "needed",
        "sought",
        "job",
        "career",
        "skill",
        "salary",
        "compensation",
        "essential",
        "critical",
        "valuable",
        "important",
    ]

    # Count career signal matches
    signals_found = []
    for signal in career_signals:
        if signal in combined_context:
            signals_found.append(signal)
    signal_count = len(signals_found)

    # Calculate score based on topic presence first
    if not topic_mentioned:
        # Topic not mentioned = low relevance regardless of signals
        score = 1
        score_reason = (
            f"Topic '{topic}' not found in retrieved context. "
            f"Generic market signals present but topic not relevant."
        )
        # Don't show generic signals when topic doesn't match
        signals_found = [
            "No direct market signals found for this topic in the knowledge base."
        ]
    elif topic_count >= 2 and signal_count >= 2:
        # Topic appears multiple times with career signals = high relevance
        score = 5
        score_reason = (
            f"Strong market relevance for '{topic}' with {topic_count} mentions "
            f"and {signal_count} career signals found."
        )
    elif signal_count >= 3:
        # Many career signals (even with single topic mention) = moderate-high
        score = 4
        score_reason = (
            f"Moderate market relevance for '{topic}' with {topic_count} mention(s) "
            f"and {signal_count} career signal(s)."
        )
    elif topic_mentioned:
        # Topic appears = modest relevance (minimum 3)
        score = 3
        score_reason = (
            f"Topic '{topic}' mentioned {topic_count} time(s) in context "
            f"with {signal_count} career signal(s)."
        )
    else:
        # Fallback (should not reach here)
        score = 2
        score_reason = f"Limited market context for '{topic}'."

    return {
        "score": score,
        "reason": score_reason,
        "market_relevance_score": score,
        "market_signals": signals_found,
    }


def calculate_priority_score(
    topic,
    interest,
    difficulty,
    urgency,
    retrieved_context=None,
):
    """
    Calculate a priority score for a learning topic.

    Higher interest, urgency, and career relevance increase the score.
    Higher difficulty slightly lowers the score, because very hard topics may need more planning.
    Market relevance is calculated from retrieved_context if provided.

    Args:
        topic: The learning topic string.
        interest: Interest level 1-5.
        difficulty: Difficulty level 1-5.
        urgency: Urgency level 1-5.
        retrieved_context: Optional list of context strings from RAG retrieval.
            If provided, market relevance is computed from context instead of manual input.

    Returns:
        dict with keys: score, reason, market_relevance_score, market_signals
    """
    ratings = {
        "interest": interest,
        "difficulty": difficulty,
        "urgency": urgency,
    }

    for name, value in ratings.items():
        _validate_rating(value, name)

    # Calculate market relevance from RAG context
    market_data = calculate_market_relevance(topic, retrieved_context or [])
    career_relevance = market_data["score"]

    weighted_score = (
        interest * 0.25
        + urgency * 0.30
        + career_relevance * 0.35
        + (6 - difficulty) * 0.10
    )

    score = round((weighted_score / 5) * 100)

    reason = (
        f"{topic} has a priority score of {score}/100 based on interest, "
        f"urgency, market relevance (calculated from knowledge base), and difficulty."
    )

    return {
        "score": score,
        "reason": reason,
        "market_relevance_score": market_data["market_relevance_score"],
        "market_signals": market_data["market_signals"],
    }
