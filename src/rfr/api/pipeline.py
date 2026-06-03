"""LCEL RAG pipeline — ring-fenced retrieval + generation.

Implements the core RAG flow:
1. Secure retrieval with role-based metadata filtering
2. Context formatting with source citations
3. Prompt assembly (system + context + question)
4. LLM generation via configurable provider
5. Token-count-aware context truncation

This module uses ONLY LangChain Expression Language (LCEL).
No legacy RetrievalQA or ConversationalRetrievalChain wrappers.
"""

from __future__ import annotations

import logging
import time
from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from langchain_openai import ChatOpenAI

from rfr.api.schemas import QueryResponse, SourceInfo, TokenUsage

logger = logging.getLogger(__name__)


class RAGExecutionError(Exception):
    """Raised when the RAG pipeline encounters a fatal error."""


def create_secure_retriever(
    user_role: str,
    top_k: int = 3,
    vector_store: Any | None = None,  # type: ignore[explicit-any]
) -> Any:  # type: ignore[explicit-any]
    """Create a secure retriever that filters by user role.

    The ring-fence is enforced here: the vector store's metadata filter
    ensures only documents whose 'allowed_roles' includes the user's role
    are returned. This is a database-level filter, not an application-level one.

    Args:
        user_role: The role to filter by.
        top_k: Number of documents to retrieve.
        vector_store: A LangChain VectorStore instance. If None, uses a mock.

    Returns:
        A callable that takes a query string and returns list of Documents.

    """
    if vector_store is None:
        # Return a mock retriever for standalone/dev mode
        return _create_mock_retriever(user_role, top_k)

    return vector_store.as_retriever(
        search_kwargs={
            "k": top_k,
            "filter": {"allowed_roles": {"$in": [user_role]}},
        },
    )


def _create_mock_retriever(user_role: str, top_k: int = 3) -> Any:  # type: ignore[explicit-any]
    """Create a mock retriever for development/testing without a DB."""

    def retrieve(query: str) -> list[dict[str, Any]]:
        logger.info("Mock retriever: role=%s query=%s", user_role, query[:50])
        # Return a single mock result to demonstrate the pipeline
        if user_role == "none":
            return []
        return [
            {
                "content": (
                    "To restart the primary Nginx reverse proxy, execute: "
                    "systemctl restart nginx. Ensure you are on the management VPN."
                ),
                "metadata": {
                    "source": "confluence/nginx_guide",
                    "doc_id": "NG-001",
                    "title": "Nginx Restart Procedure",
                    "allowed_roles": ["admin", "senior_engineer"],
                },
            },
        ]

    return retrieve


def format_docs(docs: list[Any]) -> str:  # type: ignore[explicit-any]
    """Format retrieved documents into a single context string with source citations.

    Args:
        docs: List of Documents (or dicts with 'content' and 'metadata').

    Returns:
        Formatted string with source citations.

    """
    if not docs:
        return "No relevant documentation found for this query."

    parts = []
    for i, doc in enumerate(docs):
        if isinstance(doc, dict):
            content = doc.get("content", "")
            source = doc.get("metadata", {}).get("source", "Unknown")
        else:
            content = getattr(doc, "page_content", str(doc))
            source = (
                doc.metadata.get("source", "Unknown") if hasattr(doc, "metadata") else "Unknown"
            )

        parts.append(f"[Source {i + 1}: {source}]\n{content}")

    return "\n\n".join(parts)


