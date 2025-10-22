from core.registry import registry
import random


@registry.tool(tags=["utility"])
def list_available_tools() -> float:
    """Returns a list of available tools in the registry."""
    return list(registry.tool_registry.keys())


@registry.tool(tags=["arithmetic", "random_value"])
def random_value() -> float:
    """Returns a random float value between 0 and 1."""
    return random.random()
