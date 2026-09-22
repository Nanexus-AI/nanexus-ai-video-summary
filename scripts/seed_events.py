#!/usr/bin/env python3
"""Publish sample Frigate-like MQTT events with local demo snapshots for M1."""

from __future__ import annotations

import argparse
import json
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

import paho.mqtt.client as mqtt
from PIL import Image, ImageDraw, ImageFont

from nanexus.config import get_settings
from nanexus.media import local_snapshot_path, snapshots_dir

SAMPLES = [
    {
        "camera": "front_door",
        "label": "person",
        "sub_label": None,
        "has_clip": True,
        "color": (200, 40, 40),
        "text": "RED CLOTHES PERSON",
    },
    {
        "camera": "driveway",
        "label": "car",
        "sub_label": "black SUV",
        "has_clip": True,
        "color": (20, 20, 20),
        "text": "BLACK SUV",
    },
    {
        "camera": "garage",
        "label": "person",
        "sub_label": "delivery",
        "has_clip": False,
        "color": (40, 120, 220),
        "text": "DELIVERY PERSON",
    },
    {
        "camera": "driveway",
        "label": "package",
        "sub_label": "courier",
        "has_clip": True,
        "color": (180, 140, 40),
        "text": "COURIER DELIVERY VAN",
    },
    {
        "camera": "backyard",
        "label": "dog",
        "sub_label": None,
        "has_clip": False,
        "color": (120, 80, 40),
        "text": "DOG IN YARD",
    },
]


def render_snapshot(path: Path, color: tuple[int, int, int], text: str) -> None:
    img = Image.new("RGB", (640, 360), color=color)
    draw = ImageDraw.Draw(img)
    draw.rectangle((40, 40, 600, 320), outline=(255, 255, 255), width=4)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
    draw.text((60, 160), text, fill=(255, 255, 255), font=font)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, format="JPEG", quality=90)


def build_payload(sample: dict, event_id: str, snapshot_uri: str) -> dict:
    now = datetime.now(tz=UTC).timestamp()
    return {
        "type": "new",
        "before": None,
        "after": {
            "id": event_id,
            "camera": sample["camera"],
            "label": sample["label"],
            "sub_label": sample["sub_label"],
            "start_time": now,
            "end_time": None,
            "has_snapshot": True,
            "has_clip": sample["has_clip"],
            "false_positive": False,
            # Override Frigate default URI with local demo media.
            "snapshot_uri": snapshot_uri,
            "clip_uri": (
                f"{get_settings().frigate_base_url.rstrip('/')}/api/events/{event_id}/clip.mp4"
                if sample["has_clip"]
                else None
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo Frigate MQTT events")
    parser.add_argument("-n", "--count", type=int, default=len(SAMPLES), help="number of events")
    parser.add_argument("--delay", type=float, default=0.3, help="delay between publishes")
    args = parser.parse_args()

    settings = get_settings()
    snapshots_dir()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="nanexus-seed")
    client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=30)
    client.loop_start()

    published = 0
    try:
        for i in range(args.count):
            sample = SAMPLES[i % len(SAMPLES)]
            event_id = str(uuid.uuid4())
            path = local_snapshot_path(event_id)
            render_snapshot(path, sample["color"], sample["text"])
            # Prefer file:// so AI worker does not depend on API being up.
            snapshot_uri = path.resolve().as_uri()
            payload = build_payload(sample, event_id, snapshot_uri)
            # Also expose HTTP media path for clients via public_base_url mapping.
            payload["after"]["snapshot_uri"] = snapshot_uri
            payload["after"]["http_snapshot_uri"] = (
                f"{settings.public_base_url.rstrip('/')}/media/snapshots/{event_id}.jpg"
            )

            client.publish(settings.mqtt_topic, json.dumps(payload), qos=1)
            published += 1
            print(
                f"published {published}: {sample['camera']} / {sample['label']} -> {path.name}"
            )
            time.sleep(args.delay)
    finally:
        client.loop_stop()
        client.disconnect()

    print(f"done: published {published} events to {settings.mqtt_topic}")
    print(f"snapshots dir: {snapshots_dir().resolve()}")


if __name__ == "__main__":
    main()