def create_rag_chain(
    user_role: str,
    llm: ChatOpenAI | None = None,
    vector_store: Any | None = None,  # type: ignore[explicit-any]
    top_k: int = 3,
    max_context_tokens: int = 6000,
) -> Any:  # type: ignore[explicit-any]
    """Create the LCEL RAG chain with ring-fenced retrieval.

    Args:
        user_role: The user's role for document filtering.
        llm: LangChain chat model instance. If None, uses a mock.
        vector_store: Vector store for retrieval. If None, uses a mock.
        top_k: Number of documents to retrieve.
        max_context_tokens: Maximum tokens allowed in the context before truncation.

    Returns:
        A callable LCEL chain that takes a query string and returns a QueryResponse.

    """
    # 1. Create the secure retriever
    retriever = create_secure_retriever(user_role, top_k, vector_store)

    # 2. Build the extraction + format step
    def retrieve_and_format(query: str) -> dict[str, str]:
        """Execute retrieval and format context."""
        try:
            raw_docs = retriever(query) if callable(retriever) else retriever.invoke(query)

            # Normalize to list of dicts
            normalized = _normalize_docs(raw_docs) if raw_docs else []

            context = format_docs(normalized)
            return {"context": context, "question": query, "raw_docs": normalized}

        except Exception as e:
            logger.exception("Retrieval failed")
            raise RAGExecutionError(f"Document retrieval failed: {e}") from e

    # 3. The LLM is used if provided; otherwise the chain uses a mock generator
    # (No ChatOpenAI creation here — the build_response closure handles this)

    # 4. Define the prompt template
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an internal documentation assistant. Answer the user's question "
                "using ONLY the provided context. If the context does not contain the answer, "
                "explicitly state 'I do not know'. Do not guess or use outside knowledge.\n\n"
                "Context:\n{context}",
            ),
            ("human", "{question}"),
        ]
    )

    # 5. Build the chain
    def build_response(inputs: dict[str, Any]) -> QueryResponse:
        """Execute the full RAG chain and build the response."""
        start = time.time()
        try:
            context = inputs["context"]
            question = inputs["question"]
            raw_docs = inputs.get("raw_docs", [])

            # Truncate context if needed (simple char-based estimate)
            if len(context) > max_context_tokens * 4:
                context = context[: max_context_tokens * 4]
                context = context[: context.rfind("\n\n")]
                logger.warning("Context truncated to ~%d tokens", max_context_tokens)

            # Generate answer via LLM or mock
            if llm is None:
                answer = _generate_mock_answer(context, question)
            else:
                chain = (
                    {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
                    | prompt
                    | llm
                    | StrOutputParser()
                )
                answer = chain.invoke({"context": context, "question": question})

            # Build source list
            sources = []
            for doc in raw_docs:
                sources.append(
                    SourceInfo(
                        content=doc.get("content", "")[:500],
                        metadata=doc.get("metadata", {}),
                        relevance_score=doc.get("distance", doc.get("relevance_score", 0.0)),
                    )
                )

            latency = (time.time() - start) * 1000

            return QueryResponse(
                answer=answer,
                sources=sources,
                token_usage=TokenUsage(
                    prompt_tokens=len(context) // 4,
                    completion_tokens=len(answer) // 4,
                    total_tokens=(len(context) + len(answer)) // 4,
                ),
                latency_ms=round(latency, 1),
            )

        except RAGExecutionError:
            raise
        except Exception as e:
            logger.exception("RAG pipeline failed")
            raise RAGExecutionError(
                "The documentation retrieval system encountered a failure. "
                "Please try again or contact IT operations."
            ) from e

    # Wrap into a single callable
    return RunnableLambda(retrieve_and_format) | RunnableLambda(build_response)


def _normalize_docs(docs: list[Any]) -> list[dict[str, Any]]:  # type: ignore[explicit-any]
    """Normalize various document formats into a list of dicts."""
    result = []
    for doc in docs:
        if isinstance(doc, dict):
            result.append(doc)
        elif hasattr(doc, "page_content"):
            result.append(
                {
                    "content": doc.page_content,
                    "metadata": doc.metadata if hasattr(doc, "metadata") else {},
                    "distance": getattr(doc, "distance", 0.0),
                }
            )
        else:
            result.append({"content": str(doc), "metadata": {}})
    return result


def _generate_mock_answer(context: str, question: str) -> str:
    """Generate a mock answer for testing without an LLM.

    Args:
        context: The retrieved context string.
        question: The user's question.

    Returns:
        A simulated answer based on the context.

    """
    if "No relevant" in context:
        return "I could not find any relevant documentation for your query."
    # Extract a reasonable answer from the context
    lines = [l for l in context.split("\n") if l.strip() and not l.strip().startswith("[Source")]
    if lines:
        return lines[0][:200]
    return "Based on the provided documentation, here is what I found."


def execute_rag_query(
    query: str,
    user_role: str,
    llm: ChatOpenAI | None = None,
    vector_store: Any | None = None,  # type: ignore[explicit-any]
    top_k: int = 3,
) -> QueryResponse:
    """Execute a single RAG query end-to-end.

    Convenience wrapper that creates the chain, invokes it, and returns the response.

    Args:
        query: The user's question.
        user_role: The user's role for document filtering.
        llm: LangChain chat model (uses config default if None).
        vector_store: Vector store (uses mock if None).
        top_k: Number of documents to retrieve.

    Returns:
        QueryResponse with answer and sources.

    Raises:
        RAGExecutionError: If the pipeline fails at any step.

    """
    chain = create_rag_chain(user_role, llm, vector_store, top_k)
    try:
        result = chain.invoke(query)
        if isinstance(result, QueryResponse):
            return result
        # If the chain returned something else, wrap it
        return QueryResponse(answer=str(result))
    except Exception as e:
        raise RAGExecutionError(str(e)) from e
