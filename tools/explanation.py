"""Explanation evaluation tool."""


def evaluate_explanation(user_explanation, target_concept, key_terms):
    """
    Evaluate a user's explanation of a technical concept.

    This is a deterministic helper tool. It checks whether the explanation
    includes important terms and gives simple feedback.
    """
    if not user_explanation or not user_explanation.strip():
        raise ValueError("user_explanation cannot be empty.")

    explanation_lower = user_explanation.lower()
    missing_terms = [
        term for term in key_terms if term.lower() not in explanation_lower
    ]
    covered_terms = [term for term in key_terms if term.lower() in explanation_lower]

    covered_count = len(covered_terms)
    total_count = len(key_terms)

    if not key_terms:
        term_score = 50
    else:
        term_score = round((covered_count / total_count) * 100)

    length_words = len(user_explanation.split())

    if length_words < 4:
        return {
            "clarity_score": 10,
            "missing_terms": missing_terms,
            "feedback": (
                f"The explanation of {target_concept} is low quality and too short to evaluate. "
                "Please write at least one complete sentence."
            ),
            "next_step": (
                "Write a fuller explanation that defines the concept and mentions "
                "how it works."
            ),
            "strengths": [],
            "improved_wording": "".join(
                [
                    user_explanation.strip(),
                    (
                        f" Consider including: {', '.join(missing_terms)}."
                        if missing_terms
                        else ""
                    ),
                ]
            ),
        }

    length_score = min(100, length_words * 5)
    clarity_score = round((term_score * 0.7) + (length_score * 0.3))
    clarity_score = min(100, clarity_score)
    if length_words < 8:
        clarity_score = min(clarity_score, 30)

    # Build strengths list
    strengths = []
    if covered_count > 0:
        strengths.append(f"Correctly uses key term(s): {', '.join(covered_terms)}")
    if length_words >= 12:
        strengths.append("Provides a detailed enough explanation")
    if clarity_score >= 80:
        strengths.append("Demonstrates good understanding of the concept")

    # Build improved wording suggestion
    improved_parts = [user_explanation.strip()]
    if missing_terms and total_count > 0:
        missing_clause = f" Consider including: {', '.join(missing_terms)}."
        improved_parts.append(missing_clause)
    improved_wording = "".join(improved_parts)

    # Feedback with what is good and what is missing
    if clarity_score >= 80:
        feedback = (
            f"Good explanation of {target_concept}. It covers the main technical ideas "
            f"and uses {covered_count} of {total_count} key terms effectively."
        )
        next_step = (
            "Try adding a concrete example or use case to deepen understanding. "
            "For example: 'RAG is used in chatbots to pull up-to-date documents before answering.'"
        )
    elif clarity_score >= 50:
        feedback = (
            f"Partial explanation of {target_concept}. It is understandable, "
            f"but {len(missing_terms)} important technical term(s) are missing: {', '.join(missing_terms)}. "
            f"Using these terms shows precision and helps listeners recognise you understand the concept."
        )
        next_step = (
            f"Rewrite the explanation and naturally weave in: {', '.join(missing_terms)}. "
            "For instance: 'RAG uses retrieval to fetch relevant context before generation.'"
        )
    else:
        feedback = (
            f"The explanation of {target_concept} is too general. "
            f"It is missing {len(missing_terms)} key term(s): {', '.join(missing_terms)}. "
            "Technical vocabulary signals depth and helps differentiate your answer in interviews."
        )
        next_step = (
            f"Start over and structure the explanation around: {', '.join(missing_terms)}. "
            "A simple template: 'X is a technique that uses Y to achieve Z.'"
        )

    return {
        "clarity_score": clarity_score,
        "missing_terms": missing_terms,
        "feedback": feedback,
        "next_step": next_step,
        "strengths": strengths,
        "improved_wording": improved_wording,
    }
