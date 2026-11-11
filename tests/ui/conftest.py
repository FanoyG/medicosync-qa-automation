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

@pytest.fixture
def logged_in_page(new_context, base_url, registered_user):
    """A browser page that is already logged in, so the test skips the login form.
 
    1. Log in through the API and get the token.
    2. Put the token (and email) into the browser's localStorage, which is
       where the frontend keeps them (a Playwright "storage state").
    """
    response = httpx.post(
        f"{base_url}/auth/login",
        json={"email": registered_user["email"], "password": registered_user["password"]},
        timeout=10,
    )
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
 
    state = {
        "cookies": [],
        "origins": [
            {
                "origin": base_url,
                "localStorage": [
                    {"name": "access_token", "value": token},
                    {"name": "user_email", "value": registered_user["email"]},
                ],
            }
        ],
    }
    context = new_context(storage_state=state)
    return context.new_page()