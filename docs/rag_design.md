# ESTIA — RAG Design

## What is RAG?

**Retrieval-Augmented Generation (RAG)** is a technique that improves AI responses by first retrieving relevant documents from a knowledge base, then providing those documents as context to the language model before it generates an answer.

Without RAG, the AI relies only on its training data. With RAG, it can answer questions about **specific, real hotel information** it was never trained on.

---

## RAG Pipeline

```
Step 1 — INGESTION (runs once, or when knowledge changes)
─────────────────────────────────────────────────────────
knowledge/ documents
     │
     ▼
Document Loader (LangChain)
     │
     ▼
Text Splitter → chunks of ~500 tokens
     │
     ▼
OpenAI Embeddings (text-embedding-3-small)
     │
     ▼
ChromaDB Vector Store (saved to chroma_db/)


Step 2 — RETRIEVAL (runs on every guest question)
─────────────────────────────────────────────────
Guest question: "What are the spa opening hours?"
     │
     ▼
OpenAI Embeddings → question vector
     │
     ▼
ChromaDB similarity search → top 5 relevant chunks
     │
     ▼
Context documents passed to GPT-4o prompt


Step 3 — GENERATION
────────────────────
System prompt + retrieved context + guest question
     │
     ▼
GPT-4o → answer grounded in hotel knowledge
```

---

## Chunking Strategy

| Parameter | Value | Reason |
|---|---|---|
| Chunk size | 500 tokens | Fits one topic clearly without being too long |
| Overlap | 50 tokens | Prevents losing context at chunk boundaries |
| Splitter | RecursiveCharacterTextSplitter | Respects paragraph structure |

---

## Metadata per Chunk

Each chunk stored in ChromaDB carries:
```json
{
  "source": "knowledge/spa/elounda_peninsula_spa.md",
  "property": "elounda_peninsula",
  "category": "spa",
  "language": "en"
}
```

This allows filtered retrieval (e.g., only fetch spa documents for the Peninsula property).

---

## Collection Design

One ChromaDB collection: `estia_knowledge`

All properties and categories share the same collection. Filtering by metadata is used to scope queries to the relevant property when needed.

---

## Future Improvements

- Per-language collections (`estia_knowledge_en`, `estia_knowledge_el`)
- Hybrid search (keyword + semantic)
- Re-ranking retrieved chunks before passing to GPT-4o
