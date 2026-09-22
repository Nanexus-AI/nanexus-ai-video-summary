"""Inference-device selection shared by OpenCLIP provider paths."""

from __future__ import annotations

ALLOWED_DEVICES = frozenset({"auto", "cpu", "cuda"})


class CudaUnavailableError(RuntimeError):
    """Raised when CUDA is explicitly requested but is not available."""


def resolve_inference_device(requested: str, *, cuda_available: bool) -> str:
    """Resolve ``auto``/``cpu``/``cuda`` without silently falling back.

    ``auto`` may select CPU when CUDA is absent. Explicit ``cuda`` must not.
    """
    device = requested.strip().lower()
    if device not in ALLOWED_DEVICES:
        raise ValueError("AI_DEVICE must be 'cpu', 'cuda', or 'auto'")
    if device == "auto":
        return "cuda" if cuda_available else "cpu"
    if device == "cuda" and not cuda_available:
        raise CudaUnavailableError(
            "AI_DEVICE=cuda requires a CUDA-enabled PyTorch build and a visible GPU"
        )
    return device
