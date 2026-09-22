"""Synthetic, local-only Frigate media fixture for the CPU Closeout Gate."""

from pathlib import Path

from fastapi import FastAPI, Response

app = FastAPI()
fixture = Path("/fixture/synthetic-residential-camera-demo.png")


@app.get("/api/events/{event_id}/snapshot.jpg")
async def snapshot(event_id: str) -> Response:
    if event_id != "object-1":
        return Response(status_code=404)
    return Response(fixture.read_bytes(), media_type="image/png")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
