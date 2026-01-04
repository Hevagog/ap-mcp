from typing import Any

from core import get_logger, registry
from core.exceptions import GenerationError, OllamaAPIError, ToolSelectionError
from core.llm import LocalLLM
from core.models import OrchestratorResponse, ToolInvocationResult

logger = get_logger(__name__)


class LLMOrchestrator:
    """Orchestrates tool selection and invocation using a local LLM."""

    def __init__(self) -> None:
        self._llm = LocalLLM()
        logger.debug("Initialized LLMOrchestrator with local LLM")

    def _filter_callable_tools(self, tool_metadata_list: list[dict[str, Any]]) -> list[dict[str, Any]]:
        filtered: list[dict[str, Any]] = []

        for tool_meta in tool_metadata_list:
            tool_name = tool_meta.get("name", "")
            if not tool_name:
                continue

            # Skip parent tool entries (e.g., "calculator"), only use method entries (e.g., "calculator.add")
            if "." not in tool_name and tool_meta.get("external"):
                continue

            filtered.append(tool_meta)
            logger.debug("Included tool for selection", extra={"tool_name": tool_name})

        return filtered

    def _invoke_tool(self, tool_name: str, arguments: dict[str, Any]) -> ToolInvocationResult:
        try:
            result = registry.call_tool(tool_name, **arguments)
            return ToolInvocationResult(
                tool_name=tool_name,
                arguments=arguments,
                result=result,
                success=True,
                error=None,
            )
        except KeyError as e:
            logger.error("Tool not found", extra={"tool_name": tool_name, "error": str(e)})
            return ToolInvocationResult(
                tool_name=tool_name,
                arguments=arguments,
                result=None,
                success=False,
                error=f"Tool not found: {tool_name}",
            )
        except Exception as e:
            logger.exception("Error invoking tool", extra={"tool_name": tool_name, "error": str(e)})
            return ToolInvocationResult(
                tool_name=tool_name,
                arguments=arguments,
                result=None,
                success=False,
                error=str(e),
            )

    async def process_message(self, user_message: str, top_k: int = 3) -> OrchestratorResponse:
        """
        Process a user message by:
        1. Querying the vector DB for relevant tools
        2. Using local LLM to select and parameterize the best tool
        3. Invoking the selected tool
        4. Returning the result

        Args:
            user_message: The user's natural language query.
            top_k: Number of candidate tools to retrieve from vector DB.

        Returns:
            OrchestratorResponse with the result or error message.
        """
        tool_matches = registry.query_tools_by_description(user_message, top_k=top_k)
        tool_names = [t.get("name", "") for t in tool_matches if t.get("name")]

        logger.info(
            "Found candidate tools",
            extra={"user_message": user_message, "candidates": tool_names},
        )

        invocation_result, selected_tool, tool_data = None, None, None

        if not tool_matches:
            logger.info("No tools found matching user request")

        callable_tools = self._filter_callable_tools(tool_matches)

        if callable_tools:
            try:
                selection = self._llm.select_tool(user_message, callable_tools)
                selected_tool = selection.get("tool_name")
                arguments = selection.get("arguments", {})

                if selected_tool:
                    logger.info(
                        "LLM selected tool",
                        extra={"tool_name": selected_tool, "arguments": arguments},
                    )
                    invocation_result = self._invoke_tool(selected_tool, arguments)

                    if invocation_result.success:
                        tool_data = invocation_result.result
                    else:
                        tool_data = f"Error: {invocation_result.error}"
                else:
                    logger.info("LLM decided not to select any tool.")

            except (OllamaAPIError, ToolSelectionError) as e:
                logger.exception("LLM tool selection failed", extra={"error": str(e)})
                return OrchestratorResponse(
                    message=f"Error during tool selection: {e}",
                    tool_invocation=None,
                    raw_tool_matches=tool_names,
                )
        try:
            if selected_tool and tool_data:
                final_response_text = self._llm.generate_response(
                    user_message=user_message, tool_name=selected_tool, tool_result=tool_data
                )
            else:
                logger.info("No tool used. Falling back to general conversation.")
                final_response_text = self._llm.chat(user_message)

        except GenerationError as e:
            logger.error(
                "Response generation failed",
                extra={"exception": e},
            )
            final_response_text = "I'm sorry, I encountered an error while processing your request."
            if tool_data:
                final_response_text += f"\n\nTechnical Result: {tool_data}"

        return OrchestratorResponse(
            message=final_response_text,
            tool_invocation=invocation_result,
            raw_tool_matches=tool_names,
        )


orchestrator = LLMOrchestrator()
