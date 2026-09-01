"""RAG retriever utilities."""

import hashlib
import json
import shutil
import threading
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

from rag.config import DEFAULT_MIN_RELEVANCE_SCORE
from rag.loader import DEFAULT_MARKDOWN_DIR, DEFAULT_PDF_DIR, load_documents
from rag.splitter import split_documents
from tools.provider_config import get_provider_config, provider_api_key, provider_base_url

load_dotenv()

DEFAULT_PERSIST_DIRECTORY = "data/vector_store/qdrant"
COLLECTION_NAME = "skill_compass_knowledge_base"
SOURCE_METADATA_FILENAME = "source_manifest.json"
INDEX_SCHEMA_VERSION = 7
EMBEDDING_MODEL = "text-embedding-3-small"
# Module-level cache for vector stores, keyed by source directory and index path
_vector_store_cache = {}
# Embedded Qdrant storage should not be accessed concurrently by local clients
# in the same Python process.
_vector_store_lock = threading.RLock()


def clear_cache():
    """Clear the vector store cache. Useful for tests or when knowledge base changes."""
    with _vector_store_lock:
        for cache_key in list(_vector_store_cache):
            _remove_cached_store(cache_key)


def build_documents_from_chunks(chunks):
    """Convert internal chunks into LangChain documents."""
    documents = []

    for chunk in chunks:
        metadata = {
            "source": chunk["source"],
            "chunk_index": chunk["chunk_index"],
        }

        for key in (
            "source_type",
            "filename",
            "page",
            "heading",
            "heading_path",
            "section_level",
            "document_role",
            "source_authority",
            "publisher",
            "published_year",
            "original_source_title",
            "region",
            "topics",
            "title",
            "verified_source_url",
        ):
            if key in chunk:
                metadata[key] = chunk[key]

        documents.append(
            Document(
                page_content=chunk["content"],
                metadata=metadata,
            )
        )

    return documents


def create_embeddings():
    """Create embeddings for the selected OpenAI-compatible provider."""
    provider_config = get_provider_config()
    api_key = provider_api_key(provider_config)
    if provider_config.error or not api_key:
        raise ValueError(provider_config.error or "The selected provider API key is missing.")

    kwargs = {"model": EMBEDDING_MODEL, "api_key": api_key}
    if provider_base_url(provider_config):
        kwargs["base_url"] = provider_base_url(provider_config)
    return OpenAIEmbeddings(**kwargs)


def _normalize_source_directory(directory):
    return Path(directory).expanduser().resolve(strict=False)


def _is_default_source_directory(directory):
    return _normalize_source_directory(directory) == _normalize_source_directory(
        DEFAULT_MARKDOWN_DIR
    )


def _directory_identifier(normalized_directory):
    directory_hash = hashlib.sha256(str(normalized_directory).encode("utf-8"))
    return directory_hash.hexdigest()[:16]


def _effective_persist_directory(persist_directory, normalized_directory):
    return Path(persist_directory) / _directory_identifier(normalized_directory)


def _cache_key(normalized_directory, effective_persist_directory):
    return (
        str(normalized_directory),
        str(Path(effective_persist_directory).resolve(strict=False)),
        COLLECTION_NAME,
    )


def _source_file_entry(file_path):
    normalized_path = file_path.resolve(strict=False)
    file_stat = file_path.stat()
    return {
        "path": str(normalized_path),
        "size": file_stat.st_size,
        "mtime_ns": file_stat.st_mtime_ns,
    }


def _matching_source_files(directory):
    markdown_directory = Path(directory)

    if not markdown_directory.exists():
        raise FileNotFoundError(f"Knowledge base directory not found: {directory}")

    source_files = list(sorted(markdown_directory.rglob("*.md")))

    if _is_default_source_directory(directory):
        pdf_directory = Path(DEFAULT_PDF_DIR)

        if pdf_directory.exists():
            source_files.extend(sorted(pdf_directory.rglob("*.pdf")))

    return source_files


def _similarity_search_with_relevance_scores(
    vector_store,
    query,
    k,
    min_relevance_score,
):
    if hasattr(vector_store, "similarity_search_with_relevance_scores"):
        return vector_store.similarity_search_with_relevance_scores(
            query,
            k=k,
            score_threshold=min_relevance_score,
        )

    return None


def _filter_documents_by_min_score(scored_documents, min_relevance_score):
    documents = []

    for document, score in scored_documents:
        if score >= min_relevance_score:
            documents.append(document)

    return documents


def _source_manifest(directory):
    return [
        _source_file_entry(file_path)
        for file_path in _matching_source_files(directory)
    ]


