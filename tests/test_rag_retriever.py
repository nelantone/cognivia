"""Tests for rag.retriever module."""

import json
import os
from unittest.mock import Mock

import pytest

import rag.loader as loader
import rag.retriever as retriever
from rag.config import DEFAULT_MIN_RELEVANCE_SCORE
from rag.retriever import (
    build_documents_from_chunks,
    clear_cache,
    create_vector_store,
    rebuild_vector_store,
    retrieve_relevant_chunks,
)


@pytest.fixture(autouse=True)
def clear_vector_store_cache():
    """Keep cache-related tests isolated from each other."""
    clear_cache()
    yield
    clear_cache()


def expected_persist_directory(directory, persist_directory=None):
    """Return the isolated Qdrant path for a test source directory."""
    if persist_directory is None:
        persist_directory = retriever.DEFAULT_PERSIST_DIRECTORY

    normalized_directory = retriever._normalize_source_directory(directory)
    return str(
        retriever._effective_persist_directory(
            persist_directory,
            normalized_directory,
        )
    )


def create_source_directory(tmp_path, name="knowledge-base", filename="doc.md"):
    """Create a small source directory for manifest-based retriever tests."""
    source_directory = tmp_path / name
    source_directory.mkdir()
    source_file = source_directory / filename
    source_file.write_text("source content", encoding="utf-8")
    return source_directory


def write_current_source_metadata(directory, persist_directory=None):
    """Write fingerprint metadata for the current source files."""
    effective_persist_directory = expected_persist_directory(
        directory,
        persist_directory,
    )
    source_manifest = retriever._source_manifest(directory)
    fingerprint = retriever._source_fingerprint(source_manifest)
    retriever._write_source_metadata(
        effective_persist_directory,
        source_manifest,
        fingerprint,
        {
            "base_url": "https://openrouter.ai/api/v1",
            "model": "text-embedding-3-small",
            "provider": "openrouter",
        },
    )
    return effective_persist_directory


def metadata_path(directory, persist_directory=None):
    """Return the source metadata JSON path for a test source directory."""
    return (
        retriever.Path(expected_persist_directory(directory, persist_directory))
        / retriever.SOURCE_METADATA_FILENAME
    )


def qdrant_client_with_count(count):
    """Create a mocked local Qdrant client with a collection count."""
    count_result = Mock()
    count_result.count = count
    client = Mock()
    client.collection_exists.return_value = count > 0
    client.count.return_value = count_result
    return client


def cached_store_with_client():
    """Create a cached vector store entry with a mocked Qdrant client."""
    client = Mock()
    vector_store = Mock()
    vector_store.client = client
    cached_store = {
        "fingerprint": "test-fingerprint",
        "vector_store": vector_store,
    }
    return cached_store, client


class TestBuildDocumentsFromChunks:
    """Tests for build_documents_from_chunks function."""

    def test_converts_chunks_to_documents(self):
        """Verify chunks are converted to LangChain documents with metadata."""
        chunks = [
            {
                "content": "First chunk content",
                "source": "test1.md",
                "chunk_index": 0,
                "heading": "Intro",
                "heading_path": "Guide > Intro",
                "section_level": 2,
            },
            {"content": "Second chunk content", "source": "test2.md", "chunk_index": 1},
        ]
        docs = build_documents_from_chunks(chunks)

        assert len(docs) == 2
        assert docs[0].page_content == "First chunk content"
        assert docs[0].metadata["source"] == "test1.md"
        assert docs[0].metadata["chunk_index"] == 0
        assert docs[0].metadata["heading"] == "Intro"
        assert docs[0].metadata["heading_path"] == "Guide > Intro"
        assert docs[0].metadata["section_level"] == 2
        assert docs[1].page_content == "Second chunk content"
        assert docs[1].metadata["source"] == "test2.md"
        assert docs[1].metadata["chunk_index"] == 1

    def test_empty_chunks_returns_empty_list(self):
        """Verify empty input returns empty list."""
        docs = build_documents_from_chunks([])
        assert docs == []

    def test_preserves_display_metadata(self):
        """Verify source type and page metadata survive document conversion."""
        chunks = [
            {
                "content": "Future jobs evidence",
                "source": "future_jobs.pdf",
                "source_type": "pdf",
                "filename": "future_jobs.pdf",
                "page": 43,
                "document_role": "primary_source",
                "source_authority": "official",
                "publisher": "World Economic Forum",
                "published_year": "2025",
                "chunk_index": 0,
            }
        ]

        docs = build_documents_from_chunks(chunks)

        assert docs[0].metadata["source_type"] == "pdf"
        assert docs[0].metadata["filename"] == "future_jobs.pdf"
        assert docs[0].metadata["page"] == 43
        assert docs[0].metadata["document_role"] == "primary_source"
        assert docs[0].metadata["source_authority"] == "official"
        assert docs[0].metadata["publisher"] == "World Economic Forum"
        assert docs[0].metadata["published_year"] == "2025"

    def test_preserves_original_source_title_metadata(self):
        """Verify derived-summary official title survives document conversion."""
        chunks = [
            {
                "content": "AI skills evidence",
                "source": "oecd_ai_skills_gap_2025.md",
                "source_type": "markdown",
                "filename": "oecd_ai_skills_gap_2025.md",
                "document_role": "derived_summary",
                "source_authority": "derived_official",
                "original_source_title": "AI and skills: What we know so far",
                "chunk_index": 0,
            }
        ]

        docs = build_documents_from_chunks(chunks)

        assert (
            docs[0].metadata["original_source_title"]
            == "AI and skills: What we know so far"
        )


