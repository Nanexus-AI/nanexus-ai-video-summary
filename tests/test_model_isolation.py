import os
import subprocess
import sys


def test_api_import_does_not_load_torch_or_openclip() -> None:
    environment = dict(os.environ)
    environment["LEGACY_API_MODEL_INFERENCE_ENABLED"] = "false"
    code = (
        "import sys; import services.api.main; "
        "assert 'torch' not in sys.modules; assert 'open_clip' not in sys.modules"
    )
    subprocess.run([sys.executable, "-c", code], check=True, env=environment)


def test_heavy_runtime_is_confined_to_worker_modules() -> None:
    api_source = open("services/api/main.py", encoding="utf-8").read()
    assert "open_clip" not in api_source
    assert "import torch" not in api_source
