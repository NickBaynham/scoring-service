"""Seed minimal development data (requires running API DB and migrations)."""

import asyncio
import os
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Document, DocumentStatus, SourceType


async def main() -> None:
    url = os.environ.get("DATABASE_URL", "postgresql+asyncpg://scoring:scoring@localhost:5432/scoring")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    engine = create_async_engine(url)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        doc = Document(
            id=str(uuid.uuid4()),
            tenant_id="tenant_dev",
            source_type=SourceType.PASTE,
            raw_text="This is seeded development text for local credibility scoring.",
            profile="credibility_v1",
            status=DocumentStatus.READY,
        )
        session.add(doc)
        await session.commit()
        print(f"Seeded document id={doc.id}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