class TestCacheManagement:
    """Tests for vector store cache cleanup."""

    def test_clear_cache_closes_cached_qdrant_client(self):
        """Verify clear_cache closes the cached vector store client."""
        cached_store, client = cached_store_with_client()
        retriever._vector_store_cache["cache-key"] = cached_store

        clear_cache()

        client.close.assert_called_once_with()
        assert retriever._vector_store_cache == {}

    def test_clear_cache_closes_all_cached_qdrant_clients(self):
        """Verify clear_cache closes every cached vector store client."""
        cached_store_a, client_a = cached_store_with_client()
        cached_store_b, client_b = cached_store_with_client()
        retriever._vector_store_cache["cache-key-a"] = cached_store_a
        retriever._vector_store_cache["cache-key-b"] = cached_store_b

        clear_cache()

        client_a.close.assert_called_once_with()
        client_b.close.assert_called_once_with()
        assert retriever._vector_store_cache == {}

    def test_clear_cache_empty_cache_is_safe(self):
        """Verify clearing an empty cache does not fail."""
        clear_cache()

        assert retriever._vector_store_cache == {}

    def test_remove_cached_store_closes_and_removes_only_requested_store(self):
        """Verify _remove_cached_store keeps its single-entry behavior."""
        cached_store_a, client_a = cached_store_with_client()
        cached_store_b, client_b = cached_store_with_client()
        retriever._vector_store_cache["cache-key-a"] = cached_store_a
        retriever._vector_store_cache["cache-key-b"] = cached_store_b

        retriever._remove_cached_store("cache-key-a")

        client_a.close.assert_called_once_with()
        client_b.close.assert_not_called()
        assert "cache-key-a" not in retriever._vector_store_cache
        assert retriever._vector_store_cache["cache-key-b"] is cached_store_b

    def test_remove_cached_store_missing_key_is_safe(self):
        """Verify removing a missing cache key does not fail."""
        retriever._remove_cached_store("missing-cache-key")

        assert retriever._vector_store_cache == {}


