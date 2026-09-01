"""Study plan generation tool."""

import re
from pathlib import Path

VALID_ENERGY_LEVELS = {"low", "medium", "high"}
VALID_CURRENT_LEVELS = {"beginner", "intermediate", "advanced"}
INTERNAL_METADATA_KEYS = {"_id", "_collection_name"}
PROJECT_DOCUMENTATION_ROLE = "project_documentation"
AUTHORITY_PRIORITY = {
    ("primary_source", "official", "pdf"): 0,
    ("derived_summary", "derived_official", "markdown"): 1,
    ("internal_note", "internal", "markdown"): 2,
}
ACRONYMS = {"ai", "api", "rag", "wef", "pdf", "mcp", "llm", "nlp"}
LOWERCASE_TITLE_WORDS = {"and", "for", "in", "of", "the", "to"}
OPTION_STOP_WORDS = {
    "a",
    "an",
    "and",
    "ai",
    "basic",
    "for",
    "or",
    "the",
    "to",
}
ANSWER_STOP_WORDS = OPTION_STOP_WORDS | {
    "about",
    "according",
    "does",
    "future",
    "identify",
    "important",
    "report",
    "say",
    "skills",
    "what",
    "which",
}
VALID_LOWERCASE_STARTS = {
    "a",
    "an",
    "and",
    "as",
    "because",
    "for",
    "in",
    "it",
    "of",
    "on",
    "or",
    "the",
    "this",
    "to",
    "with",
}
DECISION_FOCUS_PATTERN = re.compile(
    r"\bshould\s+i\s+(?:prioritize|focus\s+on|learn)\s+(?P<focus>.+?)(?:\?|$)",
    re.IGNORECASE,
)
SINGLE_FOCUS_PATTERNS = (
    re.compile(r"\bi\s+want\s+to\s+learn\s+(?P<focus>.+?)(?:\.|!|$)", re.IGNORECASE),
    re.compile(r"\bi\s+am\s+learning\s+(?P<focus>.+?)(?:\.|!|$)", re.IGNORECASE),
    re.compile(r"\bi\s+need\s+to\s+learn\s+(?P<focus>.+?)(?:\.|!|$)", re.IGNORECASE),
    re.compile(r"\bhelp\s+me\s+learn\s+(?P<focus>.+?)(?:\.|!|$)", re.IGNORECASE),
    re.compile(r"^learn\s+(?P<focus>.+?)(?:\.|!|$)", re.IGNORECASE),
)
VAGUE_GOAL_PATTERNS = (
    re.compile(r"\bwhat\s+should\s+i\s+learn\s+next\b", re.IGNORECASE),
    re.compile(r"\bwhat\s+should\s+i\s+(?:study|focus\s+on)\b", re.IGNORECASE),
)
GUIDED_INTAKE_LOST_ENTRY_POINT = "I feel lost and need direction"
GUIDED_INTAKE_NEXT_STEP_ENTRY_POINT = "I want to choose what to learn next"
GUIDED_INTAKE_LOST_PATTERNS = (
    re.compile(r"\bi\s+feel\s+lost\b", re.IGNORECASE),
    re.compile(r"\bi(?:'|\s+a)?m\s+lost\b", re.IGNORECASE),
    re.compile(r"\bnot\s+sure\s+where\s+to\s+start\b", re.IGNORECASE),
    re.compile(r"\bdon'?t\s+know\s+where\s+to\s+start\b", re.IGNORECASE),
    re.compile(r"\b(?:practical\s+)?ai\s+learning\s+path\b", re.IGNORECASE),
)
LEARNING_GUIDANCE_PATTERNS = (
    re.compile(
        r"\b(?:what|which)\s+skills\s+should\s+i\s+(?:learn|study|focus\s+on)\b",
        re.IGNORECASE,
    ),
)
INFORMATIONAL_GOAL_PATTERNS = (
    re.compile(r"^(?:what|which)\s+skills\b", re.IGNORECASE),
    re.compile(
        r"\bwhat\s+does\s+(?:the\s+)?(?:report|wef)\s+(?:say|identify)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\bsummarize\s+the\s+evidence\s+about\b", re.IGNORECASE),
    re.compile(r"\baccording\s+to\s+the\s+report,\s+what\b", re.IGNORECASE),
)


def _clean_text(value):
    """Collapse whitespace so evidence previews are safe to display."""
    return " ".join(str(value or "").split())


def _truncate_at_word_boundary(text, max_chars):
    clean_text = _clean_text(text).lstrip(".,;:)- ")

    if len(clean_text) <= max_chars:
        return clean_text

    truncated = clean_text[:max_chars].rsplit(" ", 1)[0].strip()

    if not truncated:
        truncated = clean_text[:max_chars].strip()

    return f"{truncated}..."


def _starts_with_mid_word_fragment(text):
    clean_text = _clean_text(text).lstrip(".,;:)- ")

    if not clean_text or not clean_text[0].islower():
        return False

    first_word = re.split(r"\W+", clean_text, maxsplit=1)[0].lower()
    return first_word not in VALID_LOWERCASE_STARTS


def _is_useful_evidence_text(text, source_type):
    clean_text = _clean_text(text)

    if len(clean_text.split()) < 4:
        return False

    if source_type == "pdf" and _starts_with_mid_word_fragment(clean_text):
        return False

    return True


def _clean_evidence_display_text(text, source_type):
    raw_text = str(text or "")

    if source_type == "markdown":
        lines = raw_text.splitlines()
        content_start = 0

        for index, line in enumerate(lines):
            if line.startswith("## "):
                content_start = index
                break

        if content_start:
            raw_text = "\n".join(lines[content_start:])

        raw_text = re.sub(r"^#+\s*", "", raw_text, flags=re.MULTILINE)
        return _clean_text(raw_text)

    clean_text = _clean_text(raw_text)

    if source_type != "pdf":
        return clean_text

    clean_text = re.sub(
        r"\bFuture of Jobs Report 2025\b",
        "",
        clean_text,
        flags=re.IGNORECASE,
    )
    clean_text = re.sub(r"\b\d{1,3}\b$", "", clean_text).strip()

    if _starts_with_mid_word_fragment(clean_text):
        sentence_match = re.search(r"[.!?]\s+([A-Z][^.!?]{30,})", clean_text)

        if sentence_match:
            clean_text = sentence_match.group(1)

    return _clean_text(clean_text)


def _title_from_filename(filename):
    stem = Path(filename or "Unknown source").stem
    words = stem.replace("-", " ").replace("_", " ").split()
    titled_words = []

    for index, word in enumerate(words):
        lower_word = word.lower()

        if lower_word in ACRONYMS:
            titled_words.append(word.upper())
        elif index > 0 and lower_word in LOWERCASE_TITLE_WORDS:
            titled_words.append(lower_word)
        else:
            titled_words.append(word.capitalize())

    return " ".join(titled_words) or "Unknown source"


def _source_type_from_metadata(metadata):
    source_type = metadata.get("source_type") or metadata.get("type")

    if source_type:
        return str(source_type).lower()

    source = str(metadata.get("source", ""))
    suffix = Path(source).suffix.lower()

    if suffix == ".pdf":
        return "pdf"

    if suffix == ".md":
        return "markdown"

    return "unknown"


def _safe_metadata(metadata):
    return {
        key: value
        for key, value in (metadata or {}).items()
        if key not in INTERNAL_METADATA_KEYS
    }


def _source_type_label(source_type):
    if source_type == "pdf":
        return "PDF"

    if source_type == "markdown":
        return "Markdown"

    return source_type.capitalize() if source_type else "Unknown"


def _evidence_type_label(source_type, document_role, source_authority):
    if document_role == "primary_source" and source_type == "pdf":
        return "Primary PDF"

    if document_role == "derived_summary" and source_authority == "derived_official":
        return "Derived official summary"

    if document_role == "internal_note":
        return "Internal note"

    return _source_type_label(source_type)


def _authority_priority(evidence_item):
    key = (
        evidence_item.get("document_role"),
        evidence_item.get("source_authority"),
        evidence_item.get("source_type"),
    )
    return AUTHORITY_PRIORITY.get(key, 3)


def format_evidence_label(evidence_item):
    """Return a readable evidence label without exposing raw paths."""
    title = evidence_item.get("title") or "Unknown source"

    if evidence_item.get("source_type") == "pdf" and evidence_item.get("page") is not None:
        return f"{title} - page {evidence_item['page']}"

    return title


def _build_evidence_item(doc, max_excerpt_chars=320, max_claim_chars=140):
    raw_content = getattr(doc, "page_content", "")

    if not _clean_text(raw_content):
        return None

    metadata = _safe_metadata(getattr(doc, "metadata", {}) or {})
    document_role = metadata.get("document_role")

    if document_role == PROJECT_DOCUMENTATION_ROLE:
        return None

    source = metadata.get("source", "Unknown source")
    filename = metadata.get("filename") or Path(str(source)).name
    source_type = _source_type_from_metadata(metadata)

    display_content = _clean_evidence_display_text(raw_content, source_type)

    if not _is_useful_evidence_text(display_content, source_type):
        return None

    first_sentence = display_content.split(". ", 1)[0]
    source_authority = metadata.get("source_authority")

    title = metadata.get("title") or _title_from_filename(filename)

    return {
        "title": title,
        "source": filename or "Unknown source",
        "source_type": source_type,
        "document_role": document_role,
        "source_authority": source_authority,
        "type_label": _evidence_type_label(
            source_type,
            document_role,
            source_authority,
        ),
        "page": metadata.get("page"),
        "chunk_index": metadata.get("chunk_index", "N/A"),
        "excerpt": _truncate_at_word_boundary(display_content, max_excerpt_chars),
        "claim": _truncate_at_word_boundary(first_sentence, max_claim_chars),
        "metadata": metadata,
    }


def select_diverse_evidence(retrieved_docs, max_items=3):
    """Select readable evidence with source diversity and optional PDF inclusion."""
    if max_items <= 0:
        return []

    candidates = []

    for doc in retrieved_docs or []:
        item = _build_evidence_item(doc)

        if item:
            candidates.append(item)

    selected = []
    seen_sources = set()
    ranked_candidates = sorted(
        enumerate(candidates),
        key=lambda indexed_item: (
            _authority_priority(indexed_item[1]),
            indexed_item[0],
        ),
    )
    pdf_candidate = next(
        (
            item
            for _, item in ranked_candidates
            if item["source_type"] == "pdf"
            and item.get("document_role") == "primary_source"
        ),
        None,
    )

    if pdf_candidate:
        selected.append(pdf_candidate)
        seen_sources.add(pdf_candidate["source"])

    for _, item in ranked_candidates:
        source_key = item["source"]

        if source_key in seen_sources:
            continue

        selected.append(item)
        seen_sources.add(source_key)

        if len(selected) == max_items:
            break

    return selected[:max_items]


def build_evidence_claims(evidence_items):
    """Build concise evidence claims for reasoning, not raw UI excerpts."""
    claims = []

    for item in evidence_items:
        claim = item.get("claim")

        if claim:
            claims.append(f"{format_evidence_label(item)}: {claim}")

    return claims


def _claim_terms(text):
    terms = {
        term
        for term in re.findall(r"[a-z0-9]+", text.lower())
        if term not in ANSWER_STOP_WORDS
    }
    if "wef" in terms:
        terms.update({"2025", "jobs"})
    return terms


def _is_substantially_duplicate_claim(claim, selected_claims):
    claim_terms = _claim_terms(claim)

    if not claim_terms:
        return False

    for selected_claim in selected_claims:
        selected_terms = _claim_terms(selected_claim)

        if not selected_terms:
            continue

        overlap = len(claim_terms & selected_terms)
        similarity = overlap / len(claim_terms | selected_terms)

        if similarity >= 0.65:
            return True

    return False


def _is_low_quality_informational_claim(claim):
    clean_claim = _clean_text(claim).lower()

    if len(clean_claim.split()) < 5:
        return True

    return clean_claim.startswith(
        (
            "note ",
            "notes ",
            "source ",
            "sources ",
            "table ",
            "figure ",
            "appendix ",
        )
    )


def _clean_informational_claim(claim):
    clean_claim = _clean_text(claim)
    clean_claim = re.sub(
        r"\bFuture of Jobs Report 2025\b",
        "",
        clean_claim,
        flags=re.IGNORECASE,
    )
    clean_claim = re.sub(r"\s+[-–]\s+page\s+\d+\b", "", clean_claim, flags=re.IGNORECASE)
    return _clean_text(clean_claim).strip(" .")


def _claim_supports_explanation_goal(goal, claim):
    clean_goal = _clean_text(goal).strip(" ?.!")
    topic_match = re.search(
        r"^(?:can|could|would)\s+you\s+explain\s+(?P<topic>.+)$",
        clean_goal,
        flags=re.IGNORECASE,
    ) or re.search(
        r"^what\s+is\s+(?P<topic>.+)$",
        clean_goal,
        flags=re.IGNORECASE,
    ) or re.search(
        r"^(?:describe|explain)\s+(?P<topic>.+)$",
        clean_goal,
        flags=re.IGNORECASE,
    )

    if not topic_match:
        return True

    topic = _clean_text(topic_match.group("topic")).strip(" ?.!")
    if not topic:
        return True

    topic_pattern = r"\b" + r"\s+".join(re.escape(part) for part in topic.split()) + r"\b"
    claim_sentences = re.split(r"(?<=[.!?])\s+", _clean_text(claim))
    topic_sentence = next(
        (
            sentence
            for sentence in claim_sentences
            if re.search(topic_pattern, sentence, flags=re.IGNORECASE)
        ),
        "",
    )
    if not topic_sentence:
        return False

    superficial_patterns = (
        r"\bwhen\s+comparing\b",
        r"\b(?:ranking|ranked|ranks|prioriti[sz]e|priority|career-priority)\b",
        rf"\b(?:comparing|choosing)\b[^.!?]*{topic_pattern}",
    )
    if any(
        re.search(pattern, topic_sentence, flags=re.IGNORECASE)
        for pattern in superficial_patterns
    ):
        return False

    comma_list_pattern = (
        rf"(?:\b[\w -]+\b,\s*)+{topic_pattern}\s*,?\s*"
        r"(?:and|or)?\s*\b[\w -]+\b"
    )
    if re.search(comma_list_pattern, topic_sentence, flags=re.IGNORECASE):
        return False

    explanatory_relation = (
        r"is|means|refers\s+to|enables|allows|supports|uses|provides|helps|"
        r"works\s+by|can\s+build|can\s+use|checks"
    )
    direct_explanation_patterns = (
        rf"{topic_pattern}\b.{{0,90}}\b(?:{explanatory_relation})\b",
        rf"\b(?:with|using)\s+{topic_pattern}\b.{{0,90}}\b"
        rf"(?:{explanatory_relation}|build|use|create|develop)\b",
    )
    return any(
        re.search(pattern, topic_sentence, flags=re.IGNORECASE)
        for pattern in direct_explanation_patterns
    )


def _informational_claim_score(goal, item, original_index):
    goal_terms = _claim_terms(goal)
    text = " ".join(
        [
            str(item.get("title", "")),
            str(item.get("claim", "")),
            str(item.get("excerpt", "")),
        ]
    )
    text_terms = _claim_terms(text)
    relevance = len(goal_terms & text_terms)

    return (
        -relevance,
        _authority_priority(item),
        original_index,
    )


def build_informational_answer(goal, reasoning_items, max_claims=3):
    """Build a concise answer from a small subset of usable reasoning evidence."""
    if max_claims <= 0:
        return ""

    ranked_items = sorted(
        enumerate(reasoning_items or []),
        key=lambda indexed_item: _informational_claim_score(
            goal,
            indexed_item[1],
            indexed_item[0],
        ),
    )
    selected_claims = []
    selected_items = []

    for original_index, item in ranked_items:
        relevance = -_informational_claim_score(goal, item, original_index)[0]
        if relevance <= 0:
            break

        claim = _clean_informational_claim(item.get("claim", ""))

        if not claim or _is_low_quality_informational_claim(claim):
            continue

        if not _claim_supports_explanation_goal(goal, claim):
            continue

        if _is_substantially_duplicate_claim(claim, selected_claims):
            continue

        selected_claims.append(claim)
        selected_items.append(item)

        if len(selected_claims) == max_claims:
            break

    if not selected_claims:
        return ""

    answer = " ".join(f"{claim}." for claim in selected_claims)
    page_numbers = sorted(
        {
            item["page"]
            for item in selected_items
            if item.get("source_type") == "pdf" and item.get("page") is not None
        }
    )
    pdf_titles = {
        item.get("title")
        for item in selected_items
        if item.get("source_type") == "pdf" and item.get("title")
    }

    if page_numbers and pdf_titles:
        pages = ", ".join(str(page) for page in page_numbers)
        title = sorted(pdf_titles)[0]
        answer = f"{answer} Retrieved evidence comes from {title}, pages {pages}."

    return answer


def _summarize_reasoning_evidence(retrieved_docs):
    evidence_items = []

    for doc in retrieved_docs or []:
        item = _build_evidence_item(doc)

        if item:
            evidence_items.append(item)

    if not evidence_items:
        return {
            "has_evidence": False,
            "items": [],
        }

    return {
        "has_evidence": True,
        "items": evidence_items,
    }


def _derive_single_focus(goal):
    clean_goal = _clean_text(goal)

    if guided_intake_entry_point_for_goal(clean_goal):
        return None

    for focus_pattern in SINGLE_FOCUS_PATTERNS:
        focus_match = focus_pattern.search(clean_goal)

        if focus_match:
            focus = focus_match.group("focus").strip(" ?.!")
            return _truncate_at_word_boundary(focus, 90)

    if "?" in clean_goal or not clean_goal:
        return None

    return _truncate_at_word_boundary(clean_goal, 90)


def _is_informational_question(goal):
    clean_goal = _clean_text(goal)
    if any(pattern.search(clean_goal) for pattern in LEARNING_GUIDANCE_PATTERNS):
        return False

    return any(pattern.search(clean_goal) for pattern in INFORMATIONAL_GOAL_PATTERNS)


def guided_intake_entry_point_for_goal(goal):
    """Return the guided intake entry point for vague learning-path requests."""
    clean_goal = _clean_text(goal)
    if not clean_goal:
        return None

    if any(pattern.search(clean_goal) for pattern in GUIDED_INTAKE_LOST_PATTERNS):
        return GUIDED_INTAKE_LOST_ENTRY_POINT

    if any(pattern.search(clean_goal) for pattern in VAGUE_GOAL_PATTERNS) or any(
        pattern.search(clean_goal) for pattern in LEARNING_GUIDANCE_PATTERNS
    ):
        return GUIDED_INTAKE_NEXT_STEP_ENTRY_POINT

    return None


def _extract_decision_options(goal):
    clean_goal = _clean_text(goal)
    focus_match = DECISION_FOCUS_PATTERN.search(clean_goal)

    if not focus_match:
        return []

    focus = focus_match.group("focus").strip(" ?.!")
    normalized_focus = re.sub(r"\s*,?\s+or\s+", ", ", focus, flags=re.IGNORECASE)
    options = [
        option.strip(" .?!")
        for option in normalized_focus.split(",")
        if option.strip(" .?!")
    ]

    return options if len(options) > 1 else []


def _option_terms(option):
    return [
        term
        for term in re.findall(r"[a-z0-9]+", option.lower())
        if term not in OPTION_STOP_WORDS
    ]


def _score_option_against_evidence(option, evidence):
    option_lower = option.lower()
    terms = _option_terms(option)
    score = 0

    for item in evidence.get("items", []):
        text = " ".join(
            [
                str(item.get("title", "")),
                str(item.get("excerpt", "")),
                str(item.get("claim", "")),
            ]
        ).lower()

        if option_lower in text:
            score += 4

        for term in terms:
            if re.search(rf"\b{re.escape(term)}\b", text):
                score += 1

    return score


def _rank_decision_options(options, evidence):
    ranked_options = []

    for index, option in enumerate(options):
        ranked_options.append(
            {
                "option": option,
                "score": _score_option_against_evidence(option, evidence),
                "original_index": index,
            }
        )

    return sorted(
        ranked_options,
        key=lambda item: (-item["score"], item["original_index"]),
    )


def _select_decision_focus(goal, evidence):
    options = _extract_decision_options(goal)

    if not options:
        if _is_informational_question(goal):
            if evidence["has_evidence"]:
                return {
                    "selected_focus": None,
                    "options": [],
                    "ranked_options": [],
                    "confidence": "evidence_backed",
                    "decision_status": "informational",
                    "tied_options": [],
                }

            return {
                "selected_focus": None,
                "options": [],
                "ranked_options": [],
                "confidence": "low_evidence",
                "decision_status": "insufficient_evidence",
                "tied_options": [],
            }

        single_focus = _derive_single_focus(goal)

        if not single_focus:
            return {
                "selected_focus": None,
                "options": [],
                "ranked_options": [],
                "confidence": "needs_clarification",
                "decision_status": "needs_clarification",
                "tied_options": [],
            }

        return {
            "selected_focus": single_focus,
            "options": [],
            "ranked_options": [],
            "confidence": "not_applicable",
            "decision_status": "single_focus",
            "tied_options": [],
        }

    ranked_options = _rank_decision_options(options, evidence)
    best_option = ranked_options[0]
    best_score = best_option["score"]

    if best_score <= 0:
        return {
            "selected_focus": None,
            "options": options,
            "ranked_options": ranked_options,
            "confidence": "low_evidence",
            "decision_status": "insufficient_evidence",
            "tied_options": [],
        }

    tied_options = [
        item["option"]
        for item in ranked_options
        if item["score"] == best_score
    ]

    if len(tied_options) > 1:
        return {
            "selected_focus": None,
            "options": options,
            "ranked_options": ranked_options,
            "confidence": "tied",
            "decision_status": "tie",
            "tied_options": tied_options,
        }

    return {
        "selected_focus": best_option["option"],
        "options": options,
        "ranked_options": ranked_options,
        "confidence": "evidence_backed",
        "decision_status": "selected",
        "tied_options": [],
    }


def summarize_retrieved_evidence(retrieved_docs, max_items=3):
    """Create concise reasoning and display evidence from retrieved RAG documents."""
    evidence_items = select_diverse_evidence(retrieved_docs, max_items=max_items)

    if not evidence_items:
        return {
            "has_evidence": False,
            "summary": "No retrieved knowledge-base evidence was available.",
            "items": [],
            "claims": [],
        }

    claims = build_evidence_claims(evidence_items)

    return {
        "has_evidence": True,
        "summary": " ".join(claims),
        "items": evidence_items,
        "claims": claims,
    }


