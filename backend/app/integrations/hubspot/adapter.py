"""
HubSpot CRM adapter — implements CRMProvider using HubSpot's v3 API.

This is the only file in the project that should know HubSpot's specific
API shapes (endpoints, field names like "properties"). Everything else
talks to CRMProvider's generic interface.
"""

from typing import Any

import httpx

from app.config import settings
from app.integrations.base import CRMProvider

HUBSPOT_BASE_URL = "https://api.hubapi.com"


class HubSpotAPIError(Exception):
    """Raised when HubSpot's API returns an error response."""


class HubSpotAdapter(CRMProvider):
    def __init__(self) -> None:
        self._headers = {
            "Authorization": f"Bearer {settings.hubspot_access_token}",
            "Content-Type": "application/json",
        }

    async def _request(self, method: str, path: str, **kwargs) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.request(
                method, f"{HUBSPOT_BASE_URL}{path}", headers=self._headers, **kwargs
            )
        if response.status_code >= 400:
            raise HubSpotAPIError(
                f"HubSpot API error {response.status_code}: {response.text}"
            )
        return response.json()

    async def _search(self, object_type: str, query: str, limit: int) -> list[dict[str, Any]]:
        body = {"query": query, "limit": limit}
        data = await self._request("POST", f"/crm/v3/objects/{object_type}/search", json=body)
        return data.get("results", [])

    async def search_contacts(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        return await self._search("contacts", query, limit)

    async def get_contact(self, contact_id: str) -> dict[str, Any] | None:
        try:
            return await self._request("GET", f"/crm/v3/objects/contacts/{contact_id}")
        except HubSpotAPIError:
            return None

    async def search_companies(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        return await self._search("companies", query, limit)

    async def get_company(self, company_id: str) -> dict[str, Any] | None:
        try:
            return await self._request("GET", f"/crm/v3/objects/companies/{company_id}")
        except HubSpotAPIError:
            return None

    async def search_deals(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        return await self._search("deals", query, limit)

    async def get_deal(self, deal_id: str) -> dict[str, Any] | None:
        try:
            return await self._request("GET", f"/crm/v3/objects/deals/{deal_id}")
        except HubSpotAPIError:
            return None