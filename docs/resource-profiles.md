# Resource profiles

| Profile | Minimum | Load/cache | Network/secrets | Behavior and acceptance |
|---|---|---|---|---|
| Stub default | 2 CPU, 2 GiB RAM, 5 GiB | immediate/no weights | no external model/key | deterministic, GPU-free; `MODEL_PROVIDER=stub MODEL_BUILD_PROFILE=stub` |
| CPU OpenCLIP | 4 CPU, 8 GiB, 15 GiB | first load minutes; mounted `/root/.cache` | initial weight download | semantic embeddings; `MODEL_BUILD_PROFILE=openclip AI_DEVICE=cpu` |
| GPU OpenCLIP | 4 CPU, 8 GiB, 20 GiB, NVIDIA 8 GiB VRAM | same cache; container CUDA runtime | initial download; NVIDIA driver + NVIDIA Container Toolkit on the host | accelerated; GPU overlay + `AI_DEVICE=cuda`; failure affects only Video Summary |
| Optional Cloud LLM | 2 CPU, 4 GiB, 5 GiB | provider cold start | explicit LLM mode, outbound TLS, secret | bounded text context only; no media/raw Evidence; fallback rule/extractive |

OpenCLIP defaults to the activation-matched `ViT-B-32-quickgelu`/`openai` pair, downloaded by `open-clip-torch`.

The Linux **CPU** profile is the default OpenCLIP path. It uses the `openclip` extra and resolves torch/torchvision only from the explicit PyTorch CPU wheel index. CUDA/NVIDIA/Triton packages are not accepted in that profile. Activate it with `MODEL_BUILD_PROFILE=openclip` and `AI_DEVICE=cpu` on the existing model-worker image. Do not treat this profile as CUDA-capable.

The Linux **GPU/CUDA** profile is a separate container path, not a host Python extra for normal
development. It uses the conflicting `openclip-cuda` extra,
`docker/Dockerfile.model-worker-cuda`, and the `compose.gpu.yaml` overlay. That overlay requests
one NVIDIA GPU and sets `MODEL_PROVIDER=openclip` with `AI_DEVICE=cuda`. CUDA-enabled
Torch/Torchvision wheels are installed inside the GPU image from the PyTorch `cu130` index so
they match PyTorch 2.13's stable CUDA 13.0 build, including Blackwell `12.0+PTX`. The host needs
an NVIDIA driver and NVIDIA Container Toolkit; it does not need a CUDA toolkit or CUDA-enabled
PyTorch. This path passed Stage 6F-3 hardware validation on an RTX 5060 Ti; that result does not
guarantee every driver, toolkit, or GPU combination.

Before production, record cached artifact SHA-256, mount it read-only, and review upstream OpenAI/OpenCLIP weight terms. CUDA/cloud do not contaminate Stub. Cloud is opt-in and never receives credentials, media, full Evidence, or chain-of-thought by default.
