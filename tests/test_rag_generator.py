"""Tests for RAG answer generation helpers."""

from langchain_core.documents import Document
import pytest

import rag.generator as generator
from rag.generator import build_rag_prompt, format_retrieved_context


def test_format_retrieved_context_includes_source_metadata():
    documents = [
        Document(
            page_content="RAG retrieves context before generation.",
            metadata={"source": "rag_notes.md", "chunk_index": 0},
        )
    ]

    context = format_retrieved_context(documents)

    assert "rag_notes.md" in context
    assert "chunk 0" in context
    assert "RAG retrieves context" in context


def test_format_retrieved_context_handles_empty_documents():
    context = format_retrieved_context([])

    assert context == "No relevant context was retrieved."


def test_build_rag_prompt_includes_question_and_context():
    prompt = build_rag_prompt(
        question="What should I study next?",
        retrieved_context="Python and RAG are relevant skills.",
    )

    assert "What should I study next?" in prompt
    assert "Python and RAG are relevant skills." in prompt


def test_answer_with_rag_returns_safe_message_when_retrieval_is_empty(monkeypatch):
    def retrieve_mock(*args, **kwargs):
        return []

    monkeypatch.setattr(generator, "retrieve_relevant_chunks", retrieve_mock)
    monkeypatch.setattr(
        generator,
        "get_provider_config",
        lambda: pytest.fail("provider config should not be used without evidence"),
    )

    result = generator.answer_with_rag("What is the capital of France?")

    assert result["sources"] == []
    assert result["retrieved_context"] == "No relevant context was retrieved."
    assert "could not find relevant local evidence" in result["answer"]
