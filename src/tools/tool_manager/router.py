from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/tools",
)
async def list_tools():
    return {"message": "No tools as of yet."}
