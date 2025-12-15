from fastapi import FastAPI

from core import get_logger, registry_router
from core.communication import communication_router
from core.registry.registry import registry as tool_registry
from core_tools import tool_manager

logger = get_logger(__name__)


app = FastAPI()
app.include_router(tool_manager.router)
app.include_router(registry_router.router)
app.include_router(communication_router)


@app.get("/", include_in_schema=False)
async def root() -> dict[str, str]:
    return {"message": "MCP Server Operational"}


@app.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready", include_in_schema=False)
async def ready() -> dict[str, str | int]:
    try:
        tools = tool_registry.list_tools()
        return {
            "status": "ready",
            "tools_registered": len(tools),
        }
    except Exception as e:
        return {"status": "not-ready", "error": str(e)}
