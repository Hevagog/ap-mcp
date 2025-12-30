from abc import ABC, abstractmethod
from typing import Any


class ToolBase(ABC):
    name: str
    version: str
    capabilities: list[str]

    @abstractmethod
    def execute(self, method: str, **kwargs: Any) -> Any: ...
