from __future__ import annotations

__docformat__ = "restructuredtext"

_hard_dependencies = ["fastapi"]

for _dependency in _hard_dependencies:
    try:
        __import__(_dependency)
    except ImportError as _e:
        raise ImportError(
            f"Unable to import required dependency {_dependency}. "
        ) from _e

del _hard_dependencies, _dependency

from tool_sdk.core import mcp_tool, base
from tool_sdk.app import create_app
from tool_sdk.logging import get_logger

ToolBase = base.ToolBase
__all__ = ["mcp_tool", "ToolBase", "create_app", "get_logger"]
