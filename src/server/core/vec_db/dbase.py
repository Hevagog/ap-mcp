from typing import Any

import numpy as np
from numpy import ndarray

from core import get_logger
from core.embedder import SentenceEmbedder

logger = get_logger(__name__)


class VectorDB:
    """
    Simple in-memory vector database for storing and querying embeddings for the tools tags.
    """

    def __init__(self, embedder: SentenceEmbedder | None = None) -> None:
        """Initialize the VectorDB with an embedder.

        Args:
            embedder: A SentenceEmbedder instance. If None, uses the global singleton.
        """
        logger.debug("Initializing VectorDB")
        self._embedder = embedder or SentenceEmbedder()
        self.entries: list[dict[str, Any]] = []

    def add(self, description: str, metadata: dict[str, Any]) -> None:
        """Add a new entry to the database.

        Args:
            description: The text description to embed.
            metadata: Associated metadata for this entry.
        """
        embedding = self._embed_text(description)
        self.entries.append({"vector": embedding, "metadata": metadata})

    def query(self, vector: ndarray, top_k: int = 5) -> list[dict[str, Any]]:
        """Query the vector database for the top_k closest embeddings to the given vector using cosine similarity.

        Args:
            vector: The query vector.
            top_k: The number of closest embeddings to return.

        Returns:
            List of metadata of the top_k closest embeddings.
        """
        if not self.entries:
            return []
        embeddings_matrix = np.vstack([entry["vector"] for entry in self.entries])
        norms = np.linalg.norm(embeddings_matrix, axis=1) * np.linalg.norm(vector)
        norms[norms == 0] = 1e-10  # Prevents division by zero
        similarities = embeddings_matrix @ vector / norms
        top_k_indices = np.argsort(similarities)[-top_k:][::-1]
        return [self.entries[i]["metadata"] for i in top_k_indices]

    def text_query(self, text: str, top_k: int = 5) -> list[dict[str, Any]]:
        """Embed the given text and query the vector database.

        Args:
            text: The query text.
            top_k: The number of closest embeddings to return.

        Returns:
            List of metadata of the top_k closest embeddings.
        """
        query_vector = self._embed_text(text)
        return self.query(query_vector, top_k=top_k)

    def _embed_text(self, text: str) -> ndarray:
        """Embed a given text using the embedder.

        Args:
            text: The text to embed.

        Returns:
            The embedding vector (already normalized by sentence-transformers).
        """
        # Handle list input if passed accidentally
        if isinstance(text, list):
            text = text[0] if text else ""

        return self._embedder.embed(text)
