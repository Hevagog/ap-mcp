import importlib.util
import sys
import types
from pathlib import Path


def load_module(path: Path, name: str) -> types.ModuleType:
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None:
        raise ImportError(f"Cannot load module {name} from {path}")

    mod = importlib.util.module_from_spec(spec)
    loader = spec.loader
    if loader is None:
        raise ImportError(f"Cannot load module {name} from {path}")

    loader.exec_module(mod)
    return mod


def test_add_basic() -> None:
    top = Path(__file__).resolve().parents[1]
    svc_path = top / "tools" / "calculator_tool" / "src" / "service.py"
    stub = types.ModuleType("tool_sdk")
    stub.mcp_tool = lambda **kwargs: (lambda f: f)  # type: ignore[attr-defined]
    stub.create_app = lambda *a, **k: None  # type: ignore[attr-defined]
    sys.modules["tool_sdk"] = stub

    mod = load_module(svc_path, "calculator_service")
    assert mod.add(1, 2) == 3
    assert mod.add(-1, 1) == 0
