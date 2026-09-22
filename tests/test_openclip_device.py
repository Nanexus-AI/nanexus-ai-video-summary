import pytest

from nanexus.providers.base import ProviderError
from nanexus.providers.device import CudaUnavailableError, resolve_inference_device
from nanexus.providers.openclip import OpenCLIPProvider


def test_auto_device_uses_cpu_when_cuda_is_unavailable() -> None:
    assert resolve_inference_device("auto", cuda_available=False) == "cpu"


def test_auto_device_uses_cuda_when_available() -> None:
    assert resolve_inference_device("auto", cuda_available=True) == "cuda"


def test_cpu_device_stays_cpu_even_when_cuda_is_available() -> None:
    assert resolve_inference_device("cpu", cuda_available=True) == "cpu"


def test_explicit_cuda_rejects_unavailable_runtime() -> None:
    with pytest.raises(CudaUnavailableError, match="AI_DEVICE=cuda"):
        resolve_inference_device("cuda", cuda_available=False)


def test_openclip_explicit_cuda_does_not_fall_back_to_cpu(monkeypatch) -> None:
    import sys
    import types

    torch_mod = types.ModuleType("torch")
    torch_mod.cuda = types.SimpleNamespace(is_available=lambda: False)
    torch_mod.version = types.SimpleNamespace(cuda=None)
    open_clip_mod = types.ModuleType("open_clip")
    open_clip_mod.get_model_config = lambda _name: {"quick_gelu": True}
    open_clip_mod.get_pretrained_cfg = lambda _model, _pretrained: {"quick_gelu": True}

    def _forbidden_load(*_args, **_kwargs):
        raise AssertionError("OpenCLIP must not load weights after CUDA rejection")

    open_clip_mod.create_model_and_transforms = _forbidden_load
    monkeypatch.setitem(sys.modules, "torch", torch_mod)
    monkeypatch.setitem(sys.modules, "open_clip", open_clip_mod)

    provider = OpenCLIPProvider(
        model="ViT-B-32-quickgelu", pretrained="openai", device="cuda"
    )
    with pytest.raises(ProviderError) as caught:
        provider._load()
    assert caught.value.code == "cuda_unavailable"
    assert not caught.value.retryable
    capabilities = provider.runtime_capabilities()
    assert capabilities["requested_device"] == "cuda"
    assert capabilities["cuda_available"] is False
    assert capabilities["torch_cuda_build"] is None
