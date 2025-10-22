import numpy as np
from typing import Callable
from core.logging import get_logger

logger = get_logger(__name__)


class VectorDB:
    """
    Simple in-memory vector database for storing and querying embeddings for the tools tags.
    """

    def __init__(self, embedding_function: Callable):
        """Initialize the VectorDB with an embedding function.
        Args:
            embedding_function (Callable): A function that takes a string and returns its embedding as a numpy array.
        """
        logger.debug("Initializing VectorDB")
        self.embedding_function = embedding_function
        self.embeddings = (
            []
        )  # Since we won't have that many tools, a simple list will do for this project

    def add(self, tags: list[str]):
        tag_embeddings = self.embedding_function(contents=tags).embeddings
        tag_embeddings = np.array([np.array(emb.values) for emb in tag_embeddings])
        emb = np.mean(tag_embeddings, axis=0)
        self.embeddings.append(emb / np.linalg.norm(emb))

    def query(self, vector, top_k=5):
        """Query the vector database for the top_k closest embeddings to the given vector using cosine similarity.
        Args:
            vector (np.ndarray): The query vector.
            top_k (int): The number of closest embeddings to return.
        Returns:
            List of indices of the top_k closest embeddings.
        """
        if not self.embeddings:
            return []
        embeddings_matrix = np.vstack(self.embeddings)
        norms = np.linalg.norm(embeddings_matrix, axis=1) * np.linalg.norm(vector)
        similarities = embeddings_matrix @ vector / norms
        top_k_indices = np.argsort(similarities)[-top_k:][::-1]
        return top_k_indices
