"""Tests for basic RAG preparation pipeline."""

from rag.pipeline import prepare_knowledge_base


def test_prepare_knowledge_base_returns_chunks(tmp_path):
    file_path = tmp_path / "example.md"
    file_path.write_text("# Example\n\nThis is a RAG document.", encoding="utf-8")

    chunks = prepare_knowledge_base(tmp_path)

    assert len(chunks) == 1
    assert chunks[0]["source"] == str(file_path)
    assert "RAG document" in chunks[0]["content"]
