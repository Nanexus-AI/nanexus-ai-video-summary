#!/usr/bin/env python3
"""Build a rule-based daily summary (M0 stand-in for LLM summary worker)."""

from __future__ import annotations

import argparse
from datetime import UTC, date, datetime

from nanexus.db import SessionLocal, init_db
from nanexus.summary import build_rule_summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", type=str, default=None, help="YYYY-MM-DD (default: today UTC)")
    parser.add_argument("--camera", type=str, default=None)
    args = parser.parse_args()

    day = date.fromisoformat(args.date) if args.date else datetime.now(tz=UTC).date()
    init_db()
    db = SessionLocal()
    try:
        summary = build_rule_summary(db, day, camera=args.camera)
        print(summary.content)
        print(f"\n[saved id={summary.id} events={summary.event_count} model={summary.model}]")
    finally:
        db.close()


if __name__ == "__main__":
    main()
