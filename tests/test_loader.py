
import rag.loader as loader
from rag.loader import load_documents, load_pdf_documents


class FakePdfPage:
    def __init__(self, text):
        self.text = text

    def extract_text(self):
        return self.text


class FakePdfReader:
    def __init__(self, _file_path):
        self.pages = [FakePdfPage("PDF page text about AI careers.")]


def test_load_markdown_documents(tmp_path):
    kb_dir = tmp_path / "knowledge_base"
    kb_dir.mkdir()

    markdown_file = kb_dir / "test.md"
    markdown_file.write_text("# Test\n\nThis is a test document.", encoding="utf-8")

    docs = load_documents(kb_dir)

    assert len(docs) == 1
    assert docs[0]["type"] == "markdown"
    assert docs[0]["source_type"] == "markdown"
    assert docs[0]["document_role"] == "internal_note"
    assert docs[0]["filename"] == "test.md"
    assert "test document" in docs[0]["content"]


def test_load_pdf_documents_returns_empty_list_when_directory_does_not_exist(tmp_path):
    missing_dir = tmp_path / "missing_pdfs"

    docs = load_pdf_documents(missing_dir)

    assert docs == []


def test_load_pdf_documents_recurses_into_nested_directories(monkeypatch, tmp_path):
    nested_pdf_dir = tmp_path / "career_sources" / "pdfs"
    nested_pdf_dir.mkdir(parents=True)
    pdf_file = nested_pdf_dir / "ai_skills_report.pdf"
    pdf_file.write_bytes(b"fake pdf bytes")

    monkeypatch.setattr(loader, "PdfReader", FakePdfReader)

    docs = load_pdf_documents(tmp_path)

    assert len(docs) == 1
    assert docs[0]["source"] == str(pdf_file)
    assert docs[0]["filename"] == "ai_skills_report.pdf"
    assert docs[0]["type"] == "pdf"
    assert docs[0]["source_type"] == "pdf"
    assert docs[0]["page"] == 1
    assert docs[0]["document_role"] == "primary_source"
    assert docs[0]["source_authority"] == "official"
    assert "AI careers" in docs[0]["content"]


def test_load_documents_combines_available_sources(tmp_path):
    kb_dir = tmp_path / "knowledge_base"
    pdf_dir = tmp_path / "pdfs"
    kb_dir.mkdir()
    pdf_dir.mkdir()

    markdown_file = kb_dir / "test.md"
    markdown_file.write_text("# Test\n\nMarkdown content.", encoding="utf-8")

    docs = load_documents(
        markdown_directory=kb_dir,
        pdf_directory=pdf_dir,
        include_markdown=True,
        include_pdf=True,
    )

    assert len(docs) == 1
    assert docs[0]["type"] == "markdown"


def test_load_documents_default_source_combines_markdown_and_nested_pdfs(
    monkeypatch,
    tmp_path,
):
    markdown_file = tmp_path / "career_sources" / "README.md"
    pdf_file = tmp_path / "career_sources" / "pdfs" / "ai_report.pdf"
    markdown_file.parent.mkdir(parents=True)
    pdf_file.parent.mkdir(parents=True)
    markdown_file.write_text("# Career Sources\n\nMarkdown source.", encoding="utf-8")
    pdf_file.write_bytes(b"fake pdf bytes")

    monkeypatch.setattr(loader, "DEFAULT_MARKDOWN_DIR", str(tmp_path))
    monkeypatch.setattr(loader, "DEFAULT_PDF_DIR", str(tmp_path))
    monkeypatch.setattr(loader, "PdfReader", FakePdfReader)

    docs = load_documents(markdown_directory=tmp_path)
    source_types = [doc["source_type"] for doc in docs]

    assert source_types == ["markdown", "pdf"]
    assert docs[0]["source"] == str(markdown_file)
    assert docs[1]["source"] == str(pdf_file)
