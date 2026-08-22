from io import BytesIO

import pytest
from PIL import Image

from nanexus.event_intelligence_client import EvidenceContent
from nanexus.providers.base import ProviderAbstained
from nanexus.providers.media import validate_image_evidence


def image_bytes() -> bytes:
    output = BytesIO()
    Image.new("RGB", (2, 2), "blue").save(output, format="PNG")
    return output.getvalue()


def test_accepts_bounded_decodable_evidence() -> None:
    content = image_bytes()
    assert (
        validate_image_evidence(
            EvidenceContent(content=content, content_type="image/png"),
            maximum_bytes=len(content),
        )
        == content
    )


@pytest.mark.parametrize(
    ("content", "content_type", "maximum", "code"),
    [
        (b"x", "text/html", 10, "unsupported_media_type"),
        (b"", "image/jpeg", 10, "empty_evidence"),
        (b"xx", "image/jpeg", 1, "evidence_too_large"),
        (b"not-an-image", "image/jpeg", 100, "image_decode_failed"),
    ],
)
def test_rejects_unsafe_or_invalid_media(
    content: bytes, content_type: str, maximum: int, code: str
) -> None:
    with pytest.raises(ProviderAbstained) as caught:
        validate_image_evidence(
            EvidenceContent(content=content, content_type=content_type),
            maximum_bytes=maximum,
        )
    assert caught.value.code == code
