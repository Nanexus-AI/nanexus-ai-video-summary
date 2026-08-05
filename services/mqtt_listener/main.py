from __future__ import annotations

import json
import logging
import signal
import sys
import time
from typing import Any

import paho.mqtt.client as mqtt
from sqlalchemy import select

from nanexus.config import get_settings
from nanexus.db import SessionLocal, init_db
from nanexus.frigate import parse_frigate_event
from nanexus.models import Event
from nanexus.queue import AIJob, AIQueue

logging.basicConfig(
    level=get_settings().log_level,
    format="%(asctime)s %(levelname)s [mqtt_listener] %(message)s",
)
logger = logging.getLogger("mqtt_listener")

_running = True


def _handle_signal(signum: int, frame: Any) -> None:
    global _running
    logger.info("signal %s received, shutting down", signum)
    _running = False


def upsert_event(payload: dict[str, Any]) -> Event | None:
    parsed = parse_frigate_event(payload)
    if not parsed:
        logger.debug("ignored payload: %s", payload)
        return None

    queue = AIQueue()
    db = SessionLocal()
    try:
        event = db.scalar(select(Event).where(Event.frigate_id == parsed["frigate_id"]))
        if event:
            event.camera = parsed["camera"]
            event.label = parsed["label"]
            event.sub_label = parsed.get("sub_label")
            event.start_time = parsed["start_time"]
            event.end_time = parsed.get("end_time")
            event.snapshot_uri = parsed.get("snapshot_uri") or event.snapshot_uri
            event.clip_uri = parsed.get("clip_uri") or event.clip_uri
            event.raw_payload = parsed.get("raw_payload")
        else:
            event = Event(
                frigate_id=parsed["frigate_id"],
                camera=parsed["camera"],
                label=parsed["label"],
                sub_label=parsed.get("sub_label"),
                start_time=parsed["start_time"],
                end_time=parsed.get("end_time"),
                snapshot_uri=parsed.get("snapshot_uri"),
                clip_uri=parsed.get("clip_uri"),
                status="pending",
                raw_payload=parsed.get("raw_payload"),
            )
            db.add(event)

        db.commit()
        db.refresh(event)

        # Dedup enqueue by frigate_id for M0.
        if event.status in ("pending", "failed") and queue.mark_processed(event.frigate_id):
            queue.enqueue(
                AIJob(
                    event_id=event.id,
                    frigate_id=event.frigate_id,
                    snapshot_uri=event.snapshot_uri,
                )
            )
            event.status = "queued"
            db.add(event)
            db.commit()
            logger.info(
                "enqueued event id=%s frigate_id=%s camera=%s label=%s",
                event.id,
                event.frigate_id,
                event.camera,
                event.label,
            )
        return event
    finally:
        db.close()


def on_connect(
    client: mqtt.Client,
    userdata: Any,
    flags: Any,
    reason_code: Any,
    properties: Any = None,
) -> None:
    settings = get_settings()
    logger.info("connected to MQTT rc=%s, subscribing %s", reason_code, settings.mqtt_topic)
    client.subscribe(settings.mqtt_topic)


def on_message(client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage) -> None:
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except Exception:
        logger.exception("invalid JSON on %s", msg.topic)
        return
    try:
        upsert_event(payload)
    except Exception:
        logger.exception("failed to process event")


def main() -> None:
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    settings = get_settings()
    init_db()
    logger.info("DB ready; connecting MQTT %s:%s", settings.mqtt_host, settings.mqtt_port)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="nanexus-mqtt-listener")
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(settings.mqtt_host, settings.mqtt_port, keepalive=60)
    client.loop_start()

    try:
        while _running:
            time.sleep(0.5)
    finally:
        client.loop_stop()
        client.disconnect()
        logger.info("stopped")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        logger.exception("fatal error")
        sys.exit(1)
