import pytest

@pytest.mark.smoke
async def test_register_success(auth_service, register_payload):
    response = await auth_service.register(register_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Registration successful"
    assert data["user_id"]
    assert data["access_token"]
    assert data["refresh_token"]

async def test_duplicate_email(auth_service, register_payload):
    register_payload['email'] = 'user_john@example.com'
    await auth_service.register(register_payload)

    response = await auth_service.register(register_payload)
    assert response.status_code == 400
    assert "already exists" in response.json()['detail']

async def test_register_invalid_phone(auth_service, register_payload):
    register_payload['phone']['number'] = "123ab"
    response = await auth_service.register(register_payload)

    assert response.status_code == 422
    assert "only digit" in response.text

async def test_missing_password_field(auth_service, register_payload):
    register_payload.pop('password')
    response = await auth_service.register(register_payload)
    assert response.status_code == 422

async def test_extra_field_is_ignored(auth_service, register_payload):
    register_payload['extra'] = 'x'
    response = await auth_service.register(register_payload)
    
    assert response.status_code == 200
    assert 'user_id' in response.json()
    assert 'extra' not in response.json()