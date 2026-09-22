# Stage 6F-2 CPU OpenCLIP validation

Date: 2026-09-20
Final verdict: **PASS**
Gate 6F-2 recommendation: **PASS**

## Executive summary

The intended public candidate successfully ran the real Nanexus OpenCLIP provider and model
service on CPU with deterministic synthetic data. The approved
`ViT-B-32-quickgelu`/`openai` model acquired into a dedicated disposable cache, produced valid
512-dimensional embeddings, repeated exactly, reloaded successfully in supported offline mode,
and supplied a persisted embedding and query to the application semantic-search path. No Stub
fallback or CUDA runtime was used. Model weights, environments, databases, and generated caches
remained outside public source and were removed after evidence capture.

## Candidate and environment identity

- Source branch/base HEAD: `main`, `da3b7c6eb32160d927ff5101194698478da8b2de`.
- Construction: detached temporary worktree at the base HEAD, complete binary-safe tracked diff
  applied, then every non-ignored public untracked path copied explicitly. Existing ignored
  Stage 9 material, the main `.venv`, runtime state, and user caches were excluded.
- Candidate index/staged state: empty.
- Candidate source files: 233.
- Candidate manifest SHA-256 before and after verification:
  `fb5afb3f1f9cad4cc764ee2d58540613d7cdc80b2390f49e90ee696892f236e8`.
- Python: `3.12.3`; uv: `0.11.7`; architecture: `x86_64`; visible logical CPUs: 16.
- Observed host memory at preflight: about 28.2 GiB total and 24.9 GiB available.
- `pyproject.toml` SHA-256:
  `29b8e8e4d2d7c48a0ba6f3cc72cb544d2a6c19335ffc191d45185d96f1062b8b`.
- `uv.lock` SHA-256:
  `7dcc3cb59bb03d2d36a1bbd2cf90e8a9fdd1032b22f9b26e29d9e23803b9b81d`.

## CPU, Torch, and OpenCLIP environment

`uv lock --check` passed, followed by a fresh candidate-external installation with
`uv sync --frozen --extra test --extra openclip`. A fresh, dedicated uv cache was used and
package-index access was required. The frozen install resolved 68 packages and installed 64.
No dependency metadata changed; the lock check and both dependency-file hashes remained
identical after execution.

The runtime reported:

- `torch==2.13.0+cpu`;
- `torchvision==0.28.0+cpu`;
- `open-clip-torch==3.3.0` (`open_clip.__version__ == 3.3.0`);
- `torch.version.cuda is None`;
- `torch.cuda.is_available() is False` and device count is zero;
- selected and reported provider device: `cpu`.

No CUDA/GPU inference, CUDA wheel, or GPU-specific host state was used.

## Model acquisition and isolated cache

The requested model was `ViT-B-32-quickgelu` with pretrained identifier `openai`. First use
required public network access and succeeded without substitution. The provider initialized
healthy and identified itself as `openclip`, model `ViT-B-32-quickgelu`, version
`openai+security-camera-en-v1+cpu+3.3.0`, device `cpu`; no Stub fallback occurred.

All Hugging Face, OpenCLIP/Torch, and XDG cache variables were redirected to one dedicated
temporary cache tree outside the candidate and outside the user's normal caches. At capture it
contained six regular runtime/cache files totaling 605,201,745 bytes (about 577.17 MiB). The
single model blob was 605,143,284 bytes. No cache path or weight entered the repository.

## Real CPU inference and embedding validity

A deterministic generated 224x224 RGB PNG (5,076 bytes, SHA-256
`29f05dac57bd7efde3bfec3da512a43243ab729097c5492fa6a534975ba5bb8d`) was passed through the
actual `nanexus.providers.openclip.OpenCLIPProvider`. Image preprocessing and zero-shot analysis
succeeded. The image embedding was non-empty, non-zero, entirely finite, 512-dimensional, and
had observed norm `0.9999999`. A real text embedding was also finite and 512-dimensional.

The generated zero-shot result identified the real OpenCLIP provider and returned three labels.
The result hash was
`42e5a0631adcc237858139129da1327154e4d0f4bc402508a64441cc581b496a`.

## Repeatability and offline rerun

Two successive image inferences in the same loaded provider were bit-for-bit identical:
dimensionality remained 512 and maximum absolute difference was `0.0`. The second inference did
not redownload the model.

