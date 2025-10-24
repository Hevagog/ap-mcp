from abc import ABC, abstractmethod


class ToolBase(ABC):
    name: str
    version: str
    capabilities: list[str]

    @abstractmethod
    def execute(self, method: str, **kwargs): ...