def _source_fingerprint(source_manifest):
    manifest_json = json.dumps(source_manifest, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(manifest_json.encode("utf-8")).hexdigest()


def _source_metadata_path(effective_persist_directory):
    return Path(effective_persist_directory) / SOURCE_METADATA_FILENAME


def _embedding_identity(provider_config=None):
    """Return non-secret embedding identity used to validate persisted vectors."""
    resolved_provider_config = provider_config or get_provider_config()
    return {
        "provider": resolved_provider_config.provider,
        "model": EMBEDDING_MODEL,
        "base_url": provider_base_url(resolved_provider_config),
    }


def _read_stored_fingerprint(effective_persist_directory, embedding_identity):
    metadata_path = _source_metadata_path(effective_persist_directory)

    if not metadata_path.exists():
        return None

    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if metadata.get("index_schema_version") != INDEX_SCHEMA_VERSION:
        return None

    if metadata.get("embedding_identity") != embedding_identity:
        return None

    return metadata.get("fingerprint")


def _write_source_metadata(
    effective_persist_directory,
    source_manifest,
    fingerprint,
    embedding_identity,
):
    metadata_path = _source_metadata_path(effective_persist_directory)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {
        "embedding_identity": embedding_identity,
        "fingerprint": fingerprint,
        "index_schema_version": INDEX_SCHEMA_VERSION,
        "manifest": source_manifest,
    }
    metadata_path.write_text(
        json.dumps(metadata, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _close_vector_store(vector_store):
    client = getattr(vector_store, "client", None)

    if client and hasattr(client, "close"):
        client.close()


def _remove_cached_store(cache_key):
    cached_store = _vector_store_cache.pop(cache_key, None)

    if cached_store:
        _close_vector_store(cached_store["vector_store"])


def _create_qdrant_client(persist_directory):
    return QdrantClient(path=persist_directory)


def _collection_has_documents(client):
    if not client.collection_exists(COLLECTION_NAME):
        return False

    return client.count(COLLECTION_NAME, exact=True).count > 0


def _load_existing_vector_store(persist_directory, embeddings):
    client = _create_qdrant_client(persist_directory)

    if not _collection_has_documents(client):
        client.close()
        return None

    return QdrantVectorStore(
        client=client,
        collection_name=COLLECTION_NAME,
        embedding=embeddings,
    )


def _build_vector_store(directory, persist_directory, embeddings):
    documents = load_documents(directory)
    chunks = split_documents(documents)
    langchain_documents = build_documents_from_chunks(chunks)

    return QdrantVectorStore.from_documents(
        documents=langchain_documents,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        path=persist_directory,
    )


def create_vector_store(
    directory="data/knowledge_base",
    persist_directory=DEFAULT_PERSIST_DIRECTORY,
    force_rebuild=False,
):
    """Create or load a persistent Qdrant vector store from the knowledge base.

    Uses a module-level cache to avoid rebuilding on every query.
    """
    with _vector_store_lock:
        normalized_directory = _normalize_source_directory(directory)
        effective_persist_directory = _effective_persist_directory(
            persist_directory,
            normalized_directory,
        )
        cache_key = _cache_key(normalized_directory, effective_persist_directory)
        source_manifest = _source_manifest(directory)
        fingerprint = _source_fingerprint(source_manifest)
        provider_config = get_provider_config()
        embedding_identity = _embedding_identity(provider_config)
        api_key = provider_api_key(provider_config)
        if provider_config.error or not api_key:
            raise ValueError(
                provider_config.error or "The selected provider API key is missing."
            )

        if not force_rebuild:
            cached_store = _vector_store_cache.get(cache_key)

            if (
                cached_store
                and cached_store["fingerprint"] == fingerprint
                and cached_store.get("embedding_identity") == embedding_identity
            ):
                return cached_store["vector_store"]

        embeddings = create_embeddings()

        if force_rebuild:
            _remove_cached_store(cache_key)
            shutil.rmtree(effective_persist_directory, ignore_errors=True)
        else:
            stored_fingerprint = _read_stored_fingerprint(
                effective_persist_directory,
                embedding_identity,
            )

            if stored_fingerprint == fingerprint:
                vector_store = _load_existing_vector_store(
                    str(effective_persist_directory),
                    embeddings,
                )

                if vector_store:
                    _vector_store_cache[cache_key] = {
                        "embedding_identity": embedding_identity,
                        "fingerprint": fingerprint,
                        "vector_store": vector_store,
                    }
                    return vector_store

            _remove_cached_store(cache_key)
            shutil.rmtree(effective_persist_directory, ignore_errors=True)

        vector_store = _build_vector_store(
            directory,
            str(effective_persist_directory),
            embeddings,
        )
        _write_source_metadata(
            effective_persist_directory,
            source_manifest,
            fingerprint,
            embedding_identity,
        )
        _vector_store_cache[cache_key] = {
            "embedding_identity": embedding_identity,
            "fingerprint": fingerprint,
            "vector_store": vector_store,
        }
        return vector_store


def rebuild_vector_store(
    directory="data/knowledge_base",
    persist_directory=DEFAULT_PERSIST_DIRECTORY,
):
    """Recreate the persistent vector store from source documents."""
    return create_vector_store(
        directory=directory,
        persist_directory=persist_directory,
        force_rebuild=True,
    )


def retrieve_relevant_chunks(
    query,
    directory="data/knowledge_base",
    k=3,
    min_relevance_score=DEFAULT_MIN_RELEVANCE_SCORE,
):
    """Retrieve relevant chunks for a user query."""
    with _vector_store_lock:
        vector_store = create_vector_store(directory)

        if min_relevance_score is not None:
            scored_documents = _similarity_search_with_relevance_scores(
                vector_store,
                query,
                k,
                min_relevance_score,
            )

            if scored_documents is not None:
                return _filter_documents_by_min_score(
                    scored_documents,
                    min_relevance_score,
                )

        return vector_store.similarity_search(query, k=k)
