class OllamaError(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


class ToolSelectionError(OllamaError):
    pass


class OllamaAPIError(OllamaError):
    pass


class GenerationError(OllamaError):
    pass
