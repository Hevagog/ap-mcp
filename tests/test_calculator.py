from pathlib import Path
import importlib.util
import sys
import types


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_add_basic():
    top = Path(__file__).resolve().parents[1]
    svc_path = top / "tools" / "calculator_tool" / "src" / "service.py"
    stub = types.ModuleType("tool_sdk")
    stub.mcp_tool = lambda **kwargs: (lambda f: f)
    stub.create_app = lambda *a, **k: None
    sys.modules["tool_sdk"] = stub

    mod = load_module(svc_path, "calculator_service")
    assert mod.add(1, 2) == 3
    assert mod.add(-1, 1) == 0
