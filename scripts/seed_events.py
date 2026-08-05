#!/usr/bin/env python3
"""Publish sample Frigate-like MQTT events for local demo (no real Frigate needed)."""

from __future__ import annotations

import argparse
import json
import time
import uuid
from datetime import UTC, datetime

import paho.mqtt.client as mqtt

from nanexus.config import get_settings


SAMPLES = [
    {"camera": "front_door", "label": "person", "sub_label": None, "has_snapshot": True, "has_clip": True},
    {"camera": "driveway", "label": "car", "sub_label": "black SUV", "has_snapshot": True, "has_clip": True},
    {"camera": "garage", "label": "person", "sub_label": "delivery", "has_snapshot": True, "has_clip": False},
    {"camera": "driveway", "label": "package", "sub_label": "UPS", "has_snapshot": True, "has_clip": True},
    {"camera": "backyard", "label": "dog", "sub_label": None, "has_snapshot": True, "has_clip": False},
]


def build_payload(sample: dict) -> dict:
    now = datetime.now(tz=UTC).timestamp()
    event_id = str(uuid.uuid4())
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
            "has_snapshot": sample["has_snapshot"],
            "has_clip": sample["has_clip"],
            "false_positive": False,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo Frigate MQTT events")
    parser.add_argument("-n", "--count", type=int, default=len(SAMPLES), help="number of events")
    parser.add_argument("--delay", type=float, default=0.3, help="delay between publishes")
    args = parser.parse_args()

    settings = get_settings()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="nanexus-seed")
    client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=30)
    client.loop_start()

    published = 0
    try:
        for i in range(args.count):
            sample = SAMPLES[i % len(SAMPLES)]
            payload = build_payload(sample)
            client.publish(settings.mqtt_topic, json.dumps(payload), qos=1)
            published += 1
            print(f"published {published}: {payload['after']['camera']} / {payload['after']['label']}")
            time.sleep(args.delay)
    finally:
        client.loop_stop()
        client.disconnect()

    print(f"done: published {published} events to {settings.mqtt_topic}")


if __name__ == "__main__":
    main()
