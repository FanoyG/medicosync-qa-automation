import pytest
from app.services.auth_orchestrator import AuthOrchestrator
from app.core.security import PasswordHandler
from app.services.session_service import SessionManager
from app.services.token_service import TokenGenerator
from app.repository.auth_repo import UserRepository
from app.models.user import User
from uuid import UUID

@pytest.fixture
def auth_orchestrator(db_session, redis_client):
    """Automatically wires up all repo/service dependencies and returns the orchestrator instance."""
    pwd_handler = PasswordHandler()
    session_mgr = SessionManager(redis_client=redis_client)
    user_reg = UserRepository(db=db_session)
    token_gen = TokenGenerator(redis_client=redis_client)

    return AuthOrchestrator(
        pwd_handler=pwd_handler,
        session_mgr=session_mgr,
        user_reg=user_reg,
        token_gen=token_gen
    )

@pytest.fixture
def valid_user_payload():
    """Provides a fresh, standard dictionary representing a valid registration payload."""
    return {
        "email": "new_user@mediosync.com",
        "plain_pwd": "SecurePassword123",
        "username": "tester1",
        "role": "admin",
        "gender": "male",
        "country_code": "IN",
        "phone_number": "9999999999"
    }

# Register User Successfully

@pytest.mark.asyncio
async def test_register_user_success_path(auth_orchestrator, valid_user_payload, db_session, redis_client):
    result = await auth_orchestrator.register_user(**valid_user_payload)

    assert result["message"] == "Registration successful"
    user_id = result["user_id"]

    db_user = await db_session.get(User, UUID(user_id))
    assert db_user is not None
    assert db_user.email == valid_user_payload["email"]
    assert db_user.hashed_password != valid_user_payload["plain_pwd"]

    refersh_token_str = result["refresh_token"]
    redis_key = f"refresh:{refersh_token_str}"
    cached_data = await redis_client.hgetall(redis_key)
    
    assert cached_data is not None, f"Key {redis_key} was not found in Redis."
    assert cached_data["user_id"] == user_id
    assert cached_data["role"] == valid_user_payload["role"]

    ttl = await redis_client.ttl(redis_key)
    assert ttl > 0

# Register User with Duplicate Email

@pytest.mark.asyncio
async def test_register_user_duplicate_email_path(auth_orchestrator, valid_user_payload):
    await auth_orchestrator.register_user(**valid_user_payload)

    with pytest.raises(ValueError) as exc:
        await auth_orchestrator.register_user(**valid_user_payload)

    assert "Account already exists with this email." in str(exc.value)

# Login User Succesfully.
@pytest.mark.asyncio
async def test_login_user_success_on_first_attempt(auth_orchestrator, valid_user_payload, db_session, redis_client):
    """Verifies a user with clean history logs in successfully on the first try."""
    reg_result = await auth_orchestrator.register_user(**valid_user_payload)
    user_id = reg_result["user_id"]

    login_result = await auth_orchestrator.login_user(
        email=valid_user_payload["email"],
        plain_pwd=valid_user_payload["plain_pwd"]
    )

    assert login_result["message"] == "Login successful"
    assert login_result["user_id"] == user_id
    assert "access_token" in login_result
    assert "refresh_token" in login_result

    #Verify state mutation in Postgres and Redis
    db_user = await db_session.get(User, UUID(user_id))
    assert db_user is not None

    login_rt_str = login_result["refresh_token"]
    cached_data = await redis_client.hgetall(f"refresh:{login_rt_str}")
    assert cached_data["user_id"] == user_id


@pytest.mark.asyncio
async def test_login_user_success_resets_historical_failed_counters(auth_orchestrator, valid_user_payload, redis_client):
    """Verifies a successful login completely purges previous failed attempts from Redis."""
    reg_result = await auth_orchestrator.register_user(**valid_user_payload)
    user_id = reg_result["user_id"]
    email = valid_user_payload["email"]
    
    #Pre-seed 2 historic failures inside the container cache
    await redis_client.set(f"failed_attempts:{email}", 2)

    #Log in successfully with true credentials
    login_result = await auth_orchestrator.login_user(
        email=email, 
        plain_pwd=valid_user_payload["plain_pwd"]
    )

    assert login_result["message"] == "Login successful"
    
    #The golden check! The 2 historical failures must be wiped completely clean!
    current_failures = await redis_client.get(f"failed_attempts:{email}")
    assert current_failures is None or int(current_failures) == 0

    #Verify session tokens match
    login_rt_str = login_result["refresh_token"]
    cached_data = await redis_client.hgetall(f"refresh:{login_rt_str}")
    assert cached_data["user_id"] == user_id
    assert cached_data["role"] == valid_user_payload["role"]


# Sad Locked Out.
MAX_ATTEMPTS = 5

@pytest.mark.asyncio
async def test_login_user_lockout_boundry_at_edge(auth_orchestrator, valid_user_payload, redis_client):
    """BVA Test for (MAX - 1) failures: User should NOT be locked out yet."""
    email = valid_user_payload["email"]

    counter_key = f"failed_attempts:{email}"
    lockout_key = f"lockout:{email}"

    await auth_orchestrator.register_user(**valid_user_payload)

    # Simulate 4 failed attempts in my real Redis Container
    await redis_client.set(counter_key, MAX_ATTEMPTS - 1)

    # Should not throw a PermissionError lockout block instead ValueError becase of invalid credential
    with pytest.raises(ValueError) as exc:
        await auth_orchestrator.login_user(
            email=email,
            plain_pwd="AnyPassword@!@@22"
        )

    assert str(exc.value) == "Invalid credentials provided."

    #check did the counter increment to 5?
    current_counter = await redis_client.get(counter_key)
    assert int(current_counter) == MAX_ATTEMPTS

    #check did binary locked out key generated
    lockout_flag = await redis_client.exists(lockout_key)
    assert lockout_flag == 1

