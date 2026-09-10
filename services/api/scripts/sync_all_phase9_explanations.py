# AGNIDRISHTI AI — SIH26162
# Sync all Phase 8 predictions to Phase 9 explanations
from __future__ import annotations

import asyncio
import logging
import time

from sqlalchemy import select

from app.db.models.classification import ThermalClassificationPredictionModel
from app.db.session import get_session_factory
from app.ml.explainability.service import explainability_service

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("sync_all_phase9")


async def main() -> None:
    factory = get_session_factory()
    async with factory() as session:
        stmt = select(ThermalClassificationPredictionModel.observation_id)
        res = await session.execute(stmt)
        obs_ids = [r[0] for r in res.fetchall()]

    logger.info("Found %d classified observations to sync explanations for.", len(obs_ids))
    if not obs_ids:
        return

    chunk_size = 200
    total_created = 0
    total_reused = 0
    total_available = 0
    total_insufficient = 0

    t0 = time.perf_counter()
    async with factory() as session:
        for i in range(0, len(obs_ids), chunk_size):
            chunk = obs_ids[i : i + chunk_size]
            result = await explainability_service.sync_explanations(
                observation_ids=chunk,
                session=session,
                force_recompute=False,
            )
            total_created += result.created
            total_reused += result.reused
            total_available += result.available
            total_insufficient += result.insufficient_evidence
            logger.info(
                "Chunk %d/%d: %d created, %d reused (%d available, %d insufficient)",
                (i // chunk_size) + 1,
                (len(obs_ids) + chunk_size - 1) // chunk_size,
                result.created,
                result.reused,
                result.available,
                result.insufficient_evidence,
            )

    elapsed = time.perf_counter() - t0
    logger.info(
        "Finished Phase 9 sync: %d created, %d reused, %d available, %d insufficient in %.2fs",
        total_created,
        total_reused,
        total_available,
        total_insufficient,
        elapsed,
    )


if __name__ == "__main__":
    asyncio.run(main())
