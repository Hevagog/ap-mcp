from typing import Callable
from google import genai
from google.genai import types
from functools import partial
import httpx
import os

from core import get_logger
from core.vec_db import VectorDB

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

    def core_tool(self, name: str | None = None, tags: list[str] | None = None, **meta):

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

    def register_tool(self, tool_data: dict):

        required = ["name", "base_url"]
        for k in required:
            if k not in tool_data:
                raise ValueError(f"Manifest missing required field: {k}")

        tool_name = tool_data["name"]
        tags = tool_data.get("tags", [])
        description = tool_data.get("description", "")
        base_url = tool_data["base_url"].rstrip("/")
        methods = tool_data.get("methods", [])

        if not methods:
            logger.warning(
                f"Tool '{tool_name}' registered without methods; only metadata stored."
            )

        def _make_proxy(method_name: str) -> Callable:
            def _proxy(*args, **kwargs):
                payload = {"method": method_name, "args": list(args), "kwargs": kwargs}
                with httpx.Client(timeout=30.0) as client_http:
                    resp = client_http.post(f"{base_url}/invoke", json=payload)
                    resp.raise_for_status()
                    data = resp.json()
                    return data.get("result", data)

            return _proxy

        meta_entry = {
            "name": tool_name,
            "title": tool_name,
            "description": description,
            "tags": tags,
            "callable": lambda: {
                "tool": tool_name,
                "version": tool_data.get("version"),
                "methods": [m.get("name") for m in methods],
            },
            "external": True,
            "base_url": base_url,
            "version": tool_data.get("version"),
        }
        self.tool_registry[tool_name] = meta_entry

        logger.debug(f"Registered tool metadata: {meta_entry}")

        self._vec_db.add(tags)
        logger.info(f"Registered external tool: {tool_name} @ {base_url}")

        for m in methods:
            m_name = m.get("name")
            if not m_name:
                continue
            fq_name = f"{tool_name}.{m_name}"
            entry = {
                "name": fq_name,
                "title": f"{tool_name}:{m_name}",
                "description": f"Proxy to {tool_name}.{m_name}",
                "tags": tags,
                "callable": _make_proxy(m_name),
                "external": True,
                "base_url": base_url,
                "version": tool_data.get("version"),
            }
            self.tool_registry[fq_name] = entry
            logger.debug(f"Registered method proxy: {fq_name}")

    def list_tools(self):
        return self._get_tool_names()

    def call_tool(self, name: str, *args, **kwargs):
        if name not in self.tool_registry:
            raise KeyError(f"Tool '{name}' not registered")
        return self.tool_registry[name]["callable"](*args, **kwargs)

    def _get_tool_names(self):
        return list(self.tool_registry.keys())


registry = Registry("default")
