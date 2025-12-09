from typing import Callable

import numpy as np
from numpy import ndarray

from core import get_logger

logger = get_logger(__name__)


class VectorDB:
    """
    Simple in-memory vector database for storing and querying embeddings for the tools tags.
    """

    def __init__(self, embedding_function: Callable) -> None:
        """Initialize the VectorDB with an embedding function.
        Args:
            embedding_function (Callable): A function that takes a string and returns its embedding as a numpy array.
        """
        logger.debug("Initializing VectorDB")
        self.embedding_function = embedding_function
        self.entries: list[dict] = []

    def add(self, description: str, metadata: dict) -> None:
        embedding = self._embed_text(description)
        self.entries.append({"vector": embedding, "metadata": metadata})

    def query(self, vector: ndarray, top_k: int = 5) -> list[dict]:
        """Query the vector database for the top_k closest embeddings to the given vector using cosine similarity.
        Args:
            vector (np.ndarray): The query vector.
            top_k (int): The number of closest embeddings to return.
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

    def text_query(self, text: str, top_k: int = 5) -> list[dict]:
        """Embed the given text and query the vector database.
        Args:
            text (str): The query text.
            top_k (int): The number of closest embeddings to return.
        Returns:
            List of metadata of the top_k closest embeddings.
        """
        query_vector = self._embed_text(text)
        return self.query(query_vector, top_k=top_k)

    def _embed_text(self, text: str) -> np.ndarray:
        """Embed a given text using the embedding function.
        Args:
            text (str): The text to embed.
        Returns:
            np.ndarray: The embedding vector.
        """
        # Handle list input if passed accidentally
        if isinstance(text, list):
            text = text[0] if text else ""

        response = self.embedding_function(contents=text)

        if hasattr(response, "embeddings") and response.embeddings:
            embedding_values = response.embeddings[0].values
        elif hasattr(response, "embedding") and response.embedding:
            embedding_values = response.embedding.values
        emb_vector = np.array(embedding_values)
        norm = np.linalg.norm(emb_vector)
        if norm > 0:
            return emb_vector / norm
        return emb_vector
