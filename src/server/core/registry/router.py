from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from core import get_logger
from core.models.manifest import Manifest
from core.registry.registry import registry as tool_registry

logger = get_logger(__name__)


router = APIRouter()


class ToolCallRequest(BaseModel):
    tool_name: str
    args: list[Any] = []
    kwargs: dict[str, Any] = {}


@router.get("/tools/definitions")
async def get_tool_definitions() -> list[dict[str, Any]]:
    return tool_registry.get_tool_definitions()


@router.post("/tools/call")
async def call_tool(request: ToolCallRequest) -> dict[str, Any]:
    try:
        result = tool_registry.call_tool(request.tool_name, *request.args, **request.kwargs)
        return {"result": result}
    except Exception as e:
        logger.error("Error calling tool", extra={"tool_name": request.tool_name, "exception": e})
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register")
async def register_tool_(request: Request) -> dict[str, str]:
    logger.info("Received tool registration request")
    payload = await request.json()
    manifest = Manifest.model_validate(payload)
    logger.info("Tool registration", extra={"payload": payload})
    tool_registry.register_tool(manifest.model_dump())
    logger.info("Tool registered", extra={"tool_name": manifest.name})
    return {"status": "ok"}
