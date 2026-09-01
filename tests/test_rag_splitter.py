"""Tests for RAG document splitter."""

import pytest

import rag.splitter as splitter
from rag.splitter import _token_count, split_documents


def _reset_tokenizer_caches():
    splitter._get_tokenizer.cache_clear()
    splitter._token_count.cache_clear()


class WhitespaceEncoding:
    def encode(self, text):
        return text.split()


def _use_whitespace_tokenizer(monkeypatch):
    def fake_get_encoding(name):
        return WhitespaceEncoding()

    monkeypatch.setattr(splitter.tiktoken, "get_encoding", fake_get_encoding)
    _reset_tokenizer_caches()


def _normalized_words(text):
    return text.split()


def _chunk_words(chunks):
    return _normalized_words(" ".join(chunk["content"] for chunk in chunks))


def _assert_words_covered_in_order(source_text, chunks):
    source_words = _normalized_words(source_text)
    emitted_words = _chunk_words(chunks)
    search_start = 0

    for source_word in source_words:
        try:
            found_index = emitted_words.index(source_word, search_start)
        except ValueError:
            pytest.fail(f"Missing source word from chunks: {source_word}")

        search_start = found_index + 1


def test_token_count_prefers_cl100k_base_when_available(monkeypatch):
    class FakeEncoding:
        def encode(self, text):
            return text.split()

    calls = []

    def fake_get_encoding(name):
        calls.append(name)
        return FakeEncoding()

    monkeypatch.setattr(splitter.tiktoken, "get_encoding", fake_get_encoding)
    _reset_tokenizer_caches()

    try:
        assert _token_count("alpha beta") == 2
        assert calls == ["cl100k_base"]
    finally:
        _reset_tokenizer_caches()


def test_token_count_uses_deterministic_byte_fallback_when_cl100k_unavailable(
    monkeypatch,
):
    calls = []

    def fake_get_encoding(name):
        calls.append(name)
        raise OSError("offline")

    monkeypatch.setattr(splitter.tiktoken, "get_encoding", fake_get_encoding)
    _reset_tokenizer_caches()

    try:
        assert splitter._get_tokenizer() is splitter._BYTE_ENCODING
        assert _token_count("éé") == 4
        assert calls == ["cl100k_base"]
    finally:
        _reset_tokenizer_caches()


def test_split_documents_returns_chunks():
    documents = [
        {
            "source": "test.md",
            "content": "This is a short document about RAG.",
        }
    ]

    chunks = split_documents(documents, chunk_size=100, chunk_overlap=20)

    assert len(chunks) == 1
    assert chunks[0]["source"] == "test.md"
    assert "RAG" in chunks[0]["content"]


def test_split_documents_splits_long_document():
    documents = [
        {
            "source": "long.md",
            "content": "A" * 250,
        }
    ]

    chunks = split_documents(documents, chunk_size=100, chunk_overlap=20)

    assert len(chunks) > 1
    assert all("source" in chunk for chunk in chunks)
    assert all("content" in chunk for chunk in chunks)


def test_split_documents_detects_markdown_headers_and_preserves_metadata():
    documents = [
        {
            "source": "guide.md",
            "filename": "guide.md",
            "source_type": "markdown",
            "content": (
                "# AI Learning\n"
                "Overview evidence.\n\n"
                "## RAG Evaluation\n"
                "RAG evaluation checks retrieval quality.\n\n"
                "## LangGraph\n"
                "LangGraph structures workflows."
            ),
        }
    ]

    chunks = split_documents(documents, chunk_size=100, chunk_overlap=0)

    assert [chunk["heading"] for chunk in chunks] == [
        "AI Learning",
        "RAG Evaluation",
        "LangGraph",
    ]
    assert chunks[0]["heading_path"] == "AI Learning"
    assert chunks[1]["heading_path"] == "AI Learning > RAG Evaluation"
    assert chunks[1]["section_level"] == 2
    assert chunks[1]["filename"] == "guide.md"


