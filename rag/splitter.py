"""Document splitting utilities for RAG."""

from functools import lru_cache
import re

import tiktoken
from langchain_text_splitters import RecursiveCharacterTextSplitter


_BYTE_ENCODING = tiktoken.Encoding(
    name="cognivia_byte_encoding",
    pat_str=r"[\s\S]",
    mergeable_ranks={bytes([index]): index for index in range(256)},
    special_tokens={},
)
_STANDARD_ENCODING_NAME = "cl100k_base"

_OPTIONAL_METADATA_KEYS = (
    "document_role",
    "source_authority",
    "publisher",
    "published_year",
    "original_source_title",
    "region",
    "topics",
    "title",
    "verified_source_url",
)
_MARKDOWN_HEADER_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")


def _get_offline_fallback_tokenizer():
    """Return a deterministic byte tokenizer when cl100k_base is unavailable."""
    return _BYTE_ENCODING


@lru_cache(maxsize=1)
def _get_tokenizer():
    try:
        return tiktoken.get_encoding(_STANDARD_ENCODING_NAME)
    except (OSError, ValueError):
        return _get_offline_fallback_tokenizer()


@lru_cache(maxsize=4096)
def _token_count(text):
    return len(_get_tokenizer().encode(text))


def _build_splitter(chunk_size, chunk_overlap):
    return RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=_token_count,
        separators=["\n\n", "\n", " ", ""],
    )


def _is_markdown_document(document, source, source_type, filename):
    if str(source_type).lower() == "markdown":
        return True

    for value in (filename, source, document.get("path")):
        if value and str(value).lower().endswith((".md", ".markdown")):
            return True

    return False


def _base_chunk_metadata(document, source, source_type, filename, page):
    chunk = {
        "source": source,
        "source_type": source_type,
    }

    if filename:
        chunk["filename"] = filename

    if page is not None:
        chunk["page"] = page

    for key in _OPTIONAL_METADATA_KEYS:
        if key in document:
            chunk[key] = document[key]

    return chunk


def _split_markdown_sections(content):
    sections = []
    current_lines = []
    current_heading = None
    current_heading_path = []
    current_section_level = None
    heading_stack = []

    def flush_section():
        section_content = "\n".join(current_lines).strip()
        if not section_content:
            return

        sections.append(
            {
                "content": section_content,
                "heading": current_heading,
                "heading_path": " > ".join(current_heading_path),
                "section_level": current_section_level,
            }
        )

    for line in content.splitlines():
        match = _MARKDOWN_HEADER_PATTERN.match(line)

        if match:
            flush_section()
            level = len(match.group(1))
            heading = match.group(2).strip()
            heading_stack = heading_stack[: level - 1]
            heading_stack.append(heading)
            current_lines = [line]
            current_heading = heading
            current_heading_path = list(heading_stack)
            current_section_level = level
        else:
            current_lines.append(line)

    flush_section()
    return sections


def _split_document_content(document, content, splitter):
    source = document.get("source", "unknown")
    source_type = document.get("source_type", document.get("type", "unknown"))
    filename = document.get("filename")
    page = document.get("page")

    if _is_markdown_document(document, source, source_type, filename):
        sections = _split_markdown_sections(content)
        if sections:
            return source, source_type, filename, page, sections

    return (
        source,
        source_type,
        filename,
        page,
        [{"content": chunk_content} for chunk_content in splitter.split_text(content)],
    )


def split_documents(documents, chunk_size=1000, chunk_overlap=200):
    """
    Split loaded documents into smaller chunks.

    Each chunk keeps source metadata so retrieved context can be traced back.
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")

    if chunk_overlap < 0:
        raise ValueError("chunk_overlap cannot be negative.")

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size.")

    splitter = _build_splitter(chunk_size, chunk_overlap)
    chunks = []

    for document in documents:
        content = document.get("content", "")

        if not content.strip():
            continue

        source, source_type, filename, page, sections = _split_document_content(
            document,
            content,
            splitter,
        )
        chunk_index = 0

        for section in sections:
            section_content = section["content"]
            for chunk_content in splitter.split_text(section_content):
                if not chunk_content:
                    continue

                chunk = _base_chunk_metadata(
                    document,
                    source,
                    source_type,
                    filename,
                    page,
                )
                chunk.update(
                    {
                        "content": chunk_content,
                        "chunk_index": chunk_index,
                    }
                )

                if section.get("heading"):
                    chunk["heading"] = section["heading"]
                    chunk["heading_path"] = section["heading_path"]
                    chunk["section_level"] = section["section_level"]

                chunks.append(chunk)
                chunk_index += 1

    return chunks
