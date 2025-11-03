from fastapi import APIRouter, Request
from typing import Dict
from core import get_logger
from core.registry.registry import registry as tool_registry
from core.models.manifest import Manifest

logger = get_logger(__name__)


router = APIRouter()


@router.post("/register")
async def register_tool_(request: Request):
    logger.info("Received tool registration request")
    payload = await request.json()
    manifest = Manifest.model_validate(payload)
    logger.info(f"Tool registration payload: {payload}")
    tool_registry.register_tool(manifest.model_dump())
    logger.info(f"Tool registered: {manifest.name}")
    return {"status": "ok"}
