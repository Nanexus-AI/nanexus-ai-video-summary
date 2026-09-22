# Stage 6F-3 GPU/CUDA clean-candidate re-verification

Date: 2026-09-20
Final verdict: **PASS**
Gate 6F-3 recommendation: **PASS**

## Executive summary

The corrected GPU-specific profile passed final hardware validation on an NVIDIA GeForce RTX
5060 Ti. A fresh isolated public candidate preserved the CPU-only profile, built the separate
CUDA image with the locked cu130 wheels, exposed exactly one NVIDIA GPU through the Compose
overlay, loaded real `ViT-B-32-quickgelu`/`openai`, and performed real Nanexus OpenCLIP
inference with model parameters and input tensors on CUDA. The normalized 512-dimensional result
agreed strongly with an exact-input CPU reference and completed the application
persistence/pgvector/semantic-search chain. Recreate and supported offline-cache startup passed.
No Stub or CPU fallback occurred.

## Candidate identity

- Source branch/base HEAD: `main`, `da3b7c6eb32160d927ff5101194698478da8b2de`.
- A detached worktree at that HEAD received the binary-safe tracked patch and all 58 non-ignored
  public untracked files individually. Ignored Stage 9 material, `.env`, host environments,
  runtime data, and existing model caches were excluded.
- Tracked patch SHA-256: `82a945d0c12975987235af37d72489cf8d2c1f92209911e819791a1b26e6fa8c`.
- Manifest: 215 files (129 HEAD, 28 tracked-patch, 58 allowlisted untracked); SHA-256
  `ec9e168695decd3bb66f109e271a897d5f0c74aaa17cac8e29af37bc5acbef92`.
- Candidate and main-worktree indexes were empty. Nothing was staged, committed, or pushed.
- Docker client/server: 29.1.3; Compose: 2.32.4; uv: 0.11.7; Python: 3.12.3.
- Candidate hashes: `pyproject.toml`
  `35a168f4eadfd3c4742f29b903d4fa81c9926a26c66005ced82ffa9fac55d151`; `uv.lock`
  `1c2dd70827b8722f5a5fb93a30fce85f542dbdf592eb952becb6e091e0b25dec`; `.dockerignore`
  `52fc0c35c6a9d19194f2d324e3afb6ff1eecd5831671c913c4bc91c368c19b1a`.

## CPU regression result

**PASS.** In a fresh candidate-external environment/cache, `uv lock --check` and
`uv sync --frozen --extra test --extra openclip` succeeded. Runtime identity was
`torch==2.13.0+cpu`, `torchvision==0.28.0+cpu`, `torch.version.cuda is None`, CUDA unavailable,
and device count zero. The CPU route required no NVIDIA reservation or device.

## Host driver and container-runtime result

**PASS.** Host and disposable CUDA-container observations were:

- NVIDIA GeForce RTX 5060 Ti; driver 595.84; driver-supported CUDA 13.2;
- 16,311 MiB total memory; compute capability 12.0;
- NVIDIA Container Toolkit/CLI 1.20.0;
- NVIDIA runtime registered while ordinary `runc` remained the default.

`nvidia/cuda:13.0.2-base-ubuntu24.04` with `--gpus all` saw the same hardware. No host CUDA
toolkit or host CUDA Python package was installed.

## GPU image metadata and CUDA visibility

**PASS.** A clean `--no-cache --pull` build used only the 394 kB approved context. Image ID
`sha256:8559979affa5259c6387eb63d0a57cbaa2edbc1e8be57664b2de77cab8c34081` reported:

- `torch==2.13.0+cu130`;
- `torchvision==0.28.0+cu130`;
- `open_clip==3.3.0`;
- `torch.version.cuda == "13.0"`.

A Compose/BuildKit build independently resolved the same CUDA environment. In NVIDIA runtime,
CUDA was available, device count was one, device name was RTX 5060 Ti, and capability was `(12,
0)`. A synchronized tensor allocated on `cuda:0` and returned the expected operation result
`17.0`. No Hugging Face model directory/blob was baked into the image. The five `.pth` suffix
files were 9-151 byte Python path-configuration text files, not weights.

## Nanexus GPU service/device result

