from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from core.embedder.sentence_embedder import SentenceEmbedder


class TestSentenceEmbedder:
    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        # Reset the singleton before each test
        SentenceEmbedder._instance = None
        yield
        SentenceEmbedder._instance = None

    @patch("core.embedder.sentence_embedder.SentenceTransformer")
    def test_singleton_behavior(self, mock_transformer: MagicMock) -> None:
        emb1 = SentenceEmbedder()
        emb2 = SentenceEmbedder()
        assert emb1 is emb2
        # Initialization happens lazily, so not initialized yet
        assert not emb1._initialized

        # Trigger initialization
        emb1._ensure_initialized()
        mock_transformer.assert_called_once()

        # Second init call shouldn't trigger reload
        emb2._ensure_initialized()
        mock_transformer.assert_called_once()

    @patch("core.embedder.sentence_embedder.SentenceTransformer")
    def test_embed(self, mock_transformer: MagicMock) -> None:
        # Arrange
        mock_model = MagicMock()
        mock_model.encode.return_value = np.array([0.1, 0.2, 0.3])
        mock_transformer.return_value = mock_model

        embedder = SentenceEmbedder()

        # Act
        result = embedder.embed("test text")

        # Assert
        assert np.array_equal(result, np.array([0.1, 0.2, 0.3]))
        mock_model.encode.assert_called_with(
            "test text",
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

    @patch("core.embedder.sentence_embedder.SentenceTransformer")
    def test_embed_empty_string(self, mock_transformer: MagicMock) -> None:
        # Arrange
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model

        embedder = SentenceEmbedder()

        # Act
        embedder.embed("   ")

        # Assert
        mock_model.encode.assert_called_with(
            " ",
            convert_to_numpy=True,
            normalize_embeddings=True,
        )

    @patch("core.embedder.sentence_embedder.SentenceTransformer")
    def test_embed_batch(self, mock_transformer: MagicMock) -> None:
        # Arrange
        mock_model = MagicMock()
        expected = np.array([[0.1, 0.2], [0.3, 0.4]])
        mock_model.encode.return_value = expected
        mock_transformer.return_value = mock_model

        embedder = SentenceEmbedder()

        # Act
        result = embedder.embed_batch(["text1", "text2"])

        # Assert
        assert np.array_equal(result, expected)
        mock_model.encode.assert_called_with(
            ["text1", "text2"],
            convert_to_numpy=True,
            normalize_embeddings=True,
            batch_size=32,
        )

    @patch("core.embedder.sentence_embedder.SentenceTransformer")
    def test_embed_batch_with_empty(self, mock_transformer: MagicMock) -> None:
        # Arrange
        mock_model = MagicMock()
        mock_transformer.return_value = mock_model

        embedder = SentenceEmbedder()

        # Act
        embedder.embed_batch(["text1", "   ", "text3"])

        # Assert
        mock_model.encode.assert_called_with(
            ["text1", " ", "text3"],
            convert_to_numpy=True,
            normalize_embeddings=True,
            batch_size=32,
        )

    @patch("core.embedder.sentence_embedder.SentenceTransformer")
    def test_embedding_dimension(self, mock_transformer: MagicMock) -> None:
        # Arrange
        mock_model = MagicMock()
        mock_model.get_sentence_embedding_dimension.return_value = 768
        mock_transformer.return_value = mock_model

        embedder = SentenceEmbedder()

        # Act
        dim = embedder.embedding_dimension

        # Assert
        assert dim == 768
