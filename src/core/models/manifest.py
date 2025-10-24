from pydantic import BaseModel, HttpUrl, Field
from typing import List, Optional


class MethodSpec(BaseModel):
    name: str = Field(..., description="Method name exposed by the tool")
    description: Optional[str] = Field(
        default=None, description="Docstring/summary for this method"
    )
    path: Optional[str] = Field(
        default=None, description="Optional explicit HTTP path for this method"
    )
    http_method: Optional[str] = Field(
        default=None, description="Optional HTTP method if using explicit path"
    )


class Manifest(BaseModel):
    name: str
    description: str = ""
    tags: List[str] = []
    base_url: str
    methods: List[MethodSpec] = []
