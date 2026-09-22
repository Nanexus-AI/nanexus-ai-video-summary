from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_linux_openclip_extra_stays_on_cpu_index() -> None:
    project = tomllib.loads(_read("pyproject.toml"))
    extras = project["project"]["optional-dependencies"]
    assert extras["openclip"] == [
        "torch>=2.2,<3",
        "torchvision>=0.17,<1",
        "open-clip-torch>=2.26,<4",
    ]
    sources = project["tool"]["uv"]["sources"]
    cpu_torch = [
        source
        for source in sources["torch"]
        if source.get("extra") == "openclip"
    ]
    assert cpu_torch == [
        {"index": "pytorch-cpu", "extra": "openclip", "marker": "sys_platform == 'linux'"}
    ]
    indexes = {index["name"]: index["url"] for index in project["tool"]["uv"]["index"]}
    assert indexes["pytorch-cpu"] == "https://download.pytorch.org/whl/cpu"


def test_openclip_cuda_extra_is_conflicting_and_uses_cu130() -> None:
    project = tomllib.loads(_read("pyproject.toml"))
    extras = project["project"]["optional-dependencies"]
    assert extras["openclip-cuda"] == [
        "torch==2.13.0",
        "torchvision==0.28.0",
        "open-clip-torch>=2.26,<4",
    ]
    conflicts = project["tool"]["uv"]["conflicts"]
    assert [{"extra": "openclip"}, {"extra": "openclip-cuda"}] in conflicts
    sources = project["tool"]["uv"]["sources"]
    cuda_torch = [
        source
        for source in sources["torch"]
        if source.get("extra") == "openclip-cuda"
    ]
    assert cuda_torch == [
        {
            "index": "pytorch-cu130",
            "extra": "openclip-cuda",
            "marker": "sys_platform == 'linux'",
        }
    ]
    indexes = {index["name"]: index["url"] for index in project["tool"]["uv"]["index"]}
    assert indexes["pytorch-cu130"] == "https://download.pytorch.org/whl/cu130"


def test_uv_lock_keeps_linux_cpu_and_cuda_wheels_distinct() -> None:
    lock = _read("uv.lock")
    assert 'version = "2.13.0+cpu"' in lock
    assert 'version = "2.13.0+cu130"' in lock
    assert 'version = "0.28.0+cpu"' in lock
    assert 'version = "0.28.0+cu130"' in lock
    assert "https://download.pytorch.org/whl/cpu" in lock
    assert "https://download.pytorch.org/whl/cu130" in lock
    assert "2.14.0+cu130" not in lock


def test_cpu_model_worker_image_does_not_install_cuda_extra() -> None:
    dockerfile = _read("docker/Dockerfile.model-worker")
    assert "uv sync --frozen --no-dev --extra openclip" in dockerfile
    assert "openclip-cuda" not in dockerfile
    assert "nvidia/cuda" not in dockerfile


def test_gpu_model_worker_image_installs_cuda_extra() -> None:
    dockerfile = _read("docker/Dockerfile.model-worker-cuda")
    assert "FROM nvidia/cuda:13.0.2-base-ubuntu24.04" in dockerfile
    assert "uv sync --frozen --no-dev --extra openclip-cuda" in dockerfile
    assert "--extra openclip;" not in dockerfile
    assert "--extra openclip " not in dockerfile


def test_release_and_cpu_compose_do_not_reserve_nvidia_gpu() -> None:
    for path in (
        "compose.release.yaml",
        "compose.search.yaml",
        "compose.model.yaml",
        "docker-compose.yml",
    ):
        text = _read(path)
        assert "driver: nvidia" not in text
        assert "capabilities: [gpu]" not in text


def test_gpu_compose_overlay_reserves_one_nvidia_gpu_without_host_ports() -> None:
    text = _read("compose.gpu.yaml")
    assert "dockerfile: docker/Dockerfile.model-worker-cuda" in text
    assert "AI_DEVICE: cuda" in text
    assert "MODEL_PROVIDER: openclip" in text
    assert "driver: nvidia" in text
    assert "count: 1" in text
    assert "capabilities: [gpu]" in text
    assert "ports:" not in text
