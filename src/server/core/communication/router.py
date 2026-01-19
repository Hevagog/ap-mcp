from fastapi import APIRouter

from core import get_logger
from core.models import MessageRequest, OrchestratorResponse
from core.orchestrator import LLMOrchestrator

logger = get_logger(__name__)

router = APIRouter()

_orchestrator = LLMOrchestrator()


@router.post("/message", response_model=OrchestratorResponse)
async def handle_message(request: MessageRequest) -> OrchestratorResponse:
    logger.info("Received message request", extra={"content": request.content})

    response = await _orchestrator.process_message(request.content)

    logger.info(
        "Orchestrator response",
        extra={
            "response_message": response.message,
            "tool_invocation": (response.tool_invocation.model_dump() if response.tool_invocation else None),
        },
    )

    return response
