from typing import Any

from pydantic import BaseModel


class MessageRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    content: str


class ToolInvocationResult(BaseModel):
    tool_name: str
    arguments: dict[str, Any]
    result: Any
    success: bool
    error: str | None = None


class OrchestratorResponse(BaseModel):
    message: str
    tool_invocation: ToolInvocationResult | None = None
    raw_tool_matches: list[str] | None = None
