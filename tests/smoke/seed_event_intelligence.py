"""Seed the base-owned sanitized fixture through its own ingest pipeline."""

import asyncio
from pathlib import Path

from nanexus_event_intelligence.adapters.frigate.demo_cli import seed
from nanexus_event_intelligence.config import get_settings
from nanexus_event_intelligence.persistence.database import (
    create_engine,
    create_session_factory,
)


async def main() -> None:
    engine = create_engine(get_settings().database_url)
    try:
        await seed(create_session_factory(engine), Path("/fixtures"))
    finally:
        await engine.dispose()


asyncio.run(main())