class TestCreateVectorStore:
    """Tests for create_vector_store function."""

    def test_creates_persisted_index_when_metadata_is_missing(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify source documents are loaded when no fingerprint metadata exists."""
        source_directory = create_source_directory(tmp_path)
        raw_documents = [{"content": "Raw document", "source": "example.md"}]
        chunks = [
            {"content": "Chunk content", "source": "example.md", "chunk_index": 0}
        ]
        fake_embeddings = object()
        created_store = object()

        load_documents = Mock(return_value=raw_documents)
        split_documents = Mock(return_value=chunks)
        embeddings_class = Mock(return_value=fake_embeddings)
        vector_store_class = Mock()
        vector_store_class.from_documents = Mock(return_value=created_store)

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", embeddings_class)
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)

        store = create_vector_store(str(source_directory))
        expected_persist = expected_persist_directory(source_directory)

        assert store is created_store
        vector_store_class.assert_not_called()
        load_documents.assert_called_once_with(str(source_directory))
        split_documents.assert_called_once_with(raw_documents)
        embeddings_class.assert_called_once_with(
            model="text-embedding-3-small",
            api_key="test-api-key",
            base_url="https://openrouter.ai/api/v1",
        )
        vector_store_class.from_documents.assert_called_once()
        call_kwargs = vector_store_class.from_documents.call_args.kwargs
        assert call_kwargs["embedding"] is fake_embeddings
        assert call_kwargs["collection_name"] == retriever.COLLECTION_NAME
        assert call_kwargs["path"] == expected_persist
        assert len(call_kwargs["documents"]) == 1
        assert call_kwargs["documents"][0].page_content == "Chunk content"
        assert call_kwargs["documents"][0].metadata == {
            "source": "example.md",
            "chunk_index": 0,
        }
        assert metadata_path(source_directory).exists()

    def test_loads_existing_index_without_loading_documents(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify an existing Qdrant collection skips source document processing."""
        source_directory = create_source_directory(tmp_path)
        write_current_source_metadata(source_directory)
        persisted_store = Mock()
        qdrant_client = qdrant_client_with_count(2)
        fake_embeddings = object()
        load_documents = Mock()
        split_documents = Mock()
        embeddings_class = Mock(return_value=fake_embeddings)
        qdrant_client_class = Mock(return_value=qdrant_client)
        vector_store_class = Mock(return_value=persisted_store)
        vector_store_class.from_documents = Mock()

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", embeddings_class)
        monkeypatch.setattr(retriever, "QdrantClient", qdrant_client_class)
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)

        store = create_vector_store(str(source_directory))

        assert store is persisted_store
        qdrant_client_class.assert_called_once_with(
            path=expected_persist_directory(source_directory),
        )
        vector_store_class.assert_called_once_with(
            client=qdrant_client,
            collection_name=retriever.COLLECTION_NAME,
            embedding=fake_embeddings,
        )
        load_documents.assert_not_called()
        split_documents.assert_not_called()
        vector_store_class.from_documents.assert_not_called()

    def test_matching_embedding_identity_reuses_existing_index(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify matching source and embedding identity reuses persisted Qdrant."""
        source_directory = create_source_directory(tmp_path)
        write_current_source_metadata(source_directory)
        persisted_store = Mock()
        qdrant_client = qdrant_client_with_count(2)
        fake_embeddings = object()
        load_documents = Mock()
        split_documents = Mock()
        embeddings_class = Mock(return_value=fake_embeddings)
        qdrant_client_class = Mock(return_value=qdrant_client)
        vector_store_class = Mock(return_value=persisted_store)
        vector_store_class.from_documents = Mock()

        monkeypatch.delenv("COGNIVIA_LLM_PROVIDER", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", embeddings_class)
        monkeypatch.setattr(retriever, "QdrantClient", qdrant_client_class)
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)

        store = create_vector_store(str(source_directory))

        assert store is persisted_store
        qdrant_client_class.assert_called_once_with(
            path=expected_persist_directory(source_directory),
        )
        load_documents.assert_not_called()
        split_documents.assert_not_called()
        vector_store_class.from_documents.assert_not_called()

    def test_caching_returns_same_instance(self, monkeypatch, tmp_path):
        """Verify repeated calls return the same cached instance."""
        source_directory = create_source_directory(tmp_path)
        write_current_source_metadata(source_directory)
        persisted_store = Mock()
        qdrant_client = qdrant_client_with_count(3)
        embeddings_class = Mock(return_value=object())
        qdrant_client_class = Mock(return_value=qdrant_client)
        vector_store_class = Mock(return_value=persisted_store)
        vector_store_class.from_documents = Mock()
        load_documents = Mock()
        split_documents = Mock()

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "QdrantClient", qdrant_client_class)
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", embeddings_class)

        store1 = create_vector_store(str(source_directory))
        store2 = create_vector_store(str(source_directory))

        assert store1 is store2
        qdrant_client_class.assert_called_once_with(
            path=expected_persist_directory(source_directory),
        )
        vector_store_class.assert_called_once()
        load_documents.assert_not_called()
        split_documents.assert_not_called()
        embeddings_class.assert_called_once()
        vector_store_class.from_documents.assert_not_called()

    def test_provider_identity_change_invalidates_cached_index(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify provider changes do not reuse the in-process vector store cache."""
        source_directory = create_source_directory(tmp_path)
        stores = [object(), object()]
        load_documents = Mock(return_value=[{"content": "source", "source": "doc.md"}])
        split_documents = Mock(
            return_value=[
                {"content": "source", "source": "doc.md", "chunk_index": 0}
            ]
        )
        vector_store_class = Mock()
        vector_store_class.from_documents = Mock(side_effect=stores)
        rmtree = Mock()

        monkeypatch.setenv("COGNIVIA_LLM_PROVIDER", "openrouter")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", Mock(return_value=object()))
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)
        monkeypatch.setattr(retriever.shutil, "rmtree", rmtree)

        first_store = create_vector_store(str(source_directory))
        rmtree.reset_mock()
        monkeypatch.setenv("COGNIVIA_LLM_PROVIDER", "openai")
        second_store = create_vector_store(str(source_directory))

        assert first_store is stores[0]
        assert second_store is stores[1]
        assert vector_store_class.from_documents.call_count == 2
        rmtree.assert_called_once_with(
            retriever.Path(expected_persist_directory(source_directory)),
            ignore_errors=True,
        )

    def test_different_directories_get_separate_caches(self, monkeypatch, tmp_path):
        """Verify different directories get separate cache entries and indexes."""
        first_directory = create_source_directory(tmp_path, "first-directory")
        second_directory = create_source_directory(tmp_path, "second-directory")
        write_current_source_metadata(first_directory)
        write_current_source_metadata(second_directory)
        store_a = Mock()
        store_b = Mock()
        client_a = qdrant_client_with_count(1)
        client_b = qdrant_client_with_count(1)
        load_documents = Mock()
        split_documents = Mock()
        embeddings_class = Mock(return_value=object())
        qdrant_client_class = Mock(side_effect=[client_a, client_b])
        vector_store_class = Mock(side_effect=[store_a, store_b])
        vector_store_class.from_documents = Mock()

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", embeddings_class)
        monkeypatch.setattr(retriever, "QdrantClient", qdrant_client_class)
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)

        first_store = create_vector_store(str(first_directory))
        second_store = create_vector_store(str(second_directory))
        first_persist = expected_persist_directory(first_directory)
        second_persist = expected_persist_directory(second_directory)

        assert first_store is store_a
        assert second_store is store_b
        assert first_store is not second_store
        assert first_persist != second_persist
        assert qdrant_client_class.call_count == 2
        assert qdrant_client_class.call_args_list[0].kwargs["path"] == first_persist
        assert qdrant_client_class.call_args_list[1].kwargs["path"] == second_persist
        assert vector_store_class.call_count == 2
        assert vector_store_class.call_args_list[0].kwargs["client"] is client_a
        assert vector_store_class.call_args_list[1].kwargs["client"] is client_b
        load_documents.assert_not_called()
        split_documents.assert_not_called()
        vector_store_class.from_documents.assert_not_called()

    def test_existing_index_for_one_directory_is_not_reused_for_another(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify directory B opens its own index even when directory A exists."""
        directory_a = create_source_directory(tmp_path, "directory-a")
        directory_b = create_source_directory(tmp_path, "directory-b")
        write_current_source_metadata(directory_a)
        write_current_source_metadata(directory_b)
        store_a = Mock()
        store_b = Mock()
        client_a = qdrant_client_with_count(4)
        client_b = qdrant_client_with_count(5)
        qdrant_client_class = Mock(side_effect=[client_a, client_b])
        vector_store_class = Mock(side_effect=[store_a, store_b])
        vector_store_class.from_documents = Mock()

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "QdrantClient", qdrant_client_class)
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", Mock(return_value=object()))
        monkeypatch.setattr(retriever, "load_documents", Mock())
        monkeypatch.setattr(retriever, "split_documents", Mock())

        store_a_result = create_vector_store(str(directory_a))
        store_b_result = create_vector_store(str(directory_b))
        persist_directories = [
            call.kwargs["path"] for call in qdrant_client_class.call_args_list
        ]

        assert store_a_result is store_a
        assert store_b_result is store_b
        assert persist_directories == [
            expected_persist_directory(directory_a),
            expected_persist_directory(directory_b),
        ]
        assert persist_directories[0] != persist_directories[1]
        retriever.load_documents.assert_not_called()
        retriever.split_documents.assert_not_called()
        vector_store_class.from_documents.assert_not_called()

    def test_force_rebuild_recreates_index(self, monkeypatch, tmp_path):
        """Verify force rebuild removes the persisted index and rebuilds it."""
        source_directory = create_source_directory(tmp_path)
        write_current_source_metadata(source_directory)
        raw_documents = [{"content": "Raw document", "source": "example.md"}]
        chunks = [
            {"content": "Chunk content", "source": "example.md", "chunk_index": 0}
        ]
        created_store = object()
        fake_embeddings = object()
        load_documents = Mock(return_value=raw_documents)
        split_documents = Mock(return_value=chunks)
        embeddings_class = Mock(return_value=fake_embeddings)
        vector_store_class = Mock()
        vector_store_class.from_documents = Mock(return_value=created_store)
        rmtree = Mock()

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", embeddings_class)
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)
        monkeypatch.setattr(retriever.shutil, "rmtree", rmtree)

        store = create_vector_store(str(source_directory), force_rebuild=True)
        expected_persist = expected_persist_directory(source_directory)

        assert store is created_store
        rmtree.assert_called_once_with(
            retriever.Path(expected_persist),
            ignore_errors=True,
        )
        vector_store_class.assert_not_called()
        load_documents.assert_called_once_with(str(source_directory))
        split_documents.assert_called_once_with(raw_documents)
        vector_store_class.from_documents.assert_called_once()
        assert (
            vector_store_class.from_documents.call_args.kwargs["path"]
            == expected_persist
        )

    def test_force_rebuild_removes_only_requested_directory_index(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify rebuilding directory A does not remove or rebuild directory B."""
        directory_a = create_source_directory(tmp_path, "directory-a")
        directory_b = create_source_directory(tmp_path, "directory-b")
        write_current_source_metadata(directory_b)
        store_b = Mock()
        qdrant_client = qdrant_client_with_count(2)
        rebuilt_store_a = object()
        qdrant_client_class = Mock(return_value=qdrant_client)
        vector_store_class = Mock(return_value=store_b)
        vector_store_class.from_documents = Mock(return_value=rebuilt_store_a)
        load_documents = Mock(return_value=[{"content": "A", "source": "a.md"}])
        split_documents = Mock(
            return_value=[{"content": "A", "source": "a.md", "chunk_index": 0}]
        )
        rmtree = Mock()

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "QdrantClient", qdrant_client_class)
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", Mock(return_value=object()))
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)
        monkeypatch.setattr(retriever.shutil, "rmtree", rmtree)

        directory_b_store = create_vector_store(str(directory_b))
        directory_a_store = create_vector_store(str(directory_a), force_rebuild=True)

        assert directory_b_store is store_b
        assert directory_a_store is rebuilt_store_a
        rmtree.assert_called_once_with(
            retriever.Path(expected_persist_directory(directory_a)),
            ignore_errors=True,
        )
        load_documents.assert_called_once_with(str(directory_a))
        split_documents.assert_called_once()
        vector_store_class.from_documents.assert_called_once()
        qdrant_client_class.assert_called_once_with(
            path=expected_persist_directory(directory_b),
        )
        assert vector_store_class.call_count == 1
        assert (
            vector_store_class.call_args.kwargs["client"]
            is qdrant_client
        )

    def test_normalized_equivalent_paths_use_same_index_and_cache(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify equivalent paths resolve to the same persistent index."""
        source_directory = tmp_path / "knowledge-base"
        source_directory.mkdir()
        (source_directory / "doc.md").write_text("source content", encoding="utf-8")
        equivalent_directory = source_directory / ".." / source_directory.name
        write_current_source_metadata(source_directory)
        persisted_store = Mock()
        qdrant_client = qdrant_client_with_count(2)
        qdrant_client_class = Mock(return_value=qdrant_client)
        vector_store_class = Mock(return_value=persisted_store)
        vector_store_class.from_documents = Mock()

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "QdrantClient", qdrant_client_class)
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", Mock(return_value=object()))
        monkeypatch.setattr(retriever, "load_documents", Mock())
        monkeypatch.setattr(retriever, "split_documents", Mock())

        store1 = create_vector_store(str(source_directory))
        store2 = create_vector_store(str(equivalent_directory))

        assert store1 is store2
        qdrant_client_class.assert_called_once_with(
            path=expected_persist_directory(source_directory),
        )
        vector_store_class.assert_called_once_with(
            client=qdrant_client,
            collection_name=retriever.COLLECTION_NAME,
            embedding=vector_store_class.call_args.kwargs["embedding"],
        )
        retriever.load_documents.assert_not_called()
        retriever.split_documents.assert_not_called()

    def test_added_source_file_invalidates_and_rebuilds_index(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify adding a source file rebuilds the affected persisted index."""
        source_directory = create_source_directory(tmp_path)
        write_current_source_metadata(source_directory)
        (source_directory / "new.md").write_text("new content", encoding="utf-8")
        created_store = object()
        load_documents = Mock(return_value=[{"content": "new", "source": "new.md"}])
        split_documents = Mock(
            return_value=[{"content": "new", "source": "new.md", "chunk_index": 0}]
        )
        vector_store_class = Mock()
        vector_store_class.from_documents = Mock(return_value=created_store)
        rmtree = Mock()

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", Mock(return_value=object()))
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)
        monkeypatch.setattr(retriever.shutil, "rmtree", rmtree)

        store = create_vector_store(str(source_directory))

        assert store is created_store
        rmtree.assert_called_once_with(
            retriever.Path(expected_persist_directory(source_directory)),
            ignore_errors=True,
        )
        load_documents.assert_called_once_with(str(source_directory))
        split_documents.assert_called_once()
        vector_store_class.from_documents.assert_called_once()

    def test_nested_markdown_source_file_is_included_in_manifest(self, tmp_path):
        """Verify derived/internal Markdown files are fingerprinted."""
        source_directory = create_source_directory(tmp_path)
        derived_directory = source_directory / "derived"
        derived_directory.mkdir()
        nested_file = derived_directory / "oecd_ai_and_skills.md"
        nested_file.write_text("derived content", encoding="utf-8")

        manifest_paths = {
            retriever.Path(entry["path"]).name
            for entry in retriever._source_manifest(source_directory)
        }

        assert "doc.md" in manifest_paths
        assert "oecd_ai_and_skills.md" in manifest_paths

    def test_default_nested_pdf_source_file_is_included_in_manifest(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify default knowledge-base PDFs are fingerprinted recursively."""
        source_directory = create_source_directory(tmp_path)
        pdf_directory = source_directory / "career_sources" / "pdfs"
        pdf_directory.mkdir(parents=True)
        pdf_file = pdf_directory / "ai_skills_report.pdf"
        pdf_file.write_bytes(b"fake pdf bytes")

        monkeypatch.setattr(retriever, "DEFAULT_MARKDOWN_DIR", str(source_directory))
        monkeypatch.setattr(retriever, "DEFAULT_PDF_DIR", str(source_directory))

        manifest_paths = {
            retriever.Path(entry["path"]).name
            for entry in retriever._source_manifest(source_directory)
        }

        assert "doc.md" in manifest_paths
        assert "ai_skills_report.pdf" in manifest_paths

    def test_equivalent_default_path_variants_include_same_pdfs_in_manifest(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify default path aliases fingerprint the same Markdown/PDF set."""
        source_directory = create_source_directory(tmp_path)
        pdf_directory = source_directory / "career_sources" / "pdfs"
        pdf_directory.mkdir(parents=True)
        pdf_file = pdf_directory / "ai_skills_report.pdf"
        pdf_file.write_bytes(b"fake pdf bytes")
        equivalent_directory = source_directory / ".." / source_directory.name

        monkeypatch.setattr(retriever, "DEFAULT_MARKDOWN_DIR", str(source_directory))
        monkeypatch.setattr(retriever, "DEFAULT_PDF_DIR", str(source_directory))

        source_manifest = retriever._source_manifest(source_directory)
        equivalent_manifest = retriever._source_manifest(equivalent_directory)
        manifest_paths = {
            retriever.Path(entry["path"]).name for entry in equivalent_manifest
        }

        assert "doc.md" in manifest_paths
        assert "ai_skills_report.pdf" in manifest_paths
        assert equivalent_manifest == source_manifest
        assert retriever._source_fingerprint(equivalent_manifest) == (
            retriever._source_fingerprint(source_manifest)
        )

    def test_equivalent_default_path_variant_loads_default_pdfs(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify loader PDF inclusion uses normalized default path equality."""
        source_directory = create_source_directory(tmp_path)
        equivalent_directory = source_directory / ".." / source_directory.name
        pdf_document = {"content": "pdf evidence", "source": "report.pdf"}
        load_pdf_documents = Mock(return_value=[pdf_document])

        monkeypatch.setattr(loader, "DEFAULT_MARKDOWN_DIR", str(source_directory))
        monkeypatch.setattr(loader, "DEFAULT_PDF_DIR", str(source_directory))
        monkeypatch.setattr(loader, "load_pdf_documents", load_pdf_documents)

        documents = loader.load_documents(equivalent_directory)

        assert pdf_document in documents
        load_pdf_documents.assert_called_once_with(str(source_directory))

    def test_equivalent_default_path_does_not_rebuild_normalized_index(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify path aliases reuse the same cached default-source index."""
        source_directory = create_source_directory(tmp_path)
        pdf_directory = source_directory / "career_sources" / "pdfs"
        pdf_directory.mkdir(parents=True)
        pdf_file = pdf_directory / "ai_skills_report.pdf"
        pdf_file.write_bytes(b"fake pdf bytes")
        equivalent_directory = source_directory / ".." / source_directory.name
        persist_directory = tmp_path / "indexes"
        raw_documents = [{"content": "Raw document", "source": "doc.md"}]
        chunks = [
            {"content": "Chunk content", "source": "doc.md", "chunk_index": 0}
        ]
        created_store = object()
        load_documents = Mock(return_value=raw_documents)
        split_documents = Mock(return_value=chunks)
        embeddings_class = Mock(return_value=object())
        vector_store_class = Mock()
        vector_store_class.from_documents = Mock(return_value=created_store)

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "DEFAULT_MARKDOWN_DIR", str(source_directory))
        monkeypatch.setattr(retriever, "DEFAULT_PDF_DIR", str(source_directory))
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", embeddings_class)
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)

        store = create_vector_store(
            str(source_directory),
            persist_directory=str(persist_directory),
        )
        equivalent_store = create_vector_store(
            str(equivalent_directory),
            persist_directory=str(persist_directory),
        )

        assert equivalent_store is store
        assert store is created_store
        load_documents.assert_called_once_with(str(source_directory))
        split_documents.assert_called_once_with(raw_documents)
        embeddings_class.assert_called_once()
        vector_store_class.from_documents.assert_called_once()

    def test_modified_source_file_invalidates_index(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify metadata changes on a source file rebuild the index."""
        source_directory = create_source_directory(tmp_path)
        source_file = source_directory / "doc.md"
        write_current_source_metadata(source_directory)
        source_file.write_text("updated content", encoding="utf-8")
        os.utime(source_file, ns=(2_000_000_000, 2_000_000_000))
        created_store = object()
        load_documents = Mock(return_value=[{"content": "updated", "source": "doc.md"}])
        split_documents = Mock(
            return_value=[{"content": "updated", "source": "doc.md", "chunk_index": 0}]
        )
        vector_store_class = Mock()
        vector_store_class.from_documents = Mock(return_value=created_store)

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", Mock(return_value=object()))
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)
        monkeypatch.setattr(retriever.shutil, "rmtree", Mock())

        store = create_vector_store(str(source_directory))

        assert store is created_store
        load_documents.assert_called_once_with(str(source_directory))
        split_documents.assert_called_once()
        vector_store_class.from_documents.assert_called_once()

    def test_removed_source_file_invalidates_index(self, monkeypatch, tmp_path):
        """Verify removing a source file rebuilds the index."""
        source_directory = create_source_directory(tmp_path)
        removed_file = source_directory / "remove-me.md"
        removed_file.write_text("removed content", encoding="utf-8")
        write_current_source_metadata(source_directory)
        removed_file.unlink()
        created_store = object()
        load_documents = Mock(return_value=[{"content": "remaining", "source": "doc.md"}])
        split_documents = Mock(
            return_value=[
                {"content": "remaining", "source": "doc.md", "chunk_index": 0}
            ]
        )
        vector_store_class = Mock()
        vector_store_class.from_documents = Mock(return_value=created_store)

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", Mock(return_value=object()))
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)
        monkeypatch.setattr(retriever.shutil, "rmtree", Mock())

        store = create_vector_store(str(source_directory))

        assert store is created_store
        load_documents.assert_called_once_with(str(source_directory))
        split_documents.assert_called_once()
        vector_store_class.from_documents.assert_called_once()

    def test_nested_pdf_source_file_change_invalidates_index(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify changed default knowledge-base PDFs rebuild the index."""
        source_directory = create_source_directory(tmp_path)
        pdf_directory = source_directory / "career_sources" / "pdfs"
        pdf_directory.mkdir(parents=True)
        pdf_file = pdf_directory / "ai_skills_report.pdf"
        pdf_file.write_bytes(b"old pdf bytes")
        monkeypatch.setattr(retriever, "DEFAULT_MARKDOWN_DIR", str(source_directory))
        monkeypatch.setattr(retriever, "DEFAULT_PDF_DIR", str(source_directory))
        write_current_source_metadata(source_directory)
        pdf_file.write_bytes(b"updated pdf bytes")
        os.utime(pdf_file, ns=(3_000_000_000, 3_000_000_000))
        created_store = object()
        load_documents = Mock(return_value=[{"content": "updated", "source": str(pdf_file)}])
        split_documents = Mock(
            return_value=[
                {"content": "updated", "source": str(pdf_file), "chunk_index": 0}
            ]
        )
        vector_store_class = Mock()
        vector_store_class.from_documents = Mock(return_value=created_store)

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", Mock(return_value=object()))
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)
        monkeypatch.setattr(retriever.shutil, "rmtree", Mock())

        store = create_vector_store(str(source_directory))

        assert store is created_store
        load_documents.assert_called_once_with(str(source_directory))
        split_documents.assert_called_once()
        vector_store_class.from_documents.assert_called_once()

    def test_directory_change_does_not_rebuild_other_directory(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify source changes rebuild only the changed directory index."""
        directory_a = create_source_directory(tmp_path, "directory-a")
        directory_b = create_source_directory(tmp_path, "directory-b")
        write_current_source_metadata(directory_a)
        write_current_source_metadata(directory_b)
        (directory_a / "new.md").write_text("new content", encoding="utf-8")
        store_b = Mock()
        qdrant_client = qdrant_client_with_count(3)
        rebuilt_store_a = object()
        qdrant_client_class = Mock(return_value=qdrant_client)
        vector_store_class = Mock(return_value=store_b)
        vector_store_class.from_documents = Mock(return_value=rebuilt_store_a)
        load_documents = Mock(return_value=[{"content": "A", "source": "a.md"}])
        split_documents = Mock(
            return_value=[{"content": "A", "source": "a.md", "chunk_index": 0}]
        )
        rmtree = Mock()

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", Mock(return_value=object()))
        monkeypatch.setattr(retriever, "QdrantClient", qdrant_client_class)
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)
        monkeypatch.setattr(retriever.shutil, "rmtree", rmtree)

        b_store = create_vector_store(str(directory_b))
        a_store = create_vector_store(str(directory_a))

        assert b_store is store_b
        assert a_store is rebuilt_store_a
        rmtree.assert_called_once_with(
            retriever.Path(expected_persist_directory(directory_a)),
            ignore_errors=True,
        )
        load_documents.assert_called_once_with(str(directory_a))
        split_documents.assert_called_once()
        assert vector_store_class.call_count == 1
        vector_store_class.from_documents.assert_called_once()
        qdrant_client_class.assert_called_once_with(
            path=expected_persist_directory(directory_b),
        )

    def test_fingerprint_metadata_written_only_after_successful_index_creation(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify failed index creation does not write new fingerprint metadata."""
        source_directory = create_source_directory(tmp_path)
        load_documents = Mock(return_value=[{"content": "source", "source": "doc.md"}])
        split_documents = Mock(
            return_value=[
                {"content": "source", "source": "doc.md", "chunk_index": 0}
            ]
        )
        vector_store_class = Mock()
        vector_store_class.from_documents = Mock(side_effect=RuntimeError("build failed"))

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", Mock(return_value=object()))
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)

        with pytest.raises(RuntimeError, match="build failed"):
            create_vector_store(str(source_directory))

        assert not metadata_path(source_directory).exists()

        vector_store_class.from_documents.side_effect = None
        vector_store_class.from_documents.return_value = object()

        create_vector_store(str(source_directory))

        metadata = json.loads(metadata_path(source_directory).read_text("utf-8"))
        assert metadata["fingerprint"] == retriever._source_fingerprint(
            retriever._source_manifest(source_directory)
        )
        assert metadata["index_schema_version"] == retriever.INDEX_SCHEMA_VERSION

    def test_schema_version_change_invalidates_existing_index(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify code-only schema changes rebuild even if source files match."""
        source_directory = create_source_directory(tmp_path)
        effective_persist_directory = write_current_source_metadata(source_directory)
        metadata_file = retriever.Path(effective_persist_directory) / (
            retriever.SOURCE_METADATA_FILENAME
        )
        metadata = json.loads(metadata_file.read_text("utf-8"))
        metadata["index_schema_version"] = retriever.INDEX_SCHEMA_VERSION - 1
        metadata_file.write_text(json.dumps(metadata), encoding="utf-8")
        created_store = object()
        load_documents = Mock(return_value=[{"content": "source", "source": "doc.md"}])
        split_documents = Mock(
            return_value=[
                {"content": "source", "source": "doc.md", "chunk_index": 0}
            ]
        )
        vector_store_class = Mock()
        vector_store_class.from_documents = Mock(return_value=created_store)

        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", Mock(return_value=object()))
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)
        monkeypatch.setattr(retriever.shutil, "rmtree", Mock())

        store = create_vector_store(str(source_directory))

        assert store is created_store
        load_documents.assert_called_once_with(str(source_directory))
        split_documents.assert_called_once()
        vector_store_class.from_documents.assert_called_once()

    def test_provider_identity_change_invalidates_existing_index(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify OpenAI does not reuse an index built with OpenRouter embeddings."""
        source_directory = create_source_directory(tmp_path)
        write_current_source_metadata(source_directory)
        created_store = object()
        load_documents = Mock(return_value=[{"content": "source", "source": "doc.md"}])
        split_documents = Mock(
            return_value=[
                {"content": "source", "source": "doc.md", "chunk_index": 0}
            ]
        )
        vector_store_class = Mock()
        vector_store_class.from_documents = Mock(return_value=created_store)
        rmtree = Mock()

        monkeypatch.setenv("COGNIVIA_LLM_PROVIDER", "openai")
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", Mock(return_value=object()))
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)
        monkeypatch.setattr(retriever.shutil, "rmtree", rmtree)

        store = create_vector_store(str(source_directory))

        assert store is created_store
        rmtree.assert_called_once_with(
            retriever.Path(expected_persist_directory(source_directory)),
            ignore_errors=True,
        )
        load_documents.assert_called_once_with(str(source_directory))
        split_documents.assert_called_once()
        vector_store_class.from_documents.assert_called_once()

    def test_embedding_model_change_invalidates_existing_index(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify a model change rebuilds even when source files match."""
        source_directory = create_source_directory(tmp_path)
        write_current_source_metadata(source_directory)
        created_store = object()
        load_documents = Mock(return_value=[{"content": "source", "source": "doc.md"}])
        split_documents = Mock(
            return_value=[
                {"content": "source", "source": "doc.md", "chunk_index": 0}
            ]
        )
        vector_store_class = Mock()
        vector_store_class.from_documents = Mock(return_value=created_store)
        rmtree = Mock()

        monkeypatch.delenv("COGNIVIA_LLM_PROVIDER", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "EMBEDDING_MODEL", "text-embedding-3-large")
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", Mock(return_value=object()))
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)
        monkeypatch.setattr(retriever.shutil, "rmtree", rmtree)

        store = create_vector_store(str(source_directory))

        assert store is created_store
        rmtree.assert_called_once_with(
            retriever.Path(expected_persist_directory(source_directory)),
            ignore_errors=True,
        )
        load_documents.assert_called_once_with(str(source_directory))
        split_documents.assert_called_once()
        vector_store_class.from_documents.assert_called_once()

    def test_source_metadata_includes_embedding_identity(
        self,
        monkeypatch,
        tmp_path,
    ):
        """Verify persisted metadata records provider and model identity."""
        source_directory = create_source_directory(tmp_path)
        created_store = object()
        load_documents = Mock(return_value=[{"content": "source", "source": "doc.md"}])
        split_documents = Mock(
            return_value=[
                {"content": "source", "source": "doc.md", "chunk_index": 0}
            ]
        )
        vector_store_class = Mock()
        vector_store_class.from_documents = Mock(return_value=created_store)

        monkeypatch.delenv("COGNIVIA_LLM_PROVIDER", raising=False)
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-api-key")
        monkeypatch.setattr(retriever, "OpenAIEmbeddings", Mock(return_value=object()))
        monkeypatch.setattr(retriever, "QdrantVectorStore", vector_store_class)
        monkeypatch.setattr(retriever, "load_documents", load_documents)
        monkeypatch.setattr(retriever, "split_documents", split_documents)

        create_vector_store(str(source_directory))

        metadata = json.loads(metadata_path(source_directory).read_text("utf-8"))
        assert metadata["embedding_identity"] == {
            "base_url": "https://openrouter.ai/api/v1",
            "model": "text-embedding-3-small",
            "provider": "openrouter",
        }
        assert metadata["index_schema_version"] == retriever.INDEX_SCHEMA_VERSION

    def test_rebuild_vector_store_forces_rebuild(self, monkeypatch):
        """Verify the explicit rebuild helper delegates to force rebuild."""
        create_vector_store_mock = Mock(return_value=object())
        monkeypatch.setattr(
            retriever,
            "create_vector_store",
            create_vector_store_mock,
        )

        rebuild_vector_store(
            directory="test-directory",
            persist_directory="test-persist-directory",
        )

        create_vector_store_mock.assert_called_once_with(
            directory="test-directory",
            persist_directory="test-persist-directory",
            force_rebuild=True,
        )


class TestRetrieveRelevantChunks:
    """Tests for retrieve_relevant_chunks function."""

    def test_explicit_none_uses_vector_store_similarity_search(self, monkeypatch):
        """Verify explicit unfiltered retrieval delegates query and k."""
        fake_documents = [Mock(), Mock()]
        fake_vector_store = Mock()
        fake_vector_store.similarity_search.return_value = fake_documents
        create_vector_store_mock = Mock(return_value=fake_vector_store)

        monkeypatch.setattr(
            retriever,
            "create_vector_store",
            create_vector_store_mock,
        )

        results = retrieve_relevant_chunks(
            "AI learning",
            directory="test-dir",
            k=2,
            min_relevance_score=None,
        )

        assert results is fake_documents
        create_vector_store_mock.assert_called_once_with("test-dir")
        fake_vector_store.similarity_search.assert_called_once_with("AI learning", k=2)

    def test_default_relevance_score_gate_filters_weak_matches(
        self,
        monkeypatch,
    ):
        """Verify production retrieval defaults to relevance-score gating."""
        retained_document = Mock()
        fake_vector_store = Mock()
        fake_vector_store.similarity_search_with_relevance_scores.return_value = [
            (Mock(), 0.12),
            (retained_document, DEFAULT_MIN_RELEVANCE_SCORE),
        ]

        monkeypatch.setattr(
            retriever,
            "create_vector_store",
            Mock(return_value=fake_vector_store),
        )

        results = retrieve_relevant_chunks(
            "AI learning",
            directory="test-dir",
            k=2,
        )

        assert results == [retained_document]
        fake_vector_store.similarity_search_with_relevance_scores.assert_called_once_with(
            "AI learning",
            k=2,
            score_threshold=DEFAULT_MIN_RELEVANCE_SCORE,
        )
        fake_vector_store.similarity_search.assert_not_called()

    def test_optional_relevance_score_gate_filters_weak_matches(
        self,
        monkeypatch,
    ):
        """Verify opt-in retrieval gating drops low-relevance documents."""
        weak_document = Mock()
        retained_document = Mock()
        retained_document.metadata = {
            "source": "data/knowledge_base/derived/oecd_ai_skills_gap_2025.md",
            "source_type": "markdown",
        }
        fake_vector_store = Mock()
        fake_vector_store.similarity_search_with_relevance_scores.return_value = [
            (weak_document, 0.12),
            (retained_document, 0.82),
        ]
        create_vector_store_mock = Mock(return_value=fake_vector_store)

        monkeypatch.setattr(
            retriever,
            "create_vector_store",
            create_vector_store_mock,
        )

        results = retrieve_relevant_chunks(
            "AI learning",
            directory="test-dir",
            k=2,
            min_relevance_score=0.8,
        )

        assert results == [retained_document]
        assert results[0].metadata == retained_document.metadata
        create_vector_store_mock.assert_called_once_with("test-dir")
        fake_vector_store.similarity_search_with_relevance_scores.assert_called_once_with(
            "AI learning",
            k=2,
            score_threshold=0.8,
        )
        fake_vector_store.similarity_search.assert_not_called()

    def test_optional_relevance_score_gate_can_return_empty_list(
        self,
        monkeypatch,
    ):
        """Verify weak gated matches return no documents."""
        fake_vector_store = Mock()
        fake_vector_store.similarity_search_with_relevance_scores.return_value = [
            (Mock(), 0.15),
            (Mock(), 0.2),
        ]

        monkeypatch.setattr(
            retriever,
            "create_vector_store",
            Mock(return_value=fake_vector_store),
        )

        results = retrieve_relevant_chunks(
            "unrelated query",
            directory="test-dir",
            k=2,
            min_relevance_score=0.75,
        )

        assert results == []
        fake_vector_store.similarity_search_with_relevance_scores.assert_called_once_with(
            "unrelated query",
            k=2,
            score_threshold=0.75,
        )
        fake_vector_store.similarity_search.assert_not_called()

    def test_optional_relevance_score_gate_preserves_result_order(
        self,
        monkeypatch,
    ):
        """Verify score filtering does not reorder retained documents."""
        first_document = Mock()
        second_document = Mock()
        fake_vector_store = Mock()
        fake_vector_store.similarity_search_with_relevance_scores.return_value = [
            (first_document, 0.91),
            (Mock(), 0.2),
            (second_document, 0.88),
        ]

        monkeypatch.setattr(
            retriever,
            "create_vector_store",
            Mock(return_value=fake_vector_store),
        )

        results = retrieve_relevant_chunks(
            "AI learning",
            directory="test-dir",
            k=3,
            min_relevance_score=0.8,
        )

        assert results == [first_document, second_document]

    def test_optional_relevance_score_gate_falls_back_when_api_missing(
        self,
        monkeypatch,
    ):
        """Verify missing score API keeps existing top-k retrieval behavior."""
        fake_documents = [Mock(), Mock()]
        fake_vector_store = Mock(spec=["similarity_search"])
        fake_vector_store.similarity_search.return_value = fake_documents

        monkeypatch.setattr(
            retriever,
            "create_vector_store",
            Mock(return_value=fake_vector_store),
        )

        results = retrieve_relevant_chunks(
            "AI learning",
            directory="test-dir",
            k=2,
            min_relevance_score=0.8,
        )

        assert results is fake_documents
        fake_vector_store.similarity_search.assert_called_once_with("AI learning", k=2)
