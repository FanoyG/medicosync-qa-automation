import pytest

@pytest.mark.smoke
async def test_login_success(auth_service, registered_user, login_payload):
    response = await auth_service.login(login_payload)
    assert response.status_code == 200
    assert response.json()["message"] == "Login successful"

@pytest.mark.smoke
async def test_login_wrong_password(auth_service, registered_user, login_payload):
    login_payload["password"] = "WrongPass999!"
    response = await auth_service.login(login_payload)
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid credentials provided."


async def test_login_unknown_email(auth_service, login_payload):
    response = await auth_service.login(login_payload)   # user never registered
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid credentials provided."


async def test_login_missing_password(auth_service, login_payload):
    login_payload.pop("password")
    response = await auth_service.login(login_payload)
    assert response.status_code == 422

@pytest.mark.smoke
async def test_login_locked_after_5_failed_attempts(auth_service, registered_user, login_payload):
    wrong = {**login_payload, "password": "WrongPass999!"}

    for _ in range(5):
        await auth_service.login(wrong)           # each one returns 400

    response = await auth_service.login(login_payload)   # right password, still blocked
    assert response.status_code == 429
    assert "Locked out" in response.json()["detail"]

async def test_login_success_resets_failed_attempts(auth_service, registered_user, login_payload):
    wrong = {**login_payload, "password": "WrongPass999!"}

    for _ in range(4):
        await auth_service.login(wrong)
    assert (await auth_service.login(login_payload)).status_code == 200   # reset here

    for _ in range(4):
        await auth_service.login(wrong)
    assert (await auth_service.login(login_payload)).status_code == 200   # not locked