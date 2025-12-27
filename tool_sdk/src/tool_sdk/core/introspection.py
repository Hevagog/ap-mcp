import inspect
from typing import Callable, Any, Dict, get_type_hints


def get_function_schema(func: Callable) -> dict[str, Any]:
    """
    Generates a JSON Schema for the arguments of a function.
    """
    type_hints = get_type_hints(func)
    sig = inspect.signature(func)

    properties = {}
    required = []

    for name, param in sig.parameters.items():
        if name == "self" or name == "cls":
            continue

        param_type = type_hints.get(name, Any)
        json_type = "string"  # default

        if param_type == int:
            json_type = "integer"
        elif param_type == float:
            json_type = "number"
        elif param_type == bool:
            json_type = "boolean"
        elif param_type == str:
            json_type = "string"
        elif param_type == list or getattr(param_type, "__origin__", None) == list:
            json_type = "array"
        elif param_type == dict or getattr(param_type, "__origin__", None) == dict:
            json_type = "object"

        prop_schema = {"type": json_type}
        if param.default != inspect.Parameter.empty:
            prop_schema["default"] = param.default
        else:
            required.append(name)

        properties[name] = prop_schema

    return {"type": "object", "properties": properties, "required": required}
