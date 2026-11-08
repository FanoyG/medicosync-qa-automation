import uuid
import pytest
from sqlalchemy.exc import DataError, IntegrityError, StatementError
from app.models.user import User, UserGender, UserRole


@pytest.fixture()
def valid_user_payload():
    return {
        "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
        "hashed_password": "some_hashed_value",
        "full_name": "John Doe",
        "role": UserRole.DOCTOR,
        "gender": UserGender.MALE,
        "country_code": "+91",
        "phone_number": "9999999999",
        "specialty": "Cardiology",
    }


# ---------------------------------------------------------------------------
# User model: successful creation and default values
# ---------------------------------------------------------------------------
async def test_user_id_is_generated(db_session, valid_user_payload):
    user = User(**valid_user_payload)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert isinstance(user.id, uuid.UUID)


async def test_user_is_active_defaults_to_true(db_session, valid_user_payload):
    user = User(**valid_user_payload)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.is_active is True


async def test_user_created_at_is_set_and_timezone_aware(db_session, valid_user_payload):
    user = User(**valid_user_payload)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.created_at is not None
    assert user.created_at.tzinfo is not None


# ---------------------------------------------------------------------------
# User model: uniqueness and required constraints
# ---------------------------------------------------------------------------
async def test_user_email_must_be_unique(db_session, valid_user_payload):
    db_session.add(User(**valid_user_payload))
    await db_session.commit()

    db_session.add(User(**{**valid_user_payload, "phone_number": "8888888888"}))
    with pytest.raises(IntegrityError) as exc:
        await db_session.commit()

    # Precise anchor check on the raw driver string
    assert "Key (email)" in str(exc.value.orig)


@pytest.mark.parametrize("field_name", [
    "email", "hashed_password", "full_name",
    "role", "gender", "country_code", "phone_number",
])
async def test_required_fields_cannot_be_null(db_session, valid_user_payload, field_name):
    db_session.add(User(**{**valid_user_payload, field_name: None}))

    with pytest.raises(IntegrityError) as exc:
        await db_session.commit()

    # Precise quoted column anchor check
    assert f'column "{field_name}"' in str(exc.value.orig)


# ---------------------------------------------------------------------------
# User model: optional field and enum rules
# ---------------------------------------------------------------------------
async def test_specialty_can_be_null(db_session, valid_user_payload):
    user = User(**{**valid_user_payload, "specialty": None})
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.specialty is None


@pytest.mark.parametrize(
    "field_name, invalid_value",
    [
        ("role", "superadmin"),
        ("gender", "superadmin"),
    ],
)
async def test_invalid_enum_values_are_rejected(db_session, valid_user_payload, field_name, invalid_value):
    payload = {**valid_user_payload, field_name: invalid_value}
    user = User(**payload)
    db_session.add(user)

    with pytest.raises((DataError, StatementError)):
        await db_session.commit()


@pytest.mark.parametrize("role_value", [UserRole.DOCTOR, UserRole.ADMIN, UserRole.ASSISTANT])
async def test_valid_role_values_are_accepted(db_session, valid_user_payload, role_value):
    user = User(**{**valid_user_payload, "role": role_value})
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert isinstance(user.role, UserRole)
    assert user.role == role_value


@pytest.mark.parametrize("gender_value", [UserGender.MALE, UserGender.FEMALE, UserGender.OTHER])
async def test_valid_gender_values_are_accepted(db_session, valid_user_payload, gender_value):
    user = User(**{**valid_user_payload, "gender": gender_value})
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert isinstance(user.gender, UserGender)
    assert user.gender == gender_value


# ---------------------------------------------------------------------------
# User model: string length boundaries and enforcement
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "field_name, value",
    [
        ("email", "a" * 255),
        ("hashed_password", "b" * 255),
        ("full_name", "c" * 255),
        ("country_code", "+12"),
        ("phone_number", "1" * 15),
        ("specialty", "d" * 100),
    ],
)
async def test_string_fields_accept_boundary_values(db_session, valid_user_payload, field_name, value):
    payload = {**valid_user_payload, field_name: value}
    user = User(**payload)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert getattr(user, field_name) == value


@pytest.mark.parametrize(
    "field_name, value",
    [
        ("email", "a" * 256),
        ("hashed_password", "b" * 256),
        ("full_name", "c" * 256),
        ("country_code", "+1234"),
        ("phone_number", "1" * 16),
        ("specialty", "d" * 101),
    ],
)
async def test_string_fields_reject_values_over_limit(db_session, valid_user_payload, field_name, value):
    payload = {**valid_user_payload, field_name: value}
    user = User(**payload)
    db_session.add(user)

    with pytest.raises((DataError)):
        await db_session.commit()

#-----------------------------------------------
# Case-Sensitive Edge Case
#-----------------------------------------------

@pytest.mark.xfail(reason="email uniqueness is case-sensitive at DB level")
async def test_email_unique_ignores_case(db_session, valid_user_payload):
    db_session.add(User(**valid_user_payload))
    await db_session.commit()

    db_session.add(User(**{**valid_user_payload, "email": "TEST@test.com", "phone_number": "8888888888"}))
    with pytest.raises(IntegrityError):
        await db_session.commit()