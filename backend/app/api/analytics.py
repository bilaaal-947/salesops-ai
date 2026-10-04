"""
Analytics API routes — pipeline metrics, deal aging, etc.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import User
from app.database.repositories import get_pipeline_metrics
from app.database.session import get_db
from app.security.authentication import get_current_user

router = APIRouter()


@router.get("/pipeline")
async def pipeline_metrics(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    return await get_pipeline_metrics(db, user.organization_id)