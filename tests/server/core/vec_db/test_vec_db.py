from unittest.mock import MagicMock

import numpy as np
import pytest

from core.vec_db.dbase import VectorDB


class TestVectorDB:
    @pytest.fixture()
    def mock_embedder(self):
        embedder = MagicMock()
        embedder.embed.side_effect = lambda _: np.array([0.1, 0.2, 0.3])
        return embedder

    @pytest.fixture()
    def db(self, mock_embedder):
        return VectorDB(embedder=mock_embedder)

    def test_initialization(self, db):
        assert db.entries == []
        assert db._embedder is not None

    def test_add_entry(self, db, mock_embedder):
        # Arrange
        mock_embedder.embed.side_effect = None
        mock_embedder.embed.return_value = np.array([1.0, 0.0, 0.0])
        # Act
        db.add("test description", {"id": 1})
        # Assert
        assert len(db.entries) == 1
        assert np.array_equal(db.entries[0]["vector"], np.array([1.0, 0.0, 0.0]))
        assert db.entries[0]["metadata"] == {"id": 1}
        mock_embedder.embed.assert_called_with("test description")

    def test_query_empty_db(self, db):
        results = db.query(np.array([1.0, 0.0, 0.0]))
        assert results == []

    def test_query_logic(self, db):
        # Arrange
        db.entries = [
            {"vector": np.array([1.0, 0.0]), "metadata": {"name": "aligned"}},
            {"vector": np.array([0.0, 1.0]), "metadata": {"name": "orthogonal"}},
            {"vector": np.array([-1.0, 0.0]), "metadata": {"name": "opposite"}},
        ]
        query_vec = np.array([1.0, 0.0])
        # Act
        results = db.query(query_vec, top_k=3)
        # Assert
        assert len(results) == 3
        assert results[0]["name"] == "aligned"
        assert results[1]["name"] == "orthogonal"
        assert results[2]["name"] == "opposite"

    def test_query_top_k(self, db):
        # Arrange
        db.entries = [{"vector": np.array([1.0]), "metadata": {"id": i}} for i in range(5)]
        # Act
        results = db.query(np.array([1.0]), top_k=2)
        # Assert
        assert len(results) == 2

    def test_text_query(self, db, mock_embedder):
        # Arrange
        def side_effect(text):
            if text == "query":
                return np.array([1.0, 0.0])
            return np.array([0.0, 1.0])

        mock_embedder.embed.side_effect = side_effect

        # Act
        db.add("stored", {"id": "stored"})

        results = db.text_query("query", top_k=1)

        # Assert
        assert len(results) == 1
        assert results[0]["id"] == "stored"
        mock_embedder.embed.assert_any_call("query")

    def test_division_by_zero_prevention(self, db):
        # Arrange
        db.entries = [{"vector": np.array([0.0, 0.0]), "metadata": {"id": "zero"}}]
        query_vec = np.array([1.0, 0.0])

        # Act
        results = db.query(query_vec)

        # Assert
        assert len(results) == 1
        assert results[0]["id"] == "zero"

    def test_embed_text_list_handling(self, db, mock_embedder):
        mock_embedder.embed.return_value = np.array([1.0])
        db.add(["list input"], {"id": 1})
        mock_embedder.embed.assert_called_with("list input")

        db.add([], {"id": 2})
        mock_embedder.embed.assert_called_with("")