def test_split_documents_keeps_markdown_sections_from_blending():
    documents = [
        {
            "source": "guide.md",
            "source_type": "markdown",
            "content": (
                "# RAG Evaluation\n"
                "retrieval quality answer grounding source traceability\n\n"
                "# Cooking\n"
                "tacos pastor marinade pineapple salsa"
            ),
        }
    ]

    chunks = split_documents(documents, chunk_size=100, chunk_overlap=20)

    rag_chunks = [
        chunk for chunk in chunks if chunk.get("heading_path") == "RAG Evaluation"
    ]
    cooking_chunks = [
        chunk for chunk in chunks if chunk.get("heading_path") == "Cooking"
    ]

    assert rag_chunks
    assert cooking_chunks
    assert all("tacos" not in chunk["content"] for chunk in rag_chunks)
    assert all("retrieval quality" not in chunk["content"] for chunk in cooking_chunks)


def test_split_documents_keeps_markdown_oversized_sections_token_limited(monkeypatch):
    _use_whitespace_tokenizer(monkeypatch)
    documents = [
        {
            "source": "guide.md",
            "source_type": "markdown",
            "content": "# RAG Evaluation\nalpha beta gamma delta epsilon zeta eta",
        }
    ]

    try:
        chunks = split_documents(documents, chunk_size=4, chunk_overlap=1)

        assert len(chunks) > 1
        assert all(_token_count(chunk["content"]) <= 4 for chunk in chunks)
        assert all(chunk["heading"] == "RAG Evaluation" for chunk in chunks)
    finally:
        _reset_tokenizer_caches()


def test_split_documents_keeps_non_markdown_behavior_without_heading_metadata():
    documents = [
        {
            "source": "notes.txt",
            "source_type": "text",
            "content": "# Not a Markdown heading\nplain text content",
        }
    ]

    chunks = split_documents(documents, chunk_size=100, chunk_overlap=0)

    assert len(chunks) == 1
    assert chunks[0]["content"] == "# Not a Markdown heading\nplain text content"
    assert "heading" not in chunks[0]


def test_split_documents_ignores_empty_content():
    documents = [
        {
            "source": "empty.md",
            "content": "",
        }
    ]

    chunks = split_documents(documents)

    assert chunks == []


def test_split_documents_adds_chunk_index():
    documents = [
        {
            "source": "test.md",
            "content": "A" * 250,
        }
    ]

    chunks = split_documents(documents, chunk_size=100, chunk_overlap=20)

    assert chunks[0]["chunk_index"] == 0
    assert chunks[1]["chunk_index"] == 1


