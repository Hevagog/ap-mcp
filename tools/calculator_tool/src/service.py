import uvicorn
import os

from tool_sdk import mcp_tool, ToolBase, create_app


@mcp_tool(name="calculator", tags=["math", "arithmetic"], entry_point=True)
class CalculatorTool(ToolBase):
    def execute(self, a: int, b: int) -> int:
        return a + b


if __name__ == "__main__":
    _tool = CalculatorTool()
    app = create_app(_tool)
    port = int(os.environ.get("TOOL_PORT", "5080"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info", log_config=None)
