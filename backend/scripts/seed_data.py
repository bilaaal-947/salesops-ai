"""
Seed the database with realistic synthetic demo data for the
NovaStack Technologies demo organization (Section 62/63).

Run from inside backend/ with the venv active:
    python -m scripts.seed_data
"""

import asyncio
import random
from datetime import datetime, timedelta, timezone

from faker import Faker
from sqlalchemy import select

from app.database.models import (
    Account,
    ActivityType,
    Contact,
    Deal,
    DealActivity,
    DealStage,
    Organization,
    Task,
    User,
    UserRole,
)
from app.database.session import AsyncSessionLocal

fake = Faker()

DEAL_STAGES = list(DealStage)
NUM_ACCOUNTS = 50
CONTACTS_PER_ACCOUNT = 3
DEALS_PER_ACCOUNT = 2


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        existing = await session.execute(
            select(Organization).where(Organization.name == "NovaStack Technologies")
        )
        if existing.scalar_one_or_none():
            print("Demo data already exists — skipping. Delete the org manually to reseed.")
            return

        org = Organization(name="NovaStack Technologies")
        session.add(org)
        await session.flush()  # get org.id without committing yet

        users = [
            User(organization_id=org.id, email="manager@novastack.demo",
                 full_name="Jordan Reyes", role=UserRole.SALES_MANAGER),
            User(organization_id=org.id, email="rep1@novastack.demo",
                 full_name="Alex Chen", role=UserRole.SALES_REP),
            User(organization_id=org.id, email="rep2@novastack.demo",
                 full_name="Sam Patel", role=UserRole.SALES_REP),
            User(organization_id=org.id, email="admin@novastack.demo",
                 full_name="Taylor Morgan", role=UserRole.ADMIN),
        ]
        session.add_all(users)
        await session.flush()

        reps = [u for u in users if u.role == UserRole.SALES_REP]

        for _ in range(NUM_ACCOUNTS):
            account = Account(
                organization_id=org.id,
                name=fake.company(),
                industry=random.choice(["B2B SaaS", "Fintech", "Healthcare", "E-commerce", "Manufacturing"]),
                employee_count=random.randint(20, 2000),
            )
            session.add(account)
            await session.flush()

            for _ in range(CONTACTS_PER_ACCOUNT):
                session.add(Contact(
                    account_id=account.id,
                    full_name=fake.name(),
                    email=fake.company_email(),
                    title=random.choice(["VP Sales", "CTO", "Head of Ops", "Procurement Manager", "CEO"]),
                ))

            for _ in range(DEALS_PER_ACCOUNT):
                stage = random.choices(
                    DEAL_STAGES,
                    weights=[20, 20, 25, 15, 15, 5],  # skew toward active mid-funnel stages
                )[0]
                days_since_activity = random.randint(0, 45)
                deal = Deal(
                    account_id=account.id,
                    owner_id=random.choice(reps).id,
                    name=f"{account.name} - {fake.bs().title()}",
                    value=round(random.uniform(5_000, 120_000), 2),
                    stage=stage,
                    last_activity_at=datetime.now(timezone.utc) - timedelta(days=days_since_activity),
                )
                session.add(deal)
                await session.flush()

                for _ in range(random.randint(1, 5)):
                    session.add(DealActivity(
                        deal_id=deal.id,
                        activity_type=random.choice(list(ActivityType)),
                        occurred_at=datetime.now(timezone.utc) - timedelta(days=random.randint(1, 60)),
                        summary=fake.sentence(),
                    ))

                if days_since_activity > 14 and deal.value > 30_000:
                    session.add(Task(
                        deal_id=deal.id,
                        assigned_to=deal.owner_id,
                        title=f"Follow up with {account.name}",
                        due_at=datetime.now(timezone.utc) + timedelta(days=2),
                        created_by_agent=False,
                    ))

        await session.commit()
        print(f"Seeded: 1 org, {len(users)} users, {NUM_ACCOUNTS} accounts, "
              f"~{NUM_ACCOUNTS * CONTACTS_PER_ACCOUNT} contacts, "
              f"~{NUM_ACCOUNTS * DEALS_PER_ACCOUNT} deals.")


if __name__ == "__main__":
    asyncio.run(seed())