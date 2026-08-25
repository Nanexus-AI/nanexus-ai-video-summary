# Resource profiles

| Profile | Minimum | Load/cache | Network/secrets | Behavior and acceptance |
|---|---|---|---|---|
| Stub default | 2 CPU, 2 GiB RAM, 5 GiB | immediate/no weights | no external model/key | deterministic, GPU-free; `MODEL_PROVIDER=stub MODEL_BUILD_PROFILE=stub` |
| CPU OpenCLIP | 4 CPU, 8 GiB, 15 GiB | first load minutes; mounted `/root/.cache` | initial weight download | semantic embeddings; `MODEL_BUILD_PROFILE=openclip AI_DEVICE=cpu` |
| GPU OpenCLIP | 4 CPU, 8 GiB, 20 GiB, NVIDIA 8 GiB VRAM | same cache; compatible CUDA/driver | initial download; explicit GPU override | accelerated; `AI_DEVICE=cuda`; failure affects only Video Summary |
| Optional Cloud LLM | 2 CPU, 4 GiB, 5 GiB | provider cold start | explicit LLM mode, outbound TLS, secret | bounded text context only; no media/raw Evidence; fallback rule/extractive |

OpenCLIP defaults to `ViT-B-32`/`openai`, downloaded by `open-clip-torch`. Before production, record cached artifact SHA-256, mount it read-only, and review upstream OpenAI/OpenCLIP weight terms. CUDA/cloud do not contaminate Stub. Cloud is opt-in and never receives credentials, media, full Evidence, or chain-of-thought by default.
