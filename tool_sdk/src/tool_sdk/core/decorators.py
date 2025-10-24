from functools import wraps


def mcp_tool(name: str, tags=None, entry_point: bool = False):
    def decorator(cls):
        cls.name = name
        cls.tags = tags or []
        cls.entry_point = entry_point
        return cls

    return decorator
