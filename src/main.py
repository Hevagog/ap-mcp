from fastapi import FastAPI
import uvicorn
import os
from core import get_logger
from tools import tool_manager

logger = get_logger(__name__)


app = FastAPI()
app.include_router(tool_manager.router)


@app.get("/", include_in_schema=False)
async def root():
    return {"message": "MCP Server Operational"}


if __name__ == "__main__":
    logger.info("Starting MCP Server on port 5000")
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info", log_config=None)
