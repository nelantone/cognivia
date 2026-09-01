"""Tests for RAG document loader."""

from rag.loader import load_markdown_documents


def test_load_documents_loads_md_files(tmp_path):
    file_path = tmp_path / "example.md"
    file_path.write_text("# Example\n\nThis is a test document.", encoding="utf-8")

    documents = load_markdown_documents(tmp_path)

    assert len(documents) == 1
    assert documents[0]["source"] == str(file_path)
    assert "test document" in documents[0]["content"]
    assert documents[0]["document_role"] == "internal_note"
    assert documents[0]["source_authority"] == "internal"
    assert documents[0]["source_type"] == "markdown"


def test_load_markdown_documents_recurses_and_sets_derived_metadata(tmp_path):
    derived_dir = tmp_path / "derived"
    derived_dir.mkdir()
    file_path = derived_dir / "oecd_ai_and_skills.md"
    file_path.write_text(
        "# OECD AI and Skills\n\n"
        "publisher: OECD\n"
        "publication_year: 2025\n"
        "original_source_title: AI and Skills\n"
        "document_role: derived_summary\n"
        "source_authority: derived_official\n\n"
        "## Source and Purpose\n\n"
        "Derived official summary.",
        encoding="utf-8",
    )

    documents = load_markdown_documents(tmp_path)

    assert len(documents) == 1
    assert documents[0]["source"] == str(file_path)
    assert documents[0]["document_role"] == "derived_summary"
    assert documents[0]["source_authority"] == "derived_official"
    assert documents[0]["publisher"] == "OECD"
    assert documents[0]["published_year"] == "2025"
    assert documents[0]["original_source_title"] == "AI and Skills"


def test_load_markdown_documents_marks_project_documentation(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    file_path = docs_dir / "public_sources_notes.md"
    file_path.write_text(
        "# Public Sources Notes\n\nThis describes project source policy.",
        encoding="utf-8",
    )

    documents = load_markdown_documents(tmp_path)

    assert len(documents) == 1
    assert documents[0]["source"] == str(file_path)
    assert documents[0]["document_role"] == "project_documentation"
    assert documents[0]["source_authority"] == "internal"


def test_load_markdown_documents_ignores_empty_files(tmp_path):
    empty_file = tmp_path / "empty.md"
    empty_file.write_text("", encoding="utf-8")

    documents = load_markdown_documents(tmp_path)

    assert documents == []


def test_load_markdown_documents_raises_for_missing_directory(tmp_path):
    missing_path = tmp_path / "missing"

    try:
        load_markdown_documents(missing_path)
    except FileNotFoundError as error:
        assert "Knowledge base directory not found" in str(error)
    else:
        raise AssertionError("Expected FileNotFoundError")
