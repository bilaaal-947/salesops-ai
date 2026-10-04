"""
Smoke test for the HubSpot adapter — confirms real API connectivity
and that search_contacts / search_companies return actual data.

Run from backend/ with venv active:
    python -m scripts.test_hubspot_connection
"""

import asyncio

from app.integrations.hubspot.adapter import HubSpotAdapter, HubSpotAPIError


async def main() -> None:
    adapter = HubSpotAdapter()

    print("Testing search_contacts()...")
    try:
        contacts = await adapter.search_contacts(query="", limit=10)
        print(f"  Found {len(contacts)} contact(s).")
        for c in contacts[:3]:
            props = c.get("properties", {})
            print(f"  - {props.get('firstname', '')} {props.get('lastname', '')} ({props.get('email', 'no email')})")
    except HubSpotAPIError as e:
        print(f"  FAILED: {e}")
        return

    print("\nTesting search_companies()...")
    try:
        companies = await adapter.search_companies(query="", limit=10)
        print(f"  Found {len(companies)} company(ies).")
        for c in companies[:3]:
            props = c.get("properties", {})
            print(f"  - {props.get('name', 'unnamed')}")
    except HubSpotAPIError as e:
        print(f"  FAILED: {e}")
        return

    print("\n✅ HUBSPOT CONNECTION TEST PASSED")


if __name__ == "__main__":
    asyncio.run(main())