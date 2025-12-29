"""Sentence embedder using HuggingFace sentence-transformers."""

import numpy as np
from numpy import ndarray
from sentence_transformers import SentenceTransformer

from core import get_logger

logger = get_logger(__name__)


class SentenceEmbedder:
    """
    Embedder using sentence-transformers for semantic similarity.

    Uses all-MiniLM-L6-v2 by default - a lightweight but effective model
    that produces 384-dimensional embeddings optimized for semantic similarity.
    """

    _instance: "SentenceEmbedder | None" = None

    def __init__(
        self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ) -> None:
        """Initialize the embedder (called only once due to singleton)."""
        self._model_name = model_name
        self._model: SentenceTransformer | None = None
        self._initialized = False

    def __new__(
        cls, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    ) -> "SentenceEmbedder":
        """Singleton pattern to avoid loading the model multiple times."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _ensure_initialized(self) -> None:
        """Lazy initialization of the model."""
        if not self._initialized:
            logger.info(
                "Loading sentence embedding model",
                extra={"model_name": self._model_name},
            )
            self._model = SentenceTransformer(self._model_name)
            self._initialized = True
            logger.info("Sentence embedding model loaded successfully")

    def embed(self, text: str) -> ndarray:
        """
        Embed a single text string.

        Args:
            text: The text to embed.

        Returns:
            Normalized embedding vector as numpy array.
        """
        self._ensure_initialized()
        if self._model is None:
            raise RuntimeError("Model not initialized")

        # Handle empty or whitespace-only text
        if not text or not text.strip():
            text = " "

        embedding: ndarray = self._model.encode(
            text,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        return embedding

    def embed_batch(self, texts: list[str]) -> ndarray:
        """
        Embed multiple texts in a batch for efficiency.

        Args:
            texts: List of texts to embed.

        Returns:
            2D numpy array of normalized embeddings.
        """
        self._ensure_initialized()
        if self._model is None:
            raise RuntimeError("Model not initialized")

        # Handle empty texts
        processed_texts = [t if t and t.strip() else " " for t in texts]

        embeddings: ndarray = self._model.encode(
            processed_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            batch_size=32,
        )
        return embeddings

    @property
    def embedding_dimension(self) -> int:
        """Return the dimension of the embeddings."""
        self._ensure_initialized()
        if self._model is None:
            raise RuntimeError("Model not initialized")
        return self._model.get_sentence_embedding_dimension() or 384


# Global singleton instance
embedder = SentenceEmbedder()
