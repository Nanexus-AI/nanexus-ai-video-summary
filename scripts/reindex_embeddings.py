#!/usr/bin/env python3
"""Import JSONL EmbeddingJobs produced through the public processor flow."""

import argparse
import json
from pathlib import Path

from nanexus.db import SessionLocal
from nanexus.indexing import EmbeddingJob, activate_model, persist_embedding


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--activate", action="store_true")
    args = parser.parse_args()
    jobs = [
        EmbeddingJob.from_json(line) for line in args.input.read_text().splitlines() if line.strip()
    ]
    versions = {(job.model, job.model_version) for job in jobs}
    print(
        json.dumps(
            {
                "status": "planned",
                "records": len(jobs),
                "models": sorted(versions),
                "dry_run": args.dry_run,
            }
        )
    )
    if args.dry_run:
        return
    with SessionLocal() as db:
        for index, job in enumerate(jobs, 1):
            persist_embedding(db, job)
            print(json.dumps({"status": "progress", "completed": index, "total": len(jobs)}))
        if args.activate:
            if len(versions) != 1:
                raise SystemExit("--activate requires exactly one model version")
            model, version = next(iter(versions))
            activate_model(db, model=model, model_version=version)
    print(json.dumps({"status": "complete", "records": len(jobs), "activated": args.activate}))


if __name__ == "__main__":
    main()
