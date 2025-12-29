import os
from typing import Any

import ollama
from ollama import Client

from core import get_logger

logger = get_logger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:1.5b")


class LocalLLM:
    def __init__(self, model_name: str | None = None) -> None:
        self._model_name = model_name or OLLAMA_MODEL
        self._client = Client(host=OLLAMA_HOST)

        logger.debug(
            "Initialized LocalLLM with Ollama",
            extra={"model": self._model_name, "host": OLLAMA_HOST},
        )

        self._ensure_model_available()

    def _ensure_model_available(self) -> None:
        try:
            list_response = self._client.list()

            models = list_response.models if hasattr(list_response, "models") else list_response.get("models", [])

            installed_models = []
            for m in models:
                if hasattr(m, "model"):
                    installed_models.append(m.model)
                elif isinstance(m, dict):
                    installed_models.append(m.get("name") or m.get("model"))
                else:
                    installed_models.append(str(m))

            if not any(self._model_name in model for model in installed_models):
                logger.info(
                    "Pulling Ollama model (this may take a while)...",
                    extra={"model": self._model_name},
                )
                self._client.pull(self._model_name)
                logger.info("Model pulled successfully", extra={"model": self._model_name})

        except Exception as e:
            logger.warning(
                "Could not verify model availability",
                extra={"error": str(e), "model": self._model_name},
            )

    def select_tool(self, user_message: str, tools: list[dict[str, Any]]) -> dict[str, Any]:
        """
        Select the best tool for the user message using Native Tool Calling.

        Args:
            user_message: The user's natural language query.
            tools: List of tool definitions (from Registry/Vector DB).

        Returns:
            Dictionary with 'tool_name' and 'arguments'.
        """
        if not tools:
            return {"tool_name": None, "arguments": {}}

        formatted_tools = []
        for tool in tools:
            formatted_tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.get("name"),
                        "description": tool.get("description"),
                        "parameters": tool.get("parameters"),
                    },
                }
            )

        try:
            response = self._client.chat(
                model=self._model_name,
                messages=[{"role": "user", "content": user_message}],
                tools=formatted_tools,
                options={
                    "temperature": 0.1,  # Keeping low for deterministic tool selection
                },
            )

            message = response.message if hasattr(response, "message") else response["message"]
            tool_calls = message.tool_calls if hasattr(message, "tool_calls") else message.get("tool_calls")

            if tool_calls:
                tool_call = tool_calls[0]

                function_data = tool_call.function if hasattr(tool_call, "function") else tool_call["function"]

                if hasattr(function_data, "name"):
                    name = function_data.name
                    arguments = function_data.arguments
                else:
                    name = function_data["name"]
                    arguments = function_data["arguments"]

                logger.info("Tool selected", extra={"tool": name, "query": user_message})

                return {"tool_name": name, "arguments": arguments}

            logger.debug("No tool selected by model", extra={"query": user_message})
            return {"tool_name": None, "arguments": {}}

        except ollama.ResponseError as e:
            logger.error(
                "Ollama API error during tool selection",
                extra={
                    "error": str(e),
                    "status_code": e.status_code,
                    "tools_sent": formatted_tools,
                },
            )
            return {"tool_name": None, "arguments": {}}
        except Exception as e:
            logger.exception("Unexpected error during tool selection", extra={"error": str(e)})
            return {"tool_name": None, "arguments": {}}
