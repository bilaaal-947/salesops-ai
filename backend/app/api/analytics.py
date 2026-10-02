"""
Analytics API routes — pipeline metrics, deal aging, etc.

TODO(auth): organization_id is temporarily resolved by looking up the demo
org by name. Once Supabase auth is wired up (Phase 1 remaining item), this
must be replaced with organization_id derived from the authenticated
session — never trust a client-supplied value here (Section 26).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import Organization
from app.database.repositories import get_pipeline_metrics
from app.database.session import get_db

router = APIRouter()

DEMO_ORG_NAME = "NovaStack Technologies"


async def _get_demo_org_id(db: AsyncSession) -> str:
    result = await db.execute(select(Organization).where(Organization.name == DEMO_ORG_NAME))
    org = result.scalar_one_or_none()
    if org is None:
        raise HTTPException(status_code=404, detail="Demo organization not found — run the seed script first.")
    return org.id


@router.get("/pipeline")
async def pipeline_metrics(db: AsyncSession = Depends(get_db)) -> dict:
    org_id = await _get_demo_org_id(db)
    return await get_pipeline_metrics(db, org_id)