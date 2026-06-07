import chromadb
from chromadb.utils import embedding_functions

from config import CHROMA_COLLECTION, CHROMA_PATH, EMBEDDING_MODEL, N_RESULTS

_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
    model_name=EMBEDDING_MODEL
)
_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_or_create_collection(
    name=CHROMA_COLLECTION,
    embedding_function=_ef,
    metadata={"hnsw:space": "cosine"},
)


def get_collection():
    """Return the ChromaDB collection. Used by app.py during ingestion."""
    return _collection


def embed_and_store(chunks):
    """
    Embed a list of chunk dicts and persist them in ChromaDB.

    Stores alongside each embedding:
      - documents : raw chunk text (used for retrieval + display)
      - metadatas : professor name and source label for attribution
      - ids       : unique chunk_id strings
    """
    _collection.add(
        documents=[c["text"] for c in chunks],
        metadatas=[{"professor": c["professor"], "source": c["source"]} for c in chunks],
        ids=[c["chunk_id"] for c in chunks],
    )
    print(f"Stored {_collection.count()} total chunks in the vector store.")


def retrieve(query, n_results=N_RESULTS):
    """
    Semantic search: return the top-n chunks most similar to query.

    Returns a list of dicts with keys: "text", "professor", "source", "distance".
    Returns [] if the collection is empty.
    """
    if _collection.count() == 0:
        return []

    results = _collection.query(
        query_texts=[query],
        n_results=n_results,
        include=["documents", "metadatas", "distances"],
    )

    return [
        {
            "text": doc,
            "professor": meta["professor"],
            "source": meta["source"],
            "distance": dist,
        }
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        )
    ]
