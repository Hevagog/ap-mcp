from __future__ import annotations

import os
from typing import Any, Dict, List
from functools import partial

from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from tool_sdk.core.manifest import Manifest, build_manifest
from tool_sdk.logging import get_logger

logger = get_logger(__name__)


class InvokeRequest(BaseModel):
    method: str
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}


@asynccontextmanager
async def lifespan(app: FastAPI, manifest: Manifest, tool_name: str):
    server_url = os.getenv("MCP_SERVER_URL")
    if not server_url:
        server_port = os.getenv("MCP_SERVER_PORT", "5000")
        server_url = f"http://mcp_server:{server_port}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
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


def create_app(tool_instance) -> FastAPI:
    method_names = [
        name
        for name in dir(tool_instance)
        if not name.startswith("_") and callable(getattr(tool_instance, name))
    ]

    tool_name = getattr(tool_instance, "name", tool_instance.__class__.__name__)
    tags = getattr(tool_instance, "tags", [])
    description = (tool_instance.__doc__ or "").strip()

    tool_url = os.getenv("TOOL_PUBLIC_URL")

    manifest = build_manifest(
        name=tool_name,
        description=description,
        tags=tags,
        base_url=tool_url,
        methods=method_names,
    )

    app = FastAPI(
        title=f"{getattr(tool_instance, 'name', 'tool')} SDK App",
        logger=logger,
        lifespan=partial(lifespan, manifest=manifest, tool_name=tool_name),
    )

    @app.get("/manifest", response_model=Manifest)
    async def get_manifest():
        return manifest

    @app.post("/invoke")
    async def invoke(req: InvokeRequest):
        method = getattr(tool_instance, req.method, None)
        if method is None or not callable(method):
            raise HTTPException(
                status_code=404, detail=f"Method {req.method} not found"
            )
        try:
            result = method(*req.args, **req.kwargs)
            return {"result": result}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return app
