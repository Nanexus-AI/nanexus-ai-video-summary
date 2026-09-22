"""Repeatable MODEL-006 CPU baseline using a generated non-private fixture."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import resource
import statistics
import time
from io import BytesIO

from PIL import Image, ImageDraw

from nanexus.providers.openclip import OpenCLIPProvider


def fixture_image() -> bytes:
    image = Image.new("RGB", (224, 224), "#d8e8f0")
    draw = ImageDraw.Draw(image)
    draw.rectangle((72, 36, 150, 190), fill="#bb2020")
    draw.ellipse((88, 16, 134, 62), fill="#d0a070")
    draw.rectangle((22, 150, 68, 198), fill="#9b6a32")
    output = BytesIO()
    image.save(output, format="PNG", optimize=False)
    return output.getvalue()


async def benchmark(runs: int) -> dict[str, object]:
    image = fixture_image()
    provider = OpenCLIPProvider(
        model="ViT-B-32-quickgelu", pretrained="openai", device="cpu"
    )
    started = time.perf_counter()
    await provider.warmup(timeout_seconds=300)
    startup_seconds = time.perf_counter() - started
    image_latencies: list[float] = []
    results = []
    for _ in range(runs):
        started = time.perf_counter()
        results.append(await provider.analyze_image(image, timeout_seconds=300))
        image_latencies.append(time.perf_counter() - started)
    text_latencies: list[float] = []
    text_vectors = []
    for _ in range(runs):
        started = time.perf_counter()
        text_vectors.append(
            await provider.embed_text("person wearing red clothes", timeout_seconds=300)
        )
        text_latencies.append(time.perf_counter() - started)
    return {
        "fixture_sha256": hashlib.sha256(image).hexdigest(),
        "fixture_description": "generated geometric person/package-like synthetic image",
        "identity": provider.identity.__dict__,
        "startup_seconds": round(startup_seconds, 4),
        "image_latency_seconds": [round(value, 4) for value in image_latencies],
        "image_latency_median_seconds": round(statistics.median(image_latencies), 4),
        "text_latency_seconds": [round(value, 4) for value in text_latencies],
        "text_latency_median_seconds": round(statistics.median(text_latencies), 4),
        "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
        "result_hashes": [item.result_hash for item in results],
        "stable": len({item.result_hash for item in results}) == 1,
        "tags": list(results[0].tags),
        "confidence": round(results[0].confidence or 0, 6),
        "embedding_dimensions": len(results[0].image_embedding),
        "text_embedding_dimensions": len(text_vectors[0]),
        "text_stable": len(set(text_vectors)) == 1,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=3, choices=range(1, 11))
    args = parser.parse_args()
    print(json.dumps(asyncio.run(benchmark(args.runs)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
