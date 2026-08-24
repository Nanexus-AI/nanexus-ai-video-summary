"""Compare legacy Event and public Review Summary behavior on a JSON fixture."""

from __future__ import annotations

import argparse
import json
from datetime import date, datetime
from pathlib import Path
from types import SimpleNamespace

from nanexus.event_intelligence_client import ReviewDetail
from nanexus.summary import compare_legacy_and_review_summaries


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("fixture", type=Path)
    parser.add_argument("--date", required=True, type=date.fromisoformat)
    parser.add_argument("--timezone", required=True)
    args = parser.parse_args()
    payload = json.loads(args.fixture.read_text())
    legacy = []
    for item in payload["legacy_events"]:
        values = dict(item)
        values["start_time"] = datetime.fromisoformat(values["start_time"].replace("Z", "+00:00"))
        legacy.append(SimpleNamespace(**values))
    reviews = [ReviewDetail.model_validate(item) for item in payload["review_details"]]
    result = compare_legacy_and_review_summaries(
        day=args.date,
        timezone=args.timezone,
        legacy_events=legacy,
        review_details=reviews,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
