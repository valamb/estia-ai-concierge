import chromadb
from chromadb.utils import embedding_functions
from loguru import logger

from app.core.config import settings
from app.services.retrieval_context import INTENT_TO_CATEGORY

_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None


def _get_collection() -> chromadb.Collection:
    """Lazily initialise ChromaDB client and collection."""
    global _client, _collection

    if _collection is not None:
        return _collection

    logger.info(f"Initialising ChromaDB at '{settings.chroma_db_path}'")

    _client = chromadb.PersistentClient(path=settings.chroma_db_path)

    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=settings.openai_api_key,
        model_name=settings.openai_embedding_model,
    )

    _collection = _client.get_or_create_collection(
        name=settings.chroma_collection_name,
        embedding_function=openai_ef,
        metadata={"hnsw:space": "cosine"},
    )

    logger.info(
        f"ChromaDB collection '{settings.chroma_collection_name}' ready — "
        f"{_collection.count()} documents indexed"
    )

    return _collection


def retrieve_context(
    query: str,
    property_id: str | None = None,
    language: str | None = None,
    top_k: int | None = None,
    intent: str | None = None,
) -> list[str]:
    """
    Query ChromaDB for the most relevant knowledge chunks.

    Args:
        query:       The (optionally enriched) search query.
        property_id: Optional property slug to narrow results (e.g. 'porto_elounda').
        language:    Optional language code ('en' or 'el') to prefer matching docs.
        top_k:       Number of chunks to return. Defaults to settings.rag_top_k.
        intent:      Optional detected intent (e.g. 'restaurant', 'spa').
                     When provided a category filter is applied; if that returns
                     zero chunks the query is retried without the filter.

    Returns:
        List of relevant document text chunks, ordered by relevance.
    """
    k = top_k or settings.rag_top_k
    collection = _get_collection()

    if collection.count() == 0:
        logger.warning(
            "ChromaDB collection is empty. "
            "Run: python -m app.scripts.ingest_knowledge"
        )
        return []

    category = INTENT_TO_CATEGORY.get(intent) if intent else None

    result = _query(collection, query, k, property_id, language, category)
    if not result and category:
        logger.debug(
            f"RAG category filter '{category}' returned 0 chunks — retrying without filter"
        )
        result = _query(collection, query, k, property_id, language, category=None)

    logger.debug(
        f"RAG retrieved {len(result)}/{k} chunks for query='{query[:60]}...'"
    )
    return result


def _query(
    collection: chromadb.Collection,
    query: str,
    k: int,
    property_id: str | None,
    language: str | None,
    category: str | None,
) -> list[str]:
    """Execute a single ChromaDB query and return filtered document chunks."""
    conditions: list[dict] = []
    if property_id:
        conditions.append({"property": {"$in": [property_id, "all"]}})
    if language:
        conditions.append({"language": language})
    if category:
        conditions.append({"category": category})

    where_filter: dict | None = None
    if len(conditions) == 1:
        where_filter = conditions[0]
    elif len(conditions) > 1:
        where_filter = {"$and": conditions}

    try:
        results = collection.query(
            query_texts=[query],
            n_results=min(k, collection.count()),
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
    except Exception as e:
        logger.error(f"ChromaDB query failed: {e}")
        return []

    documents = results.get("documents", [[]])[0]
    distances = results.get("distances", [[]])[0]

    # Filter out low-relevance results (cosine distance > 0.5 means weak match)
    return [
        doc
        for doc, dist in zip(documents, distances)
        if dist < 0.5 and doc
    ]


def collection_count() -> int:
    """Return the number of documents currently indexed."""
    try:
        return _get_collection().count()
    except Exception:
        return 0
