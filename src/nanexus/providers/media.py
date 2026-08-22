"""Defense-in-depth validation for bytes obtained from the public Evidence API."""

from io import BytesIO

from nanexus.event_intelligence_client import EvidenceContent
from nanexus.providers.base import ProviderAbstained

ALLOWED_IMAGE_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})


def validate_image_evidence(
    evidence: EvidenceContent, *, maximum_bytes: int
) -> bytes:
    if evidence.content_type not in ALLOWED_IMAGE_TYPES:
        raise ProviderAbstained(
            "unsupported_media_type", "Evidence Content-Type is not an allowed image"
        )
    if not evidence.content:
        raise ProviderAbstained("empty_evidence", "Evidence image is empty")
    if len(evidence.content) > maximum_bytes:
        raise ProviderAbstained(
            "evidence_too_large", "Evidence image exceeds the configured byte limit"
        )
    try:
        from PIL import Image, UnidentifiedImageError

        image = Image.open(BytesIO(evidence.content))
        image.verify()
    except (UnidentifiedImageError, OSError, ValueError) as error:
        raise ProviderAbstained(
            "image_decode_failed", "Evidence is not a decodable image"
        ) from error
    return evidence.content
