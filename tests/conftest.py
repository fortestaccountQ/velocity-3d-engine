import sys
import os
import gc
import pytest

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
python_dir = os.path.join(repo_root, "python")
if python_dir not in sys.path:
    sys.path.insert(0, python_dir)
if repo_root not in sys.path:
    sys.path.insert(1, repo_root)


@pytest.fixture(autouse=True)
def clean_gc_after_test():
    """Ensure cyclic garbage is cleanly collected after each test to prevent nanobind leak warnings."""
    yield
    try:
        from pielosyty.tween import TweenManager
        TweenManager.default().clear()
    except Exception:
        pass
    gc.collect()


@pytest.fixture(scope="session", autouse=True)
def clean_session_state():
    """Tear down any lingering module-level apps, textures, or singletons upon session completion."""
    yield
    for mod_name in list(sys.modules.keys()):
        if mod_name.startswith("examples."):
            mod = sys.modules.pop(mod_name, None)
            if mod is not None:
                if hasattr(mod, "app"):
                    try:
                        mod.app.close()
                    except Exception:
                        pass
                try:
                    mod.__dict__.clear()
                except Exception:
                    pass
    try:
        from examples.crossy_duck import world
        world.clear_default_material_registry()
    except Exception:
        pass
    gc.collect()

