from typing import Callable
from core.logging import get_logger
from core.vec_db import VectorDB
from google import genai
from google.genai import types
from functools import partial
import os

client = genai.Client(api_key=os.getenv("API_KEY"))


logger = get_logger(__name__)


class Registry:
    def __init__(self, name: str):
        logger.debug(f"Initializing registry: {name}")
        self.tool_registry = {}
        self._vec_db = VectorDB(
            embedding_function=partial(
                client.models.embed_content,
                model="gemini-embedding-001",
                config=types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY"),
            )
        )

    def tool(self, name: str | None = None, tags: list[str] | None = None, **meta):

        def decorator(func: Callable):
            meta_entry = {
                "name": name or func.__name__,
                "title": (func.__doc__ or "").splitlines()[0] if func.__doc__ else "",
                "description": (func.__doc__ or ""),
                "tags": tags or [],
                "callable": func,
                **meta,
            }
            self.tool_registry[meta_entry["name"]] = meta_entry
            logger.debug(
                f"Registered tool: {meta_entry['name']} with metadata: {meta_entry}"
            )
            self._vec_db.add(meta_entry["tags"])
            return func

        return decorator

    def list_tools(self):
        return self._get_tool_names()

    def call_tool(self, name: str, *args, **kwargs):
        if name not in self.tool_registry:
            raise KeyError(f"Tool '{name}' not registered")
        return self.tool_registry[name]["callable"](*args, **kwargs)

    def _get_tool_names(self):
        return list(self.tool_registry.keys())


registry = Registry("default")
