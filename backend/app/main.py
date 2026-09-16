"""
SalesOps AI — FastAPI application entrypoint.

Routers are added incrementally as each API area is built:
    app.include_router(agent_router, prefix="/api/agent", tags=["agent"])
    app.include_router(approvals_router, prefix="/api/approvals", tags=["approvals"])
    ...
"""

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database.session import get_db

app = FastAPI(
    title="SalesOps AI",
    description="Autonomous AI Sales Operations Agent",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"] if not settings.is_production else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)) -> dict:
    """Liveness/readiness probe — verifies the app can actually reach Postgres,
    not just that the process is running."""
    await db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "environment": settings.environment,
        "database": "connected",
    }


@app.get("/")
async def root() -> dict:
    return {"service": "salesops-ai-backend", "docs": "/docs"}
