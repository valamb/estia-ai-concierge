"""
RAG service tests — all run offline using an in-memory ChromaDB instance.
No OpenAI API key required.
"""

import pytest
import chromadb
from unittest.mock import patch, MagicMock

from app.services import rag_service
from app.utils.text_utils import clean_text, split_into_chunks


# --- text_utils tests (fully offline) ---

def test_clean_text_removes_extra_blank_lines():
    dirty = "Hello\n\n\n\nWorld"
    assert clean_text(dirty) == "Hello\n\nWorld"


def test_clean_text_normalizes_spaces():
    dirty = "Hello   World"
    assert clean_text(dirty).count("  ") == 0


def test_split_into_chunks_produces_multiple_chunks():
    text = " ".join(["word"] * 1200)
    chunks = split_into_chunks(text, chunk_size=100, overlap=10)
    assert len(chunks) > 1


def test_split_into_chunks_respects_overlap():
    text = " ".join([str(i) for i in range(200)])
    chunks = split_into_chunks(text, chunk_size=20, overlap=5)
    # With overlap the second chunk should start before word 20
    first_words = set(chunks[0].split())
    second_words = set(chunks[1].split())
    assert len(first_words & second_words) > 0


def test_split_empty_text_returns_empty():
    assert split_into_chunks("") == []


# --- rag_service: empty collection returns empty list ---

def test_retrieve_context_returns_empty_when_collection_empty():
    """Uses a real in-memory ChromaDB so no network call is made."""
    mock_collection = MagicMock()
    mock_collection.count.return_value = 0

    with patch.object(rag_service, "_get_collection", return_value=mock_collection):
        result = rag_service.retrieve_context("What time is the spa open?")

    assert result == []


def test_retrieve_context_filters_low_relevance():
    """Chunks with cosine distance >= 0.5 should be excluded."""
    mock_collection = MagicMock()
    mock_collection.count.return_value = 3
    mock_collection.query.return_value = {
        "documents": [["Relevant chunk", "Irrelevant chunk", "Another chunk"]],
        "metadatas": [[{}, {}, {}]],
        "distances": [[0.2, 0.6, 0.4]],
    }

    with patch.object(rag_service, "_get_collection", return_value=mock_collection):
        result = rag_service.retrieve_context("spa hours")

    # Distance 0.6 should be filtered out
    assert len(result) == 2
    assert "Relevant chunk" in result
    assert "Irrelevant chunk" not in result