**PASS.** The actual release + GPU Compose overlay started with exactly one NVIDIA reservation.
`/health` returned status `ok`, provider `openclip`, model `ViT-B-32-quickgelu`, requested and
actual device `cuda`, CUDA available true, and Torch CUDA build `13.0`. The HTTP embedding model
version was `openai+security-camera-en-v1+cuda+3.3.0`, excluding Stub and CPU fallback.

## Model acquisition and isolated cache result

**PASS.** Primary startup used new volume `nanexus6f3_model-cache`, separate from Stage 6F-2 and
outside source. Acquisition produced repository `timm/vit_base_patch32_clip_224.openai`, revision
`a6f597a30f7b82c51704746581f9a4e41421e878`, artifact `open_clip_model.safetensors`, and blob
SHA-256 `e6d1bd7789aa45192b3bf90570a789b478bae1b74ebcce7eddd908e83a2b7c31` (605,143,284 bytes).

## Real GPU inference and embedding validity

**PASS.** The actual `OpenCLIPProvider` loaded parameters on `cuda:0` and processed the generated
geometric image on CUDA. Allocated CUDA memory rose from 607,755,264 to 641,311,744 bytes across
the synchronized inference. The vector had 512 finite dimensions, was non-zero, and had norm
`1.0000000046`. Fixture SHA-256 was
`9ef07f90186536548c4764cc80f6a36350096a4336b5193b42fe9a36e82de038` (955 bytes). The service
also returned a finite, non-zero 512-dimensional text vector with norm `1.0000000164`.

## CPU/GPU comparison

**PASS.** Stage 6F-2 retained metrics rather than its raw vector, so this run generated an
exact-input CPU reference with the same code, model, identifier, revision, and runtime:

- cosine similarity: `0.9999998789654755`;
- GPU/CPU norms: `1.0000000046214281` / `0.9999999568826414`;
- maximum/mean absolute differences: `0.00010382384061813354` /
  `0.0000168939047213712`.

No repository tolerance exists. Near-unit cosine, matching norms, and small errors establish
strong CPU/CUDA floating-point agreement without a post-hoc pass threshold.

## Downstream semantic-search result

**PASS.** A fresh disposable pgvector database was migrated to project head. The GPU image vector
was persisted as an application `EmbeddingRecord` with CUDA provider/model/version and 512
dimensions. A real CUDA model-service text query passed to project `semantic_search` returned the
intended synthetic subject as the sole hit with cosine
similarity `0.29030792174888176`. Stored and query identities both reported `openclip` and the
CUDA-bearing model version; no Stub/CPU substitution occurred.

## Restart/recreate and offline-cache result

**PASS.** Compose force-recreated only the GPU model service while retaining the isolated cache.
The new container again became healthy on CUDA and returned a finite normalized 512-vector.
With `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`, startup/inference succeeded, the artifact
hash and revision stayed identical, and the new logs showed no download activity.

## Compose/security regression

**PASS.** All seven focused GPU-profile tests passed. CPU release/search/model/base files contain
no NVIDIA reservation. Release + GPU and search + GPU rendered with provider `openclip`, device
`cuda`, exactly one `driver: nvidia`/`count: 1` reservation, and no model-service host port. CPU
release remained Stub/CPU by default; internal service/security boundaries were unchanged.

## Cleanup and pollution audit

The disposable containers, validation network, model/database volumes, project images, CPU
environment/cache, detached candidate, and temporary files were removed after capture. Public
base images pulled solely for this run were removed when no validation image depended on them.
Shared BuildKit cache was not globally pruned because records cannot safely be attributed to this
run; pruning shared builders could delete unrelated user cache.

The candidate manifest stayed unchanged. No weights, cache, DB, log, GPU artifact, or environment
entered source. The main worktree stayed at the same HEAD with its prior reviewed dirty state and
an empty index.

## Remaining limitations

- Stage 6F-2 did not retain its raw vector. The comparison therefore used a freshly computed
  exact-input CPU reference. Its evidence also records a different PNG byte hash, so this run
  explicitly records and compares identical current-candidate bytes.
- Supported offline flags were proven; a kernel network namespace was not re-attempted after the
  documented Stage 6F-2 host limitation.
- Single-host memory/similarity observations are validation evidence, not performance promises.
- Shared BuildKit caches were preserved to avoid disturbing unrelated resources.

## Verdict and gate recommendation

All fifteen Stage 6F-3 pass criteria are satisfied with the limitations above. **Stage 6F-3
verdict: PASS. Gate 6F-3 recommendation: PASS.**
