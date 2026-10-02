"""
Repository layer — centralized, tenant-safe query functions.

Every function here takes organization_id explicitly and enforces it in
the query (joining through Account where needed). API routes and agent
tools should call these instead of writing raw queries, so tenant
isolation is enforced in exactly one place.
"""

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Account, Deal, DealStage


async def get_deal(
    session: AsyncSession, organization_id: uuid.UUID, deal_id: uuid.UUID
) -> Deal | None:
    """Fetch a single deal, scoped to the organization. Returns None if the
    deal doesn't exist OR belongs to a different org — callers can't tell
    the difference, which is the correct behavior for tenant isolation."""
    result = await session.execute(
        select(Deal)
        .join(Account, Deal.account_id == Account.id)
        .where(Deal.id == deal_id, Account.organization_id == organization_id)
    )
    return result.scalar_one_or_none()


async def search_deals(
    session: AsyncSession,
    organization_id: uuid.UUID,
    stage: DealStage | None = None,
    owner_id: uuid.UUID | None = None,
    stale_days: int | None = None,
    min_value: float | None = None,
) -> list[Deal]:
    """Search deals within an organization, with optional filters.
    stale_days filters to deals with no activity in at least that many days —
    the core query behind stalled-opportunity detection (Section 5)."""
    query = (
        select(Deal)
        .join(Account, Deal.account_id == Account.id)
        .where(Account.organization_id == organization_id)
    )

    if stage is not None:
        query = query.where(Deal.stage == stage)
    if owner_id is not None:
        query = query.where(Deal.owner_id == owner_id)
    if min_value is not None:
        query = query.where(Deal.value >= min_value)
    if stale_days is not None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=stale_days)
        query = query.where(
            (Deal.last_activity_at == None) | (Deal.last_activity_at <= cutoff)  # noqa: E711
        )

    result = await session.execute(query.order_by(Deal.value.desc()))
    return list(result.scalars().all())


async def get_pipeline_metrics(session: AsyncSession, organization_id: uuid.UUID) -> dict:
    """Deterministic pipeline summary — total value and count per stage.
    This is plain aggregation, not something the LLM should ever compute
    itself (Section 21)."""
    query = (
        select(Deal.stage, func.count(Deal.id), func.coalesce(func.sum(Deal.value), 0))
        .join(Account, Deal.account_id == Account.id)
        .where(Account.organization_id == organization_id)
        .group_by(Deal.stage)
    )
    result = await session.execute(query)

    by_stage = {
        stage.value: {"count": count, "value": float(total)}
        for stage, count, total in result.all()
    }
    total_value = sum(s["value"] for s in by_stage.values())
    total_count = sum(s["count"] for s in by_stage.values())

    return {
        "total_pipeline_value": total_value,
        "total_deal_count": total_count,
        "by_stage": by_stage,
    }