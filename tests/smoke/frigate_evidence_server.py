"""Synthetic, credential-free Frigate snapshot endpoint for Compose smoke tests."""

import struct
import zlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

def chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))


def fixture_png() -> bytes:
    width = height = 224
    rows = []
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            color = (216, 232, 240)
            if 72 <= x <= 150 and 36 <= y <= 190:
                color = (187, 32, 32)
            if 22 <= x <= 68 and 150 <= y <= 198:
                color = (155, 106, 50)
            row.extend(color)
        rows.append(bytes(row))
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(b"".join(rows), 9))
        + chunk(b"IEND", b"")
    )


IMAGE = fixture_png()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path != "/api/events/object-1/snapshot.jpg":
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header("Content-Type", "image/png")
        self.send_header("Content-Length", str(len(IMAGE)))
        self.end_headers()
        self.wfile.write(IMAGE)

    def log_message(self, _format: str, *_args: object) -> None:
        return


ThreadingHTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
