from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class MethodSpec(BaseModel):
    name: str = Field(..., description="Method name exposed by the tool")
    description: Optional[str] = Field(
        default=None, description="Docstring/summary for this method"
    )
    parameters: dict[str, Any] = Field(
        default_factory=dict, description="JSON Schema for the method parameters"
    )
    path: Optional[str] = Field(
        default=None, description="HTTP path for invoking this method"
    )
    http_method: Optional[str] = Field(
        default=None,
        description="HTTP method used to invoke this method (e.g., GET, POST)",
    )


class Manifest(BaseModel):
    name: str
    description: str = ""
    base_url: str
    methods: list[MethodSpec] = []


def build_manifest(
    *,
    name: str,
    description: str = "",
    base_url: str,
    methods: Optional[list[MethodSpec | str]] = None,
) -> Manifest:
    specs: list[MethodSpec] = []
    for m in methods or []:
        if isinstance(m, MethodSpec):
            specs.append(m)
        else:
            specs.append(MethodSpec(name=str(m)))
    return Manifest(
        name=name, description=description or "", base_url=base_url, methods=specs
    )
