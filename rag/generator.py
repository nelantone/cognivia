"""RAG answer generation utilities."""

from langchain_openai import ChatOpenAI

from rag.config import DEFAULT_MIN_RELEVANCE_SCORE
from rag.retriever import retrieve_relevant_chunks

# Import DEFAULT_MODEL from openrouter_client for model selection
from openrouter_client import DEFAULT_MODEL
from tools.provider_config import get_provider_config, provider_api_key, provider_base_url


RAG_SYSTEM_PROMPT = """
You are AI Skill Compass, a learning and career coach for AI learners and developers.

Answer using only the retrieved context provided by the app.
If the context is weak or incomplete, say so clearly.
Do not pretend to know something that is not supported by the context.
Do not suggest live fetching, browsing external URLs, or retrieving new content.
If the local knowledge base does not cover the topic, say it would need to be expanded.
Give practical, concise advice.

Keep the answer concise and structured.
Prefer 3–5 bullet points.
Avoid long generic study plans unless the user asks for detail.
"""


def format_retrieved_context(documents):
    """Format retrieved documents into a context block for the LLM."""
    if not documents:
        return "No relevant context was retrieved."

    context_blocks = []

    for index, document in enumerate(documents, start=1):
        source = document.metadata.get("source", "unknown")
        chunk_index = document.metadata.get("chunk_index", "unknown")

        context_blocks.append(
            f"[Source {index}: {source}, chunk {chunk_index}]\n{document.page_content}"
        )

    return "\n\n".join(context_blocks)


def build_rag_prompt(question, retrieved_context):
    """Build the user prompt for a grounded RAG answer."""
    return f"""
User question:
{question}

Retrieved context:
{retrieved_context}

Instructions:
- Answer the user question using only the retrieved context.
- Do not suggest live fetching, browsing external URLs, or retrieving new content.
- If the knowledge base does not cover the topic, say it would need to be expanded.
- Mention when the context is limited.
- Keep the answer concise and structured.
- Prefer 3–5 bullet points.
- Avoid generic long lists unless the user asks for detail.
- End with one concrete next step.
"""


def _missing_evidence_answer():
    return (
        "I could not find relevant local evidence for that question. "
        "The knowledge base may need a more specific query or additional sources."
    )


def answer_with_rag(
    question,
    directory="data/knowledge_base",
    k=3,
    min_relevance_score=DEFAULT_MIN_RELEVANCE_SCORE,
):
    """Generate a grounded answer using retrieved context.

    Uses the selected provider through langchain_openai.ChatOpenAI.
    """
    # Retrieve relevant documents
    documents = retrieve_relevant_chunks(
        question,
        directory=directory,
        k=k,
        min_relevance_score=min_relevance_score,
    )
    retrieved_context = format_retrieved_context(documents)

    if not documents:
        return {
            "answer": _missing_evidence_answer(),
            "sources": [],
            "retrieved_context": retrieved_context,
        }

    user_prompt = build_rag_prompt(question, retrieved_context)

    # Use ChatOpenAI for OpenRouter-compatible chat completion.
    provider_config = get_provider_config()
    api_key = provider_api_key(provider_config)
    if api_key and provider_config.error is None:
        model_kwargs = {
            "model": DEFAULT_MODEL.removeprefix("openai/"),
            "api_key": api_key,
            "temperature": 0.7,
        }
        if provider_base_url(provider_config):
            model_kwargs["base_url"] = provider_base_url(provider_config)
        chat_model = ChatOpenAI(
            **model_kwargs,
        )
        messages = [
            {"role": "system", "content": RAG_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]
        response = chat_model.invoke(messages)
        answer = response.content if hasattr(response, "content") else str(response)
    else:
        answer = (
            "AI skill configuration is missing. Please check your environment settings."
        )

    sources = [
        {
            "source": document.metadata.get("source", "unknown"),
            "chunk_index": document.metadata.get("chunk_index", "unknown"),
            "preview": document.page_content[:200],
        }
        for document in documents
    ]

    return {
        "answer": answer,
        "sources": sources,
        "retrieved_context": retrieved_context,
    }
