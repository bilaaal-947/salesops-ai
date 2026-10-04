"""
Smoke test for authentication: logs in as a real Supabase test user,
then calls a protected local API endpoint with the resulting token.

Run from backend/ with venv active:
    python -m scripts.test_auth_flow
"""

import httpx

from app.config import settings

TEST_EMAIL = "manager@novastack.demo"
TEST_PASSWORD = "TestPass123!"
LOCAL_API_URL = "http://localhost:8000"


def main() -> None:
    print("Step 1: Logging in via Supabase...")
    login_response = httpx.post(
        f"{settings.supabase_url}/auth/v1/token?grant_type=password",
        headers={"apikey": settings.supabase_publishable_key},
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
        timeout=10.0,
    )

    if login_response.status_code != 200:
        print(f"LOGIN FAILED: {login_response.status_code} — {login_response.text}")
        return

    token = login_response.json()["access_token"]
    print(f"Login OK. Got token: {token[:30]}...")

    print("\nStep 2: Calling protected endpoint without a token (should fail)...")
    no_auth_response = httpx.get(f"{LOCAL_API_URL}/api/pipeline", timeout=10.0)
    print(f"Status: {no_auth_response.status_code} (expecting 401 or 403)")

    print("\nStep 3: Calling protected endpoint WITH token (should succeed)...")
    auth_response = httpx.get(
        f"{LOCAL_API_URL}/api/pipeline",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10.0,
    )
    print(f"Status: {auth_response.status_code}")
    print(f"Body: {auth_response.json()}")

    if auth_response.status_code == 200:
        print("\n✅ AUTH TEST PASSED")
    else:
        print("\n❌ AUTH TEST FAILED")


if __name__ == "__main__":
    main()