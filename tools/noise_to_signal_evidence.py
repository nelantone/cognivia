"""Deterministic evidence interpretation for the Noise-to-Signal workflow."""

import re
from pathlib import Path
from typing import Any

from tools.study_plan import (
    _clean_text,
    build_informational_answer as _legacy_build_informational_answer,
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
IDENTITY_FIELDS = ("source", "filename", "chunk_index", "page", "id", "_id", "point_id")


def _informational_question_shape(goal: str) -> tuple[str, str] | None:
    clean_goal = _clean_text(goal).strip(" ?.!:")
    patterns = (
        ("how", r"^how\s+(?:does|do|is|are)\s+(?P<topic>.+?)\s+work$"),
        (
            "benefit",
            r"^why\s+(?:is|are)\s+(?P<topic>.+?)\s+useful(?:\s+(?:for|to)\s+.+)?$",
        ),
        (
            "benefit",
            r"^why\s+(?:is|are)\s+(?P<topic>.+?)\s+important(?:\s+(?:for|to)\s+.+)?$",
        ),
        ("benefit", r"^what\s+are\s+the\s+benefits\s+of\s+(?P<topic>.+)$"),
        ("benefit", r"^what\s+is\s+the\s+purpose\s+of\s+(?P<topic>.+)$"),
        (
            "definition",
            r"^(?:can|could|would)\s+you\s+explain\s+(?P<topic>.+)$",
        ),
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


def _is_sentence_like_claim(sentence: str) -> bool:
    clean_sentence = _clean_text(sentence).strip(" -#*:;")
    words = clean_sentence.split()
    if len(words) < 7 or clean_sentence.endswith(":"):
        return False
    if not re.search(
        r"\b(?:is|are|can|does|do|works?|uses?|helps?|enables?|supports?|"
        r"provides?|checks?|measures?|combines?|routes?)\b",
        clean_sentence,
        re.IGNORECASE,
    ):
        return False
    return bool(re.search(r"[.!?]$", clean_sentence))


def _clean_candidate_sentence(sentence: str) -> str:
    clean_sentence = _clean_text(sentence).strip(" -#*")
    clean_sentence = re.sub(r"\s+,", ",", clean_sentence)
    clean_sentence = re.sub(r"\s+([.!?])", r"\1", clean_sentence)
    if clean_sentence.endswith("..."):
        return ""
    if re.search(
        r"(?:,|:|;|\b(?:and|or))\s*[.!?]?$",
        clean_sentence,
        re.IGNORECASE,
    ):
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


def build_informational_answer(
    goal: str,
    reasoning_items,
    max_claims: int = 3,
) -> str:
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


def _reasoning_items_with_full_text(state: dict[str, Any]) -> list[dict[str, Any]]:
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


def _single_focus_has_domain_or_direct_support(state: dict[str, Any]) -> bool:
    focus = _clean_text(state.get("selected_focus") or state.get("goal", ""))
    return _is_ai_engineering_domain_focus(focus) or _evidence_directly_mentions_focus(
        focus,
        _reasoning_items_with_full_text(state),
    )
