from pydantic import BaseModel, Field
from typing import List, Optional


class MethodSpec(BaseModel):
    name: str = Field(..., description="Method name exposed by the tool")
    path: Optional[str] = Field(default=None)
    http_method: Optional[str] = Field(default=None)


class Manifest(BaseModel):
    name: str
    description: str = ""
    tags: List[str] = []
    base_url: str
    methods: List[MethodSpec] = []


def build_manifest(
    *,
    name: str,
    description: str = "",
    tags: Optional[List[str]] = None,
    base_url: str,
    methods: Optional[List[str]] = None,
) -> Manifest:
    return Manifest(
        name=name,
        description=description or "",
        tags=tags or [],
        base_url=base_url,
        methods=[MethodSpec(name=m) for m in (methods or [])],
    )