A new process then set `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`, retained only the
dedicated acquired model cache as the model-artifact source, and initialized the same project
provider again. Model initialization and synthetic inference succeeded, producing the same
512 dimensions and the identical result hash. The complete cache-file fingerprint was unchanged
before and after (`879240c51cd2930ce935ea93a996cc3c467e327193b5662582ab06bf86cd0b28`).

An OS network namespace was attempted as an additional block, but this host denied namespace
creation with `Operation not permitted`. The supported Hugging Face offline controls, clean
process restart, successful cache-only load, and unchanged cache fingerprint provide the
offline-rerun evidence; this host limitation is recorded rather than hidden.

## Application provider and downstream semantic search

The actual Nanexus model-service application was started through its FastAPI lifecycle with
`MODEL_PROVIDER=openclip`, the approved model tuple, and `AI_DEVICE=cpu`. Startup warmed the real
provider from the isolated cache. `/health` returned `status=ok`, and
`POST /v1/embeddings/text` returned HTTP 200 with provider `openclip`, the approved model,
CPU-bearing model version, 512 finite/non-zero values, and observed norm `0.99999997`. This
exercised the project factory, configuration, provider, startup, and HTTP response boundary.

For the bounded downstream proof, a fresh disposable PostgreSQL/pgvector database was migrated
to project head. One synthetic real image embedding was persisted as an application-owned
`EmbeddingRecord`; its stored provider/model/version and 512 dimensions matched the active
provider. A real OpenCLIP text embedding was supplied to `nanexus.semantic_search.semantic_search`.
The project query returned the synthetic review item as its single hit with observed cosine
similarity `0.2560`. This proves the required chain:

`real CPU OpenCLIP -> application embedding record -> pgvector semantic retrieval`.

Summary and Chat were not rerun because this stage's bounded objective was embedding consumption,
and their OpenCLIP-independent integration was already covered by Stage 6F-1.

## Resource observations

These are observations from one host, not performance commitments:

- acquired cache: about 577.17 MiB;
- first model initialization including acquisition: about 16.88 seconds;
- first image inference after initialization: about 0.206 seconds;
- repeated image inference: about 0.029 seconds;
- text inference: about 0.018 seconds;
- offline cached initialization: about 2.24 seconds;
- offline image inference: about 0.209 seconds;
- observed peak RSS for the instrumented acquisition/inference process: about 1.55 GiB.

## Cache and provenance observations

OpenCLIP's exposed pretrained configuration named Hugging Face source
`timm/vit_base_patch32_clip_224.openai` and also exposed the upstream OpenAI AzureEdge
`ViT-B-32.pt` URL with its content-addressed path. This run populated the Hugging Face cache
repository `timm/vit_base_patch32_clip_224.openai`, artifact name
`open_clip_model.safetensors`, revision
`a6f597a30f7b82c51704746581f9a4e41421e878`, with blob identifier
`e6d1bd7789aa45192b3bf90570a789b478bae1b74ebcce7eddd908e83a2b7c31`.

The cache is classified as a disposable private runtime artifact. These observations identify
the acquisition mechanism and revision only; they do not make a new redistribution-license
claim and no artifact is bundled.

## Pollution audit and cleanup

The final candidate manifest equaled the pre-run manifest. No weight, model cache, database,
log, virtual environment, or generated test artifact appeared in candidate source. Python
`__pycache__` directories created by imports were confined to the disposable candidate.
`pyproject.toml`, `uv.lock`, and the candidate index remained unchanged.

The disposable pgvector container/database, detached worktree, Python environment, uv cache,
model cache, and generated bytecode were removed after capture. The main worktree remained at
the same HEAD with an empty index and its pre-existing dirty public-candidate state preserved.
This evidence document is the only intended main-worktree addition from Stage 6F-2. No file was
staged, committed, or pushed.

## Limitations and gate recommendation

The synthetic fixture is controlled validation data, not a quality evaluation. Timings and
memory are single-host observations and must not be published as product-performance promises.
The host disallowed a separate network namespace, as documented above; supported offline mode
still completed from the isolated cache with an unchanged fingerprint. No CUDA/GPU result,
real camera, model redistribution, or unrelated Summary/Chat rerun is claimed.

All twelve Stage 6F-2 pass criteria are satisfied. **Stage 6F-2 verdict: PASS. Gate 6F-2
recommendation: PASS.**
