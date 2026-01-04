from functools import wraps
from typing import Any, Callable


def mcp_tool(name: str) -> Callable[[Any], Any]:
    """
    Annotation decorator to mark a function as an MCP tool.
    Args:
        name: The name of the tool.
    - Function: attaches __mcp_tool_meta__ so the SDK can discover it.
    """

    def decorator(target: Any) -> Any:
        meta = {
            "name": name,
            "description": target.__doc__,
        }
        setattr(target, "__mcp_tool_meta__", meta)
        return target

    return decorator
