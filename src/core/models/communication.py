from pydantic import BaseModel


class MessageRequest(BaseModel):
    content: str


class MessageResponse(BaseModel):
    content: str
