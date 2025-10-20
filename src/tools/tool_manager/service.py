from core.registry import registry


@registry.tool()
def random_value() -> float:
    import random

    return random.random()
