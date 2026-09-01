from pathlib import Path

from pypdf import PdfReader


DEFAULT_MARKDOWN_DIR = "data/knowledge_base"
DEFAULT_PDF_DIR = DEFAULT_MARKDOWN_DIR
MARKDOWN_METADATA_KEYS = {
    "document_role",
    "source_authority",
    "publisher",
    "published_year",
    "publication_year",
    "original_source_title",
    "region",
    "topics",
    "title",
    "verified_source_url",
}


def _normalize_directory_path(directory):
    return Path(directory).expanduser().resolve(strict=False)


def _is_default_markdown_directory(directory):
    return _normalize_directory_path(directory) == _normalize_directory_path(
        DEFAULT_MARKDOWN_DIR
    )


def _metadata_from_markdown_path(file_path, base_directory):
    relative_parts = file_path.relative_to(base_directory).parts
    section = relative_parts[0] if len(relative_parts) > 1 else ""

    if section == "derived":
        return {
            "document_role": "derived_summary",
            "source_authority": "derived_official",
        }

    if section == "internal" or len(relative_parts) == 1:
        return {
            "document_role": "internal_note",
            "source_authority": "internal",
        }

    return {
        "document_role": "project_documentation",
        "source_authority": "internal",
    }


def _metadata_from_markdown_content(content):
    metadata = {}

    for line in content.splitlines():
        if line.startswith("## "):
            break

        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        normalized_key = key.strip().lower()

        if normalized_key not in MARKDOWN_METADATA_KEYS:
            continue

        metadata_key = (
            "published_year"
            if normalized_key == "publication_year"
            else normalized_key
        )
        metadata[metadata_key] = value.strip()

    return metadata


def _metadata_from_pdf_path(file_path):
    metadata = {
        "document_role": "primary_source",
        "source_authority": "official",
        "source_type": "pdf",
    }

    if "future_of_jobs" in file_path.stem.lower():
        metadata.update(
            {
                "publisher": "World Economic Forum",
                "published_year": "2025",
                "title": "Future of Jobs Report 2025",
            }
        )

    return metadata


def load_markdown_documents(directory=DEFAULT_MARKDOWN_DIR):
    knowledge_base_path = Path(directory)

    if not knowledge_base_path.exists():
        raise FileNotFoundError(f"Knowledge base directory not found: {directory}")

    documents = []

    for file_path in sorted(knowledge_base_path.rglob("*.md")):
        content = file_path.read_text(encoding="utf-8").strip()

        if content:
            metadata = {
                **_metadata_from_markdown_path(file_path, knowledge_base_path),
                **_metadata_from_markdown_content(content),
            }
            documents.append(
                {
                    "source": str(file_path),
                    "filename": file_path.name,
                    "type": "markdown",
                    "source_type": "markdown",
                    "content": content,
                    **metadata,
                }
            )

    return documents


def load_pdf_documents(directory=DEFAULT_PDF_DIR):
    pdf_path = Path(directory)

    if not pdf_path.exists():
        return []

    documents = []

    for file_path in sorted(pdf_path.rglob("*.pdf")):
        reader = PdfReader(str(file_path))
        source_metadata = _metadata_from_pdf_path(file_path)

        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            content = text.strip()

            if content:
                documents.append(
                    {
                        "source": str(file_path),
                        "filename": file_path.name,
                        "type": "pdf",
                        "source_type": "pdf",
                        "page": page_number,
                        "content": content,
                        **source_metadata,
                    }
                )

    return documents


def load_documents(
    markdown_directory=DEFAULT_MARKDOWN_DIR,
    pdf_directory=None,
    include_markdown=True,
    include_pdf=True,
):
    documents = []

    if include_markdown:
        documents.extend(load_markdown_documents(markdown_directory))

    should_load_default_pdfs = (
        pdf_directory is None
        and _is_default_markdown_directory(markdown_directory)
    )

    if include_pdf:
        if pdf_directory is not None:
            documents.extend(load_pdf_documents(pdf_directory))
        elif should_load_default_pdfs:
            documents.extend(load_pdf_documents(DEFAULT_PDF_DIR))

    return documents
