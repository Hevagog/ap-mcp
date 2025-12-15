import importlib.util
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


def test_build_manifest_from_strings() -> None:
    top = Path(__file__).resolve().parents[1]
    manifest_path = top / "tool_sdk" / "src" / "tool_sdk" / "core" / "manifest.py"
    mod = load_module(manifest_path, "tool_sdk_manifest")
    build_manifest = mod.build_manifest

    m = build_manifest(name="t", base_url="http://x", methods=["a", "b"])
    assert m.name == "t"
    assert len(m.methods) == 2
    assert all(hasattr(mm, "name") for mm in m.methods)


def test_build_manifest_with_methodspec() -> None:
    top = Path(__file__).resolve().parents[1]
    manifest_path = top / "tool_sdk" / "src" / "tool_sdk" / "core" / "manifest.py"
    mod = load_module(manifest_path, "tool_sdk_manifest2")
    build_manifest = mod.build_manifest
    method_spec = mod.MethodSpec

    ms = method_spec(name="x", description="d")
    m = build_manifest(name="t2", base_url="http://y", methods=[ms])
    assert isinstance(m.methods[0], method_spec)
    assert m.methods[0].description == "d"
