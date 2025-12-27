from fastapi import APIRouter

from .service import list_available_tools, random_value

router = APIRouter()


@router.get(
    "/tools",
)
async def list_tools() -> dict[str, list[str]]:
    tools = list_available_tools()
    return {"tools": tools}


@router.get(
    "/tools/random",
)
async def get_random_tool() -> dict[str, float]:
    tool = random_value()
    return {"tool": tool}