@pytest.mark.parametrize("failed_count", [MAX_ATTEMPTS, MAX_ATTEMPTS + 1])
@pytest.mark.asyncio
async def test_login_user_lockout_boundry_block(auth_orchestrator, valid_user_payload, failed_count, redis_client):
    """BVA Test for MAX and (MAX + 1) failures: User must be instantly locked out."""
    email = valid_user_payload["email"]
    redis_key = f"lockout:{email}"

    #Simulate the blocked boundry count direclty inside Redis.
    await redis_client.set(redis_key, failed_count)

    with pytest.raises(PermissionError) as exc:
        await auth_orchestrator.login_user(
            email=email,
            plain_pwd="AnypassWord"
        )

    assert str(exc.value) == "Too many attempts. Locked out."

@pytest.mark.asyncio
async def test_login_user_lockout_takes_priority_over_unknown_email(auth_orchestrator, redis_client):
    """
        before checking if the email exists in Postgres.
    """
    ghost_email = "non_existent_hacker@mediosync.com"
    lockout_key = f"lockout:{ghost_email}"

    #simulate a locked gate inside Redis for a non-existent email
    #value is irrelevant since is_locked_out only checks key existence
    await redis_client.set(lockout_key, "true")

    #Try logging in with this unknown email
    #It must raise a PermissionError (Lockout), NOT a ValueError (Invalid Credentials)
    with pytest.raises(PermissionError) as exc:
        await auth_orchestrator.login_user(
            email=ghost_email,
            plain_pwd="AnyPassword123!"
        )

    #Confirm the system exited at Branch 1 cleanly
    assert str(exc.value) == "Too many attempts. Locked out."


@pytest.mark.asyncio
async def test_login_user_email_does_not_exist_branch(auth_orchestrator, redis_client):
    """    
        Should raise a ValueError instantly and leave Redis completely clean.
    """
    unregistered_email = "ghost_user_999@mediosync.com"
    counter_key = f"failed_attempts:{unregistered_email}"

    #Attempt to login an email that was never registered in Postgres
    with pytest.raises(ValueError) as exc:
        await auth_orchestrator.login_user(
            email=unregistered_email,
            plain_pwd="AnyPassword123!"
        )

    #ASSERT: Check System Response (Security standard text match)
    assert str(exc.value) == "Invalid credentials provided."

    #The failed_attempts counter key should not exist in Redis at all
    current_counter = await redis_client.get(counter_key)
    assert current_counter is None

import pytest
from uuid import UUID

@pytest.mark.asyncio
async def test_login_user_incorrect_password_branch(auth_orchestrator, valid_user_payload, db_session, redis_client):
    """
        Should raise a ValueError, increment the counter, and NOT lock the user out.
    """
    email = valid_user_payload["email"]
    counter_key = f"failed_attempts:{email}"
    lockout_key = f"lockout:{email}"

    #Register the user first so they exist inside Postgres
    reg_result = await auth_orchestrator.register_user(**valid_user_payload)
    user_id = reg_result["user_id"]

    #Attempt login with the correct email but a completely wrong password
    with pytest.raises(ValueError) as exc:
        await auth_orchestrator.login_user(
            email=email,
            plain_pwd="ThisIsAWrongPassword123!"
        )

    #Check System Response (Security standard text match)
    assert str(exc.value) == "Invalid credentials provided."

    #Verify background data changes
    #Did the failed attempts counter accurately increment to 1?
    current_counter = await redis_client.get(counter_key)
    assert current_counter is not None
    assert int(current_counter) == 1

    #Ensure the binary lockout key does NOT exist yet (since count is 1 < 5)
    lockout_flag = await redis_client.exists(lockout_key)
    assert lockout_flag == 0  # 0 means key does not exist!

@pytest.mark.asyncio
async def test_refresh_access_token_success_path(auth_orchestrator, valid_user_payload, redis_client):
    """Happy Path Test: Rotating an active refresh token to get a new access token."""
    #Register a user to get an active, functional refresh token trigger
    reg_result = await auth_orchestrator.register_user(**valid_user_payload)
    old_rt = reg_result["refresh_token"]
    user_id = reg_result["user_id"]

    #Call the token rotation service pipeline
    rotation_result = await auth_orchestrator.refresh_access_token(refresh_token_str=old_rt)

    assert "access_token" in rotation_result
    assert "refresh_token" not in rotation_result  # The app does not return a new refresh token

    #Verify the token state inside Redis remains active
    redis_key = f"refresh:{old_rt}"
    cached_data = await redis_client.hgetall(redis_key)
    
    assert cached_data is not None
    assert cached_data["user_id"] == user_id


@pytest.mark.asyncio
async def test_refresh_access_token_invalid_or_expired_path(auth_orchestrator):
    """Sad Path Test: Attempting to rotate an invalid, forged, or expired token payload."""
    fake_token = "this-token-does-not-exist-in-redis-12345"

    #Passing a forged token should instantly trigger an authentication error
    with pytest.raises(ValueError) as exc:
        await auth_orchestrator.refresh_access_token(refresh_token_str=fake_token)
    assert str(exc.value) == "Refresh token invalid or expired."
