"""
Knowledge Base Ingestion Script
================================
Reads all Markdown documents from the knowledge/ folder, splits them into
chunks, embeds them via OpenAI, and stores them in ChromaDB.

Usage:
    python -m app.scripts.ingest_knowledge

Options:
    --reset     Drop and recreate the ChromaDB collection before ingesting.
                Use this when you want a clean slate after major content changes.

Example:
    python -m app.scripts.ingest_knowledge
    python -m app.scripts.ingest_knowledge --reset
"""

import argparse
import hashlib
import sys
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions
from langchain.text_splitter import RecursiveCharacterTextSplitter
from loguru import logger

# Allow running as a module from the project root
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from app.core.config import settings
from app.core.logging import setup_logging
from app.utils.text_utils import clean_text
from app.services.language_service import extract_language_from_filename


SUPPORTED_EXTENSIONS = {".md", ".txt"}


def _extract_metadata_from_path(file_path: Path, knowledge_root: Path) -> dict:
    """
    Derive metadata from the document's folder position.

    knowledge/spa/spa_overview.md  →  category=spa, property=all
    knowledge/properties/porto_elounda/overview.md  →  category=property, property=porto_elounda
    """
    relative = file_path.relative_to(knowledge_root)
    parts = relative.parts

    category = parts[0] if len(parts) > 0 else "general"
    property_id = parts[1] if category == "properties" and len(parts) > 2 else "all"
    language = extract_language_from_filename(file_path.name)

    return {
        "source": str(relative).replace("\\", "/"),
        "category": category,
        "property": property_id,
        "language": language,
        "filename": file_path.name,
    }


def _document_id(source: str, chunk_index: int) -> str:
    """Stable, unique ID for a chunk so re-ingestion is idempotent."""
    raw = f"{source}::{chunk_index}"
    return hashlib.md5(raw.encode()).hexdigest()


def ingest(reset: bool = False) -> None:
    setup_logging()

    knowledge_root = Path(settings.knowledge_base_path)
    if not knowledge_root.exists():
        logger.error(f"Knowledge base path not found: {knowledge_root}")
        sys.exit(1)

    # --- ChromaDB setup ---
    client = chromadb.PersistentClient(path=settings.chroma_db_path)
    openai_ef = embedding_functions.OpenAIEmbeddingFunction(
        api_key=settings.openai_api_key,
        model_name=settings.openai_embedding_model,
    )

    if reset:
        logger.warning(
            f"--reset flag: deleting collection '{settings.chroma_collection_name}'"
        )
        try:
            client.delete_collection(settings.chroma_collection_name)
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=settings.chroma_collection_name,
        embedding_function=openai_ef,
        metadata={"hnsw:space": "cosine"},
    )

    # --- Text splitter ---
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.rag_chunk_size,
        chunk_overlap=settings.rag_chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    # --- Discover files ---
    files = [
        f
        for f in knowledge_root.rglob("*")
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS
    ]

    if not files:
        logger.warning(f"No documents found under {knowledge_root}")
        return

    logger.info(f"Found {len(files)} document(s) to ingest")

    total_chunks = 0
    total_files = 0

    for file_path in files:
        try:
            raw_text = file_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            continue

        text = clean_text(raw_text)
        if not text:
            logger.warning(f"Skipping empty file: {file_path}")
            continue

        chunks = splitter.split_text(text)
        if not chunks:
            continue

        metadata = _extract_metadata_from_path(file_path, knowledge_root)
        relative_source = metadata["source"]

        ids = [_document_id(relative_source, i) for i in range(len(chunks))]
        metadatas = [{**metadata, "chunk_index": i} for i in range(len(chunks))]

        # Upsert so re-running is safe (no duplicate embeddings)
        collection.upsert(
            ids=ids,
            documents=chunks,
            metadatas=metadatas,
        )

        logger.info(f"  Ingested {len(chunks):>3} chunk(s) ← {relative_source}")
        total_chunks += len(chunks)
        total_files += 1

    logger.info(
        f"\nIngestion complete: {total_files} file(s), "
        f"{total_chunks} chunk(s) → collection '{settings.chroma_collection_name}' "
        f"(total indexed: {collection.count()})"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest knowledge base into ChromaDB")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete and recreate the collection before ingesting",
    )
    args = parser.parse_args()
    ingest(reset=args.reset)
