"""Authoritative Video Summary public application paths.

Clients must not be given Event Intelligence internal processor evidence URLs.
Evidence is opened only through the job-scoped Search evidence proxy.
Subjects/citations use the public subject redirect boundary, which targets Event
Intelligence's canonical ReviewItem route (`/api/v1/review-items/{id}`).
"""

from __future__ import annotations

from uuid import UUID

SubjectId = str | UUID
JobId = str | UUID
EvidenceId = str | UUID

SUBJECT_PATH_TEMPLATE = "/api/v1/subjects/{subject_id}"
EVIDENCE_PROXY_PATH_TEMPLATE = "/api/v1/search/evidence/{job_id}/{evidence_id}"
EVENT_INTELLIGENCE_REVIEW_ITEM_PATH_TEMPLATE = "/api/v1/review-items/{review_item_id}"


def subject_path(subject_id: SubjectId) -> str:
    return SUBJECT_PATH_TEMPLATE.format(subject_id=subject_id)


def event_intelligence_review_item_path(review_item_id: SubjectId) -> str:
    return EVENT_INTELLIGENCE_REVIEW_ITEM_PATH_TEMPLATE.format(review_item_id=review_item_id)


def evidence_proxy_path(job_id: JobId, evidence_id: EvidenceId) -> str:
    return EVIDENCE_PROXY_PATH_TEMPLATE.format(job_id=job_id, evidence_id=evidence_id)


def evidence_proxy_url(public_base_url: str, job_id: JobId, evidence_id: EvidenceId) -> str:
    return f"{public_base_url.rstrip('/')}{evidence_proxy_path(job_id, evidence_id)}"


def event_intelligence_review_item_url(public_ei_base_url: str, review_item_id: SubjectId) -> str:
    return f"{public_ei_base_url.rstrip('/')}{event_intelligence_review_item_path(review_item_id)}"
