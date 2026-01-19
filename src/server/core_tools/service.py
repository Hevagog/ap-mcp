import random

from core.registry.registry import registry


@registry.core_tool(tags=["utility"])
def list_available_tools() -> list[str]:
    """Returns a list of available tools in the registry."""
    return list(registry.tool_registry.keys())


@registry.core_tool(tags=["arithmetic", "random_value"])
def random_value() -> float:
    """Returns a random float value between 0 and 1."""
    return random.random()  # noqa: S311
