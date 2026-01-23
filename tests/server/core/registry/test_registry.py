from unittest.mock import ANY, MagicMock, patch

import pytest

from core.registry.registry import Registry


class TestRegistry:
    @pytest.fixture()
    def mock_vec_db(self):
        with patch("core.registry.registry.VectorDB") as mock:
            yield mock.return_value

    @pytest.fixture()
    def registry_instance(self, mock_vec_db):
        return Registry("test_registry")

    def test_core_tool_decorator(self, registry_instance, mock_vec_db):
        # Arrange
        @registry_instance.core_tool(name="my_tool", tags=["tag1"])
        def my_function(x: int) -> int:
            """My tool description."""
            return x * 2

        # Assert
        assert "my_tool" in registry_instance.tool_registry
        entry = registry_instance.tool_registry["my_tool"]
        assert entry["name"] == "my_tool"
        assert entry["description"] == "My tool description."
        assert entry["tags"] == ["tag1"]
        assert entry["callable"](5) == 10
        mock_vec_db.add.assert_called()

    def test_core_tool_decorator_defaults(self, registry_instance, mock_vec_db):
        # Arrange
        @registry_instance.core_tool()
        def plain_func():
            pass

        # Assert
        assert "plain_func" in registry_instance.tool_registry
        assert registry_instance.tool_registry["plain_func"]["name"] == "plain_func"

    def test_core_tool_indexing_error_handled(self, registry_instance, mock_vec_db):
        # Arrange
        mock_vec_db.add.side_effect = Exception("Indexing failed")

        # Act & Assert (Should not raise)
        @registry_instance.core_tool(name="broken_index")
        def func():
            pass

        assert "broken_index" in registry_instance.tool_registry

    def test_register_tool_missing_required(self, registry_instance):
        with pytest.raises(ValueError, match="Manifest missing required field: name"):
            registry_instance.register_tool({"base_url": "http://example.com"})

    def test_register_tool_external(self, registry_instance, mock_vec_db):
        # Arrange
        tool_data = {
            "name": "ext_tool",
            "base_url": "http://api.com",
            "description": "External tool desc",
            "methods": [{"name": "method1", "description": "Method 1 desc", "parameters": {"p1": "string"}}],
        }

        # Act
        registry_instance.register_tool(tool_data)

        # Assert
        assert "ext_tool" in registry_instance.tool_registry
        assert "ext_tool.method1" in registry_instance.tool_registry

        entry = registry_instance.tool_registry["ext_tool.method1"]
        assert entry["external"] is True
        assert entry["base_url"] == "http://api.com"

        mock_vec_db.add.assert_any_call("External tool desc", metadata=ANY)
        mock_vec_db.add.assert_any_call("Method 1 desc", metadata=ANY)

    @patch("core.registry.registry.httpx.Client")
    def test_external_tool_proxy_call_post(self, mock_client_cls, registry_instance):
        # Arrange
        tool_data = {"name": "math", "base_url": "http://math.com", "methods": [{"name": "add"}]}
        registry_instance.register_tool(tool_data)

        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.post.return_value.json.return_value = {"result": 42}
        mock_client.post.return_value.status_code = 200

        # Act
        result = registry_instance.call_tool("math.add", 20, 22)

        # Assert
        assert result == 42
        mock_client.post.assert_called_with(
            "http://math.com/invoke/add", json={"method": "add", "args": [20, 22], "kwargs": {}}
        )

    @patch("core.registry.registry.httpx.Client")
    def test_external_tool_proxy_call_get(self, mock_client_cls, registry_instance):
        # Arrange
        tool_data = {
            "name": "info",
            "base_url": "http://info.com",
            "methods": [{"name": "status", "http_method": "GET"}],
        }
        registry_instance.register_tool(tool_data)

        mock_client = MagicMock()
        mock_client_cls.return_value.__enter__.return_value = mock_client
        mock_client.get.return_value.json.return_value = {"status": "ok"}
        mock_client.get.return_value.status_code = 200

        # Act
        result = registry_instance.call_tool("info.status")

        # Assert
        assert result == {"status": "ok"}  # Standard return is data.get('result', data)
        mock_client.get.assert_called_with(
            "http://info.com/invoke/status", params={"method": "status", "args": [], "kwargs": {}}
        )

    def test_call_tool_not_found(self, registry_instance):
        with pytest.raises(KeyError, match="Tool 'missing' not registered"):
            registry_instance.call_tool("missing")

    def test_list_tools(self, registry_instance):
        @registry_instance.core_tool(name="t1")
        def t1():
            pass

        assert "t1" in registry_instance.list_tools()

    def test_get_tool_definitions(self, registry_instance):
        @registry_instance.core_tool(name="t1")
        def t1():
            pass

        defs = registry_instance.get_tool_definitions()
        assert len(defs) == 1
        assert defs[0]["name"] == "t1"
        assert "callable" not in defs[0]

    def test_query_tools_by_description(self, registry_instance, mock_vec_db):
        mock_vec_db.text_query.return_value = [{"name": "t1"}]
        results = registry_instance.query_tools_by_description("query")
        assert results == [{"name": "t1"}]
        mock_vec_db.text_query.assert_called_with("query", top_k=5)
