from pathlib import Path
import importlib.util


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_build_manifest_from_strings():
    top = Path(__file__).resolve().parents[1]
    manifest_path = top / "tool_sdk" / "src" / "tool_sdk" / "core" / "manifest.py"
    mod = load_module(manifest_path, "tool_sdk_manifest")
    build_manifest = mod.build_manifest

    m = build_manifest(name="t", base_url="http://x", methods=["a", "b"])
    assert m.name == "t"
    assert len(m.methods) == 2
    assert all(hasattr(mm, "name") for mm in m.methods)


def test_build_manifest_with_methodspec():
    top = Path(__file__).resolve().parents[1]
    manifest_path = top / "tool_sdk" / "src" / "tool_sdk" / "core" / "manifest.py"
    mod = load_module(manifest_path, "tool_sdk_manifest2")
    build_manifest = mod.build_manifest
    MethodSpec = mod.MethodSpec

    ms = MethodSpec(name="x", description="d")
    m = build_manifest(name="t2", base_url="http://y", methods=[ms])
    assert isinstance(m.methods[0], MethodSpec)
    assert m.methods[0].description == "d"
