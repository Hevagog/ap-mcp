from fastapi import APIRouter
from .schemas import CodeInput, CodeOutput
from .service import execute_code

router = APIRouter()


@router.get(
    "/calculate_status",
)
async def calculate_status():
    return {"message": "Kalkulator Operational"}
