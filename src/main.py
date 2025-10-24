from fastapi import FastAPI
import uvicorn
import os
from core import get_logger, registry_router
from core.registry.registry import registry as tool_registry
from core_tools import tool_manager

logger = get_logger(__name__)


app = FastAPI()
app.include_router(tool_manager.router)
app.include_router(registry_router.router)


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "MCP Server Operational"}


@app.get("/health", include_in_schema=False)
async def health():
    return {"status": "ok"}


@app.get("/ready", include_in_schema=False)
async def ready():
    try:
        tools = tool_registry.list_tools()
        return {
            "status": "ready",
            "tools_registered": len(tools),
        }
    except Exception as e:
        return {"status": "not-ready", "error": str(e)}


if __name__ == "__main__":
    port = int(os.environ.get("MCP_SERVER_PORT", "5000"))
    logger.info(f"Starting MCP Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info", log_config=None)
