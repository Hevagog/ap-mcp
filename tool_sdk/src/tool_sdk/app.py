from __future__ import annotations

import os
from typing import Any, Dict, List, Callable, Iterable, DefaultDict
from functools import partial
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from tool_sdk.core.manifest import Manifest, MethodSpec, build_manifest
from tool_sdk.logging import get_logger

logger = get_logger(__name__)


class InvokeRequest(BaseModel):
    method: str
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI, manifests: List[Manifest]):
    server_url = os.getenv("MCP_SERVER_URL")
    if not server_url:
        server_port = os.getenv("MCP_SERVER_PORT", "5000")
        server_url = f"http://mcp_server:{server_port}"
    try:
        for manifest in manifests:
            tool_name = manifest.name
            async with httpx.AsyncClient(timeout=10.0) as client:
                server_register_url = f"{server_url.rstrip('/')}/register"
                logger.info(
                    "Auto-registering tool '%s' to MCP server at %s",
                    tool_name,
                    server_register_url,
                )
                resp = await client.post(
                    server_register_url,
                    json=manifest.model_dump(),
                )
                logger.info("Auto-registration response: %s", resp)
                resp.raise_for_status()
            logger.info(
                "Auto-registered tool '%s' to MCP server at %s", tool_name, server_url
            )
    except Exception as e:
        logger.warning("Auto-register failed: %s", e)

    yield


def create_app(tool: Callable | Iterable[Callable]) -> FastAPI:
    """
    Create an SDK FastAPI app around:
      - a collection of standalone functions decorated with @mcp_tool(name=...)
    """

    method_map: Dict[str, Callable] = {}
    tool_url = os.getenv("TOOL_PUBLIC_URL")

    grouped: Dict[str, Dict[str, Any]] = {}
    funcs = list(tool) if isinstance(tool, Iterable) and not callable(tool) else [tool]  # type: ignore[arg-type]

    for f in funcs:
        if not callable(f):
            continue
        meta = getattr(f, "__mcp_tool_meta__", None)
        if not meta:
            raise ValueError(
                "All functions must be decorated with @mcp_tool(name=...) and have proper docstrings to be discoverable"
            )
        tool_name = meta.get("name")
        doc = (f.__doc__ or "").strip()
        if not doc:
            raise ValueError(
                f"Function '{f.__name__}' must have a docstring to be discoverable"
            )

        if tool_name not in grouped:
            grouped[tool_name] = {"descriptions": [], "methods": []}
        grouped[tool_name]["descriptions"].append(doc)
        grouped[tool_name]["methods"].append(f.__name__)
        method_map[f.__name__] = f

    manifests: List[Manifest] = []
    for tool_name, data in grouped.items():
        method_specs: List[MethodSpec] = []
        for idx, method_name in enumerate(data["methods"]):
            doc = data["descriptions"][idx]
            method_specs.append(
                MethodSpec(
                    name=method_name,
                    description=doc,
                    path=f"/invoke/{method_name}",
                    http_method="POST",
                )
            )
        manifest = build_manifest(
            name=tool_name,
            description="",
            base_url=tool_url,
            methods=method_specs,
        )
        manifests.append(manifest)

    app_title = next(iter(grouped.keys())) if len(grouped) == 1 else "MCP Tool SDK App"
    app = FastAPI(
        title=f"{app_title} SDK App",
        lifespan=partial(lifespan, manifests=manifests),
    )

    for method_name, fn in method_map.items():
        route_path = f"/invoke/{method_name}"

        def endpoint_factory(f: Callable):
            async def _endpoint(req: InvokeRequest):
                try:
                    result = f(*req.args, **req.kwargs)
                    return {"result": result}
                except Exception as e:
                    raise HTTPException(status_code=500, detail=str(e))

            return _endpoint

        app.post(route_path)(endpoint_factory(fn))

    @app.get("/manifest", response_model=List[Manifest])
    async def get_manifest():
        return manifests

    return app