@pytest.mark.parametrize(
    ("content", "chunk_size", "chunk_overlap"),
    [
        ("hello beautiful world", 10, 0),
        ("alpha beautiful world", 10, 2),
        (
            "Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda",
            24,
            8,
        ),
        ("Alpha  beta\n\ngamma delta\n epsilon", 12, 3),
    ],
)
def test_split_documents_preserves_source_words_in_order(
    content,
    chunk_size,
    chunk_overlap,
):
    documents = [
        {
            "source": "test.md",
            "content": content,
        }
    ]

    chunks = split_documents(
        documents,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    assert chunks
    assert all(chunk["content"] for chunk in chunks)
    _assert_words_covered_in_order(content, chunks)


def test_split_documents_has_no_gaps_when_overlap_is_zero(monkeypatch):
    _use_whitespace_tokenizer(monkeypatch)
    documents = [
        {
            "source": "test.md",
            "content": "hello beautiful world again",
        }
    ]

    try:
        chunks = split_documents(documents, chunk_size=2, chunk_overlap=0)

        assert [chunk["content"] for chunk in chunks] == [
            "hello beautiful",
            "world again",
        ]
        assert _chunk_words(chunks) == ["hello", "beautiful", "world", "again"]
        assert [chunk["chunk_index"] for chunk in chunks] == [0, 1]
    finally:
        _reset_tokenizer_caches()


def test_split_documents_allows_overlap_without_mid_word_duplicate_when_possible(
    monkeypatch,
):
    _use_whitespace_tokenizer(monkeypatch)
    content = "alpha beta gamma delta epsilon zeta eta theta"
    documents = [
        {
            "source": "test.md",
            "content": content,
        }
    ]

    try:
        chunks = split_documents(documents, chunk_size=4, chunk_overlap=2)

        assert [chunk["content"] for chunk in chunks] == [
            "alpha beta gamma delta",
            "gamma delta epsilon zeta",
            "epsilon zeta eta theta",
        ]
        assert all(_token_count(chunk["content"]) <= 4 for chunk in chunks)
        assert [chunk["chunk_index"] for chunk in chunks] == [0, 1, 2]
        _assert_words_covered_in_order(content, chunks)
    finally:
        _reset_tokenizer_caches()


def test_split_documents_limits_chunks_by_fallback_tokens_not_characters(monkeypatch):
    def fake_get_encoding(name):
        raise OSError("offline")

    monkeypatch.setattr(splitter.tiktoken, "get_encoding", fake_get_encoding)
    _reset_tokenizer_caches()
    content = "éé"
    documents = [
        {
            "source": "test.md",
            "content": content,
        }
    ]

    try:
        chunks = split_documents(documents, chunk_size=3, chunk_overlap=0)

        assert len(content) < 3
        assert _token_count(content) > 3
        assert [chunk["content"] for chunk in chunks] == ["é", "é"]
    finally:
        _reset_tokenizer_caches()


def test_split_documents_preserves_long_word_content_with_progress():
    content = "supercalifragilisticexpialidocious"
    documents = [
        {
            "source": "test.md",
            "content": content,
        }
    ]

    chunks = split_documents(documents, chunk_size=10, chunk_overlap=0)

    assert chunks
    assert all(chunk["content"] for chunk in chunks)
    assert "".join(chunk["content"] for chunk in chunks) == content
    assert [chunk["chunk_index"] for chunk in chunks] == list(range(len(chunks)))


def test_split_documents_avoids_mid_word_boundaries_when_possible(monkeypatch):
    _use_whitespace_tokenizer(monkeypatch)
    content = (
        "Alpha beta gamma delta epsilon zeta eta theta iota kappa lambda "
        "mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega"
    )
    documents = [
        {
            "source": "test.md",
            "content": content,
        }
    ]

    try:
        chunks = split_documents(documents, chunk_size=5, chunk_overlap=2)
        source_words = set(content.split())

        assert len(chunks) > 1
        assert all(_token_count(chunk["content"]) <= 5 for chunk in chunks)
        assert all(chunk["content"].split()[0] in source_words for chunk in chunks)
        assert all(chunk["content"].split()[-1] in source_words for chunk in chunks)
        assert [chunk["chunk_index"] for chunk in chunks] == list(range(len(chunks)))
        _assert_words_covered_in_order(content, chunks)
    finally:
        _reset_tokenizer_caches()


def test_split_documents_preserves_pdf_metadata():
    documents = [
        {
            "source": "future_jobs.pdf",
            "filename": "future_jobs.pdf",
            "type": "pdf",
            "page": 43,
            "document_role": "primary_source",
            "source_authority": "official",
            "publisher": "World Economic Forum",
            "published_year": "2025",
            "content": "Future job-market skills include analytical thinking.",
        }
    ]

    chunks = split_documents(documents, chunk_size=100, chunk_overlap=20)

    assert chunks[0]["source_type"] == "pdf"
    assert chunks[0]["filename"] == "future_jobs.pdf"
    assert chunks[0]["page"] == 43
    assert chunks[0]["document_role"] == "primary_source"
    assert chunks[0]["source_authority"] == "official"
    assert chunks[0]["publisher"] == "World Economic Forum"
    assert chunks[0]["published_year"] == "2025"


def test_split_documents_preserves_derived_summary_original_source_title():
    documents = [
        {
            "source": "oecd_ai_skills_gap_2025.md",
            "filename": "oecd_ai_skills_gap_2025.md",
            "source_type": "markdown",
            "document_role": "derived_summary",
            "source_authority": "derived_official",
            "publisher": "OECD",
            "published_year": "2026",
            "original_source_title": "AI and skills: What we know so far",
            "content": "AI skills evidence should remain traceable to official sources.",
        }
    ]

    chunks = split_documents(documents, chunk_size=100, chunk_overlap=20)

    assert chunks[0]["document_role"] == "derived_summary"
    assert chunks[0]["source_authority"] == "derived_official"
    assert chunks[0]["publisher"] == "OECD"
    assert chunks[0]["published_year"] == "2026"
    assert chunks[0]["original_source_title"] == "AI and skills: What we know so far"
