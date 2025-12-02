from fastapi import APIRouter, Request, HTTPException
from typing import Dict, List, Any
from pydantic import BaseModel
from core import get_logger
from core.registry.registry import registry as tool_registry
from core.models.manifest import Manifest

logger = get_logger(__name__)


router = APIRouter()


class ToolCallRequest(BaseModel):
    tool_name: str
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}


@router.get("/tools/definitions")
async def get_tool_definitions():
    return tool_registry.get_tool_definitions()


@router.post("/tools/call")
async def call_tool(request: ToolCallRequest):
    try:
        result = tool_registry.call_tool(
            request.tool_name, *request.args, **request.kwargs
        )
        return {"result": result}
    except Exception as e:
        logger.error(f"Error calling tool {request.tool_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/register")
async def register_tool_(request: Request):
    logger.info("Received tool registration request")
    payload = await request.json()
    manifest = Manifest.model_validate(payload)
    logger.info(f"Tool registration payload: {payload}")
    tool_registry.register_tool(manifest.model_dump())
    logger.info(f"Tool registered: {manifest.name}")
    return {"status": "ok"}
