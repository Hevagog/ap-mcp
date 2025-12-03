from fastapi import APIRouter
from core import get_logger
from core.models import MessageRequest, MessageResponse
from core.registry import registry

logger = get_logger(__name__)

router = APIRouter()


@router.post("/message", response_model=MessageResponse)
async def handle_message(request: MessageRequest) -> MessageResponse:
    logger.info(f"Received message request: {request}")

    logger.info("Queried tools based on message content")
    result = registry.query_tools_by_description(request.content)
    logger.info(f"Tools matching the message: {result}")

    return MessageResponse(content=f"Found tools: {result}")
