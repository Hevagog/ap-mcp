import os
from functools import partial
from typing import Any, Callable

import httpx
from google import genai
from google.genai import types

from core import get_logger
from core.vec_db import VectorDB

client = genai.Client(api_key=os.getenv("API_KEY"))


logger = get_logger(__name__)


class Registry:
    def __init__(self, name: str):
        logger.debug("Initializing registry", extra={"registry_name": name})
        self.tool_registry: dict[str, dict[str, Any]] = {}
        self._model = "gemini-embedding-001"
        self.config = types.EmbedContentConfig(task_type="SEMANTIC_SIMILARITY")
        self._vec_db = VectorDB(
            embedding_function=partial(
                client.models.embed_content,
                model=self._model,
                config=self.config,
            )
        )

    def core_tool(self, name: str | None = None, tags: list[str] | None = None, **meta: Any) -> Callable:
        def decorator(func: Callable) -> Callable:
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
                "Registered tool with metadata",
                extra={"meta_entry": meta_entry, "tool_name": meta_entry["name"]},
            )
            try:
                self._vec_db.add([meta_entry["description"]], metadata=meta_entry)
            except Exception:
                logger.exception("Failed to index tool description")

            return func

        return decorator

    def register_tool(self, tool_data: dict) -> None:
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
                "Tool registered without methods; only metadata stored.",
                extra={"tool_name": tool_name},
            )

        def _make_proxy(method_name: str, path: str | None = None, http_method: str | None = None) -> Callable:
            def _proxy(*args: Any, **kwargs: Any) -> Any:
                payload = {"method": method_name, "args": list(args), "kwargs": str(kwargs)}
                with httpx.Client(timeout=30.0) as client_http:
                    target_path = path or f"/invoke/{method_name}"
                    url = f"{base_url}{target_path}"
                    method = (http_method or "POST").upper()
                    if method == "GET":
                        resp = client_http.get(url, params=payload)
                    else:
                        resp = client_http.post(url, json=payload)
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

        logger.debug("Registered tool metadata", extra={"meta_entry": meta_entry})

        if description:
            try:
                self._vec_db.add(description, tool_name)
            except Exception as e:
                logger.warning("Failed to index tool description", extra={"tool_name": tool_name, "exception": e})

        logger.info("Registered external tool", extra={"tool_name": tool_name, "base_url": base_url})

        for m in methods:
            m_name = m.get("name")
            if not m_name:
                continue
            fq_name = f"{tool_name}.{m_name}"
            m_desc = m.get("description") or f"Proxy to {tool_name}.{m_name}"
            m_path = m.get("path")
            m_http = m.get("http_method")
            m_params = m.get("parameters", {})
            entry = {
                "name": fq_name,
                "title": f"{tool_name}:{m_name}",
                "description": m_desc,
                "parameters": m_params,
                "tags": tags,
                "callable": _make_proxy(m_name, path=m_path, http_method=m_http),
                "external": True,
                "base_url": base_url,
                "version": tool_data.get("version"),
            }
            self.tool_registry[fq_name] = entry
            logger.debug("Registered method proxy", extra={"fq_name": fq_name})
            if m_desc:
                try:
                    self._vec_db.add(m_desc, fq_name)
                except Exception:
                    logger.exception("Failed to index method description", extra={"method_name": fq_name})

    def list_tools(self) -> list[str]:
        return self._get_tool_names()

    def call_tool(self, name: str, *args: Any, **kwargs: Any) -> dict[str, Any]:
        if name not in self.tool_registry:
            raise KeyError(f"Tool '{name}' not registered")
        return self.tool_registry[name]["callable"](*args, **kwargs)

    def _get_tool_names(self) -> list[str]:
        return list(self.tool_registry.keys())

    def get_tool_definitions(self) -> list[dict[str, Any]]:
        defs = []
        for _, v in self.tool_registry.items():
            tool_def = {key: val for key, val in v.items() if key != "callable"}
            defs.append(tool_def)
        return defs

    def query_tools_by_description(self, description: str, top_k: int = 5) -> list[dict]:
        return self._vec_db.text_query(description, top_k=top_k)


registry = Registry("default")
