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

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String
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