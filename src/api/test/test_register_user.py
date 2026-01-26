import json
import pytest
from httpx import AsyncClient, ASGITransport

from uuid import uuid4

from src.main import app


REPORT_FILE = "src/api/test/report.txt"
REGISTER_URL = "/users/register-user"


@pytest.mark.asyncio
async def test_register_user():
    results = []

    unique_suffix = uuid4().hex[:8]
    unique_email = f"testuser_{unique_suffix}@example.com"
    unique_mobile = int(unique_suffix[:10], 16) % 10**10

    # --- Define payload scenarios ---
    test_cases = [
        {
            "name": "valid_user",
            "payload": {
                "name": "Test User",
                "email": unique_email,
                "mobile_number": unique_mobile,
                "city": "Test City",
                "password": "SecurePass123",
                "confirm_password": "SecurePass123",
            },
            "expected_status": 201,
        },
        {
            "name": "password_mismatch",
            "payload": {
                "name": "Mismatch User",
                "email": f"mismatch_{unique_suffix}@example.com",
                "mobile_number": unique_mobile + 1,
                "city": "City X",
                "password": "Password1",
                "confirm_password": "Password2",
            },
            "expected_status": 400,
        },
        {
            "name": "duplicate_email",
            "payload": {
                "name": "Duplicate Email",
                "email": unique_email,
                "mobile_number": unique_mobile + 2,
                "city": "City Y",
                "password": "SomePass123",
                "confirm_password": "SomePass123",
            },
            "expected_status": 409,
        },
        {
            "name": "duplicate_mobile",
            "payload": {
                "name": "Duplicate Mobile",
                "email": f"newemail_{unique_suffix}@example.com",
                "mobile_number": unique_mobile,
                "city": "City Z",
                "password": "AnotherPass123",
                "confirm_password": "AnotherPass123",
            },
            "expected_status": 409,
        },
        {
            "name": "missing_required_fields",
            "payload": {
                "email": f"incomplete_{unique_suffix}@example.com",
                "password": "SomePass",
                "confirm_password": "SomePass",
            },
            "expected_status": 422,
        },
        {
            "name": "garbage_values",
            "payload": {
                "name": 12345,
                "email": "not-an-email",
                "mobile_number": "abcdef",
                "city": True,
                "password": None,
                "confirm_password": None,
            },
            "expected_status": 422,
        },
    ]

    # ✅ Correct httpx setup (NEW WAY)
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        for case in test_cases:
            response = await client.post(
                REGISTER_URL,
                json=case["payload"],
            )

            status_ok = response.status_code == case["expected_status"]

            try:
                response_json = response.json()
            except Exception:
                response_json = response.text

            results.append(
                {
                    "test_case": case["name"],
                    "expected_status": case["expected_status"],
                    "actual_status": response.status_code,
                    "passed": status_ok,
                    "payload": case["payload"],
                    "response": response_json,
                }
            )

    # --- Write report ---
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, indent=2, default=str))
            f.write("\n\n")

    # --- Assertions ---
    for r in results:
        assert (
            r["actual_status"] == r["expected_status"]
        ), f"❌ Failed test case: {r['test_case']}"
