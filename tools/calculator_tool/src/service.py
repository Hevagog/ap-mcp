import uvicorn
import os

from tool_sdk import mcp_tool, create_app


@mcp_tool(name="calculator")
def add(a: int, b: int) -> int:
    """Add two integers and return the result."""
    return a + b


if __name__ == "__main__":
    app = create_app(add)
    port = int(os.environ.get("TOOL_PORT", "5080"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info", log_config=None)
