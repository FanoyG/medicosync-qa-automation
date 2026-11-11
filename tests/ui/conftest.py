import asyncio
import sys
import uuid

import httpx
import pytest


@pytest.fixture(scope="session", autouse=True)
def proactor_loop_for_playwright():
    """Windows only: Playwright needs the Proactor event loop to start its driver.

    main.py sets the Selector loop (async Postgres needs it), so for the UI
    tests we switch to Proactor, then put the old setting back afterwards.
    """
    if sys.platform != "win32":
        yield
        return

    previous = asyncio.get_event_loop_policy()
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    yield
    asyncio.set_event_loop_policy(previous)


@pytest.fixture
def registered_user(base_url):
    """Create a fresh user through the API, so a UI test can log in as them."""
    user = {
        "email": f"ui_{uuid.uuid4().hex[:8]}@example.com",
        "password": "StrongPass123!",
        "full_name": "UI Test Doctor",
        "gender": "male",
        "phone": {"country_code": "+91", "number": "9876543210"},
    }
    response = httpx.post(f"{base_url}/auth/register", json=user, timeout=10)
    assert response.status_code == 200, response.text
    return user