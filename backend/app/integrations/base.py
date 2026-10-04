"""
Abstract CRM provider interface.

Nothing outside the integrations/ package should import HubSpotAdapter
directly — code depends on this interface instead, so swapping providers
later means writing one new adapter, not touching the rest of the app.
"""

from abc import ABC, abstractmethod
from typing import Any


class CRMProvider(ABC):
    @abstractmethod
    async def search_contacts(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_contact(self, contact_id: str) -> dict[str, Any] | None:
        ...

    @abstractmethod
    async def search_companies(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_company(self, company_id: str) -> dict[str, Any] | None:
        ...

    @abstractmethod
    async def search_deals(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        ...

    @abstractmethod
    async def get_deal(self, deal_id: str) -> dict[str, Any] | None:
        ...