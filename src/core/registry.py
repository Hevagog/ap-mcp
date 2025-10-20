from typing import Callable, Dict
from core.logging import get_logger

logger = get_logger(__name__)


class Registry:
    def __init__(self, name: str):
        logger.debug(f"Initializing registry: {name}")
        self.name = name
        self._tools: Dict[str, Callable] = {}

    def tool(self, name: str | None = None):

        def decorator(func: Callable):
            tool_name = name or func.__name__
            logger.info(f"Registering tool: {tool_name}")
            self._tools[tool_name] = func
            return func

        return decorator

    def list_tools(self):
        return list(self._tools.keys())

    def call_tool(self, name: str, *args, **kwargs):
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' not registered")
        return self._tools[name](*args, **kwargs)


registry = Registry("default")
