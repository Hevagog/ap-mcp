from fastapi import APIRouter

router = APIRouter()


@router.get(
    "/calculate_status",
)
async def calculate_status():
    return {"message": "Kalkulator Operational"}