def build_noise_to_signal_decision(goal, retrieved_docs):
    """Build deterministic Noise-to-Signal outputs from the user goal and evidence."""
    clean_goal = _clean_text(goal)
    guided_intake_entry_point = guided_intake_entry_point_for_goal(clean_goal)
    reasoning_evidence = _summarize_reasoning_evidence(retrieved_docs)
    evidence = summarize_retrieved_evidence(retrieved_docs)
    focus_decision = _select_decision_focus(clean_goal, reasoning_evidence)
    selected_focus = focus_decision["selected_focus"]
    decision_status = focus_decision["decision_status"]
    interaction_mode = (
        "guided_intake"
        if guided_intake_entry_point
        else "clarification" if decision_status == "needs_clarification" else "direct_decision"
    )

    if decision_status == "informational":
        evidence_answer = build_informational_answer(
            clean_goal,
            reasoning_evidence["items"],
        )
        if evidence_answer:
            reasoning = (
                "The user asked an informational question, so the response answers "
                "from retrieved evidence instead of selecting a study focus."
            )
            recommendation = f"Based on the retrieved evidence: {evidence_answer}"
            next_action = (
                "Choose one identified skill to compare against your current goals, or "
                "ask for a study plan for that specific skill."
            )
        else:
            decision_status = "insufficient_evidence"
            reasoning = (
                "The user asked an informational question, but the retrieved "
                "evidence did not contain a usable answer claim."
            )
            recommendation = (
                "The knowledge base does not contain enough usable evidence to answer "
                "this question without inventing details."
            )
            next_action = (
                "Try a more specific source, report section, role, or skill area, "
                "then retrieve evidence again."
            )
    elif decision_status == "selected":
        if focus_decision["ranked_options"]:
            other_options = [
                item["option"]
                for item in focus_decision["ranked_options"][1:]
            ]
            comparison = (
                f" It ranks above {', '.join(other_options)} because the retrieved "
                "evidence contains stronger matching signals for this option."
                if other_options and focus_decision["confidence"] == "evidence_backed"
                else " Retrieved evidence is not strong enough to separate the options clearly."
            )
            reasoning = (
                f"Retrieved evidence gives {selected_focus} the strongest deterministic "
                f"score among the listed options.{comparison}"
            )
        else:
            reasoning = (
                "Retrieved evidence points to market-relevant AI skills and practical "
                "implementation work, so the safest focus is the option that creates a "
                "small demonstrable artifact."
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
    elif decision_status == "single_focus":
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
    elif decision_status == "tie":
        tied_options = ", ".join(focus_decision["tied_options"])
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
    elif decision_status == "insufficient_evidence":
        if _is_informational_question(clean_goal):
            reasoning = (
                "The user asked an informational question, but no usable "
                "knowledge-base evidence was retrieved."
            )
            recommendation = (
                "The knowledge base does not contain enough usable evidence to answer "
                "this question without inventing details."
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
    else:
        reasoning = (
            "The goal is too broad to turn into a concrete study topic without more "
            "context."
        )
        if guided_intake_entry_point:
            recommendation = (
                "I need a little learner profile context before choosing a "
                "learning path."
            )
            next_action = (
                "Add your current level, current skills, interests, preferred work "
                "style, target role if known, and available learning time."
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
        "goal": clean_goal,
        "selected_focus": selected_focus,
        "options": focus_decision["options"],
        "option_scores": focus_decision["ranked_options"],
        "decision_status": decision_status,
        "needs_clarification": decision_status == "needs_clarification",
        "interaction_mode": interaction_mode,
        "guided_intake_entry_point": guided_intake_entry_point,
        "tied_options": focus_decision["tied_options"],
        "recommendation": recommendation,
        "evidence": evidence,
        "decision_trace": [
            f"User goal: {clean_goal}",
            f"Decision status: {decision_status}",
            f"Interpreted focus: {selected_focus or 'none'}",
            f"Short evidence-based reasoning: {reasoning}",
            f"Selected focus: {selected_focus or 'none'}",
            f"Next action: {next_action}",
        ],
        "next_action": next_action,
    }


def _validate_study_plan_inputs(available_time, energy_level, current_level):
    """Validate study plan inputs."""
    if available_time <= 0:
        raise ValueError("available_time must be greater than 0.")

    if energy_level not in VALID_ENERGY_LEVELS:
        raise ValueError("energy_level must be one of: low, medium, high.")

    if current_level not in VALID_CURRENT_LEVELS:
        raise ValueError(
            "current_level must be one of: beginner, intermediate, advanced."
        )


def generate_study_plan(
    topic,
    available_time,
    energy_level,
    current_level,
    evidence_summary=None,
):
    """
    Generate a structured study plan for a learning topic.

    This tool creates a deterministic plan based on time, energy, level, and
    optional retrieved evidence.
    Returns a plan with a clear goal, 3-4 concrete steps with time blocks,
    and an expected outcome.
    """
    _validate_study_plan_inputs(available_time, energy_level, current_level)

    goal_focus = {
        "beginner": "build a solid foundation",
        "intermediate": "strengthen practical fluency",
        "advanced": "refine expert-level judgment",
    }[current_level]
    goal = f"{goal_focus.capitalize()} in {topic}"

    level_focus = {
        "beginner": "fundamentals and simple examples",
        "intermediate": "common workflows and reliable patterns",
        "advanced": "edge cases, trade-offs, and evaluation",
    }[current_level]

    energy_focus = {
        "low": "light and low-friction",
        "medium": "steady and balanced",
        "high": "deep and hands-on",
    }[energy_level]

    if available_time <= 30:
        steps = [
            {
                "step": f"Skim a short primer on {topic} (1 page or 5–7 min video)",
                "time_minutes": 8,
            },
            {
                "step": "Write 3 bullet notes: definition, use case, and one key term",
                "time_minutes": 8,
            },
            {
                "step": f"Create a 2–3 sentence summary of {topic} in your own words",
                "time_minutes": 8,
            },
        ]
        deliverable = f"a short summary + 3 bullet notes about {topic}"
        expected_outcome = (
            f"Leave with a basic mental model of {topic} without feeling overloaded."
        )
    elif available_time <= 60:
        steps = [
            {
                "step": f"Read a focused overview of {topic} and identify 2 core concepts",
                "time_minutes": 15,
            },
            {
                "step": "Work through a tiny example (toy dataset, pseudo-code, or snippet)",
                "time_minutes": 20,
            },
            {
                "step": "Answer 2 short questions: when to use it and common pitfalls",
                "time_minutes": 15,
            },
            {
                "step": "Write a one-paragraph recap + next step",
                "time_minutes": 10,
            },
        ]
        deliverable = f"a one-paragraph recap and a tiny example of {topic}"
        expected_outcome = f"Build a practical, working understanding of {topic}."
    elif available_time <= 120:
        steps = [
            {
                "step": f"Review the key ideas of {topic} and outline the main workflow",
                "time_minutes": 20,
            },
            {
                "step": "Implement a small working example or notebook",
                "time_minutes": 35,
            },
            {
                "step": "Stress-test with a variation or edge case",
                "time_minutes": 25,
            },
            {
                "step": "Reflect: trade-offs, assumptions, and one improvement",
                "time_minutes": 15,
            },
        ]
        deliverable = f"a working mini-example plus one tested variation of {topic}"
        expected_outcome = f"Gain confidence applying {topic} beyond the happy path."
    else:
        steps = [
            {
                "step": f"Map the theory behind {topic} and list 3 design choices",
                "time_minutes": 30,
            },
            {
                "step": "Build a small end-to-end demo (data → output)",
                "time_minutes": 45,
            },
            {
                "step": "Evaluate results with a metric or checklist",
                "time_minutes": 25,
            },
            {
                "step": "Document trade-offs, edge cases, and when not to use it",
                "time_minutes": 20,
            },
        ]
        deliverable = (
            f"a documented demo of {topic} with evaluation notes and trade-offs"
        )
        expected_outcome = (
            f"Develop deeper fluency and decision-making confidence with {topic}."
        )

    if energy_level == "low":
        for step in steps:
            step["step"] = step["step"].replace("Implement", "Sketch")
            step["step"] = step["step"].replace("Build", "Outline")
        expected_outcome = expected_outcome.replace("confidence", "comfort")

    if current_level == "beginner":
        steps[0]["step"] = (
            f"Review fundamentals: define {topic} and list 2 simple examples"
        )
    elif current_level == "advanced":
        steps[-1]["step"] = (
            "Document trade-offs, edge cases, and evaluation criteria for success"
        )

    clean_evidence_summary = _clean_text(evidence_summary)
    if clean_evidence_summary:
        steps[-1]["step"] = (
            f"{steps[-1]['step']}; compare your next decision against the retrieved "
            "evidence claims"
        )
        deliverable = f"{deliverable} plus one evidence-backed next decision"
        expected_outcome = (
            f"{expected_outcome} Use the retrieved evidence to avoid a generic plan."
        )

    # Format steps as readable text for backward compatibility
    plan_text = f"**Goal:** {goal}\n\n" + "\n".join(
        f"{i}. {s['step']} ({s['time_minutes']} min)" for i, s in enumerate(steps, 1)
    )
    plan_text += f"\n\n**Deliverable:** {deliverable}"

    return {
        "plan": plan_text,
        "goal": goal,
        "steps": steps,
        "expected_outcome": (
            f"{expected_outcome} Focus on {level_focus} with a {energy_focus} pace."
        ),
    }
