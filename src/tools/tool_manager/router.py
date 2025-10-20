from fastapi import APIRouter
from .service import random_value

router = APIRouter()


@router.get(
    "/tools",
)
async def list_tools():
    tools = random_value()
    return {"tools": tools}
