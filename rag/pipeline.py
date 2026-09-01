"""Basic RAG preparation pipeline."""

from rag.loader import load_documents
from rag.splitter import split_documents


def prepare_knowledge_base(directory="data/knowledge_base"):
    """Load and split knowledge base documents into chunks."""
    documents = load_documents(directory)
    return split_documents(documents)
