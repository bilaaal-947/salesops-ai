"""
SQLAlchemy ORM models.

This file currently holds the multi-tenancy root (Organization, User).
Business tables (Account, Contact, Deal), agent-execution tables
(AgentRun, AgentAction, Approval, AuditLog), and the knowledge base tables
get added here incrementally in later phases — kept in one models.py per
Section 25 rather than pre-splitting into many files before there's enough
in each to warrant it.
"""

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    SALES_MANAGER = "SALES_MANAGER"
    SALES_REP = "SALES_REP"
    VIEWER = "VIEWER"


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    hubspot_portal_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    users: Mapped[list["User"]] = relationship(back_populates="organization")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False, default=UserRole.SALES_REP)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    organization: Mapped["Organization"] = relationship(back_populates="users")

class DealStage(str, enum.Enum):
    PROSPECTING = "PROSPECTING"
    QUALIFICATION = "QUALIFICATION"
    PROPOSAL = "PROPOSAL"
    NEGOTIATION = "NEGOTIATION"
    CLOSED_WON = "CLOSED_WON"
    CLOSED_LOST = "CLOSED_LOST"


class Account(Base):
    """A company/customer account. Owned by an organization (tenant),
    not to be confused with Organization itself — Account is the CRM
    company record, Organization is the tenant using this platform."""

    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hubspot_company_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(120), nullable=True)
    employee_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    contacts: Mapped[list["Contact"]] = relationship(back_populates="account")
    deals: Mapped[list["Deal"]] = relationship(back_populates="account")


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hubspot_contact_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    title: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    account: Mapped["Account"] = relationship(back_populates="contacts")


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True
    )
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    hubspot_deal_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    stage: Mapped[DealStage] = mapped_column(Enum(DealStage), nullable=False, default=DealStage.PROSPECTING)

    # Deterministic opportunity score (0-100), computed by code — never by the LLM.
    # See Section 22: ICP fit + company size + engagement + deal value + recency + buying signals.
    score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    account: Mapped["Account"] = relationship(back_populates="deals")
    
    
class ActivityType(str, enum.Enum):
    CALL = "CALL"
    EMAIL = "EMAIL"
    MEETING = "MEETING"
    NOTE = "NOTE"
    STAGE_CHANGE = "STAGE_CHANGE"


class DealActivity(Base):
    """A logged interaction on a deal. This is what deal.last_activity_at
    and 'days since last activity' calculations are derived from — used
    heavily by stalled-opportunity detection (Section 5)."""

    __tablename__ = "deal_activities"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    activity_type: Mapped[ActivityType] = mapped_column(Enum(ActivityType), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())


class TaskStatus(str, enum.Enum):
    OPEN = "OPEN"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class Task(Base):
    """A follow-up action item, created either by a human or by the agent
    (e.g. after a stalled-opportunity investigation recommends a follow-up)."""

    __tablename__ = "tasks"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deal_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("deals.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[TaskStatus] = mapped_column(Enum(TaskStatus), nullable=False, default=TaskStatus.OPEN)

    # True when a Task was created autonomously by the agent rather than a human —
    # useful for auditing and for the frontend to visually distinguish the two.
    created_by_agent: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_at: Mapped[datetime] = mapped_column(server_default=func.now())