import pytest
from pydantic import ValidationError

from app.schemas.auth_schemas import PhoneSchema, RefreshRequest, UserLogin, UserRegister


@pytest.fixture
def valid_phone_data():
	return {
		"country_code": "+91",
		"number": "9876543210",
	}


def test_phone_schema_accepts_valid_phone(valid_phone_data):
	phone = PhoneSchema(**valid_phone_data)

	assert phone.country_code == valid_phone_data["country_code"]
	assert phone.number == valid_phone_data["number"]


def test_phone_schema_accepts_any_country_code_content(valid_phone_data):
	data = valid_phone_data
	data["country_code"] = "not-a-real-code."

	phone = PhoneSchema(**data)

	assert phone.country_code == "not-a-real-code."


@pytest.mark.parametrize("missing_field", ["country_code", "number"])
def test_phone_schema_rejects_missing_required_field(valid_phone_data, missing_field):
	data = valid_phone_data
	del data[missing_field]

	with pytest.raises(ValidationError):
		PhoneSchema(**data)


@pytest.mark.parametrize("null_field", ["country_code", "number"])
def test_phone_schema_rejects_null_field(valid_phone_data, null_field):
	data = valid_phone_data
	data[null_field] = None

	with pytest.raises(ValidationError):
		PhoneSchema(**data)


@pytest.mark.parametrize(
	"field, value",
	[
		("country_code", 91),
		("country_code", True),
		("country_code", ["+91"]),
		("country_code", {"code": "+91"}),
		("number", 9876543210),
		("number", True),
		("number", ["9876543210"]),
		("number", {"value": "9876543210"}),
	],
)
def test_phone_schema_rejects_wrong_field_type(valid_phone_data, field, value):
	data = valid_phone_data
	data[field] = value

	with pytest.raises(ValidationError) as exc_info:
		PhoneSchema(**data)

	assert exc_info.value.errors()[0]["loc"] == (field,)
	assert exc_info.value.errors()[0]["type"] == "string_type"

@pytest.mark.parametrize("number", ["123"])
def test_phone_schema_rejects_number_below_minimum_length(valid_phone_data, number):
	data = valid_phone_data
	data["number"] = number

	with pytest.raises(ValidationError):
		PhoneSchema(**data)


@pytest.mark.parametrize("number", ["1234"])
def test_phone_schema_accepts_number_at_minimum_length(valid_phone_data, number):
	data = valid_phone_data
	data["number"] = number

	phone = PhoneSchema(**data)

	assert phone.number == number


@pytest.mark.parametrize("number", ["123456789012345"])
def test_phone_schema_accepts_number_at_maximum_length(valid_phone_data, number):
	data = valid_phone_data
	data["number"] = number

	phone = PhoneSchema(**data)

	assert phone.number == number


@pytest.mark.parametrize("number", ["1234567890123456"])
def test_phone_schema_rejects_number_above_maximum_length(valid_phone_data, number):
	data = valid_phone_data
	data["number"] = number

	with pytest.raises(ValidationError):
		PhoneSchema(**data)


@pytest.mark.parametrize("number", [""])
def test_phone_schema_rejects_empty_number(valid_phone_data, number):
	data = valid_phone_data
	data["number"] = number

	with pytest.raises(ValidationError):
		PhoneSchema(**data)


@pytest.mark.parametrize("number", ["98765abc10"])
def test_phone_schema_rejects_letters_in_number(valid_phone_data, number):
	data = valid_phone_data
	data["number"] = number

	with pytest.raises(ValidationError):
		PhoneSchema(**data)


@pytest.mark.parametrize("number", ["9876-543210"])
def test_phone_schema_rejects_symbols_in_number(valid_phone_data, number):
	data = valid_phone_data
	data["number"] = number

	with pytest.raises(ValidationError):
		PhoneSchema(**data)


def test_phone_schema_rejects_multiple_whitespace_in_number(valid_phone_data):
	data = valid_phone_data
	data["number"] = "9876  543210"

	with pytest.raises(ValidationError):
		PhoneSchema(**data)


def test_phone_schema_rejects_whitespace_at_both_ends_of_number(valid_phone_data):
	data = valid_phone_data
	data["number"] = "  9876543210  "

	with pytest.raises(ValidationError):
		PhoneSchema(**data)


def test_phone_schema_rejects_number_containing_only_spaces(valid_phone_data):
	data = valid_phone_data
	data["number"] = "          "

	with pytest.raises(ValidationError):
		PhoneSchema(**data)


def test_phone_schema_rejects_malformed_input_shape():
	with pytest.raises(ValidationError):
		PhoneSchema.model_validate(["+91", "9876543210"])


def test_phone_schema_ignores_unexpected_fields(valid_phone_data):
	data = valid_phone_data
	data["extension"] = "123"

	phone = PhoneSchema(**data)

	assert phone.country_code == valid_phone_data["country_code"]
	assert phone.number == valid_phone_data["number"]
	assert not hasattr(phone, "extension")


# UserRegister schema tests


@pytest.fixture
def valid_user_register_data():
	return {
		"email": "user@example.com",
		"password": "ValidPass1!x",
		"full_name": "John Smith",
		"gender": "male",
		"phone": {
			"country_code": "+91",
			"number": "9876543210",
		},
		"specialty": "Cardiology",
	}


def test_user_register_accepts_valid_data(valid_user_register_data):
	user = UserRegister(**valid_user_register_data)

	assert user.email == valid_user_register_data["email"]
	assert user.role == "doctor"
	assert user.gender == valid_user_register_data["gender"]


@pytest.mark.parametrize("role", ["admin", "assistant"])
def test_user_register_rejects_privileged_role_override(valid_user_register_data, role):
	data = {**valid_user_register_data, "role": role}

	with pytest.raises(ValidationError):
		UserRegister(**data)


# UserRegister email field tests


@pytest.mark.parametrize(
	"email",
	[
		"user@.you",
		"user@+gmail.com",
		"user@gmail..com",
		"user.example.com",
		"user@",
		"user name@example.com",
	],
)
def test_user_register_rejects_invalid_email(valid_user_register_data, email):
	data = valid_user_register_data
	data["email"] = email

	with pytest.raises(ValidationError):
		UserRegister(**data)


def test_user_register_rejects_missing_email(valid_user_register_data):
	data = valid_user_register_data
	del data["email"]

	with pytest.raises(ValidationError):
		UserRegister(**data)


def test_user_register_rejects_null_email(valid_user_register_data):
	data = valid_user_register_data
	data["email"] = None

	with pytest.raises(ValidationError):
		UserRegister(**data)


# UserRegister password field tests


@pytest.mark.parametrize(
	"password",
	[
		"Aa1!aaaaaaa",
		"aa1!aaaaaaaa",
		"AA1!AAAAAAAA",
		"Aa1!aaaaaaa ",
		"Aa1#aaaaaaaa",
	],
)
def test_user_register_rejects_invalid_password(valid_user_register_data, password):
	data = valid_user_register_data
	data["password"] = password

	with pytest.raises(ValidationError):
		UserRegister(**data)


@pytest.mark.parametrize("password", ["Aa1!aaaaaaaa", "Aa1!aaaaaaaaaaaaaa"])
def test_user_register_accepts_password_length_boundaries(valid_user_register_data, password):
	data = valid_user_register_data
	data["password"] = password

	user = UserRegister(**data)

	assert user.password == password


def test_user_register_rejects_missing_password(valid_user_register_data):
	data = valid_user_register_data
	del data["password"]

	with pytest.raises(ValidationError):
		UserRegister(**data)


def test_user_register_rejects_null_password(valid_user_register_data):
	data = valid_user_register_data
	data["password"] = None

	with pytest.raises(ValidationError):
		UserRegister(**data)


# UserRegister full_name field tests


@pytest.mark.parametrize("full_name", ["A", "John123", "John@Smith", "Jöhn Smith"])
def test_user_register_rejects_invalid_full_name(valid_user_register_data, full_name):
	data = valid_user_register_data
	data["full_name"] = full_name

	with pytest.raises(ValidationError):
		UserRegister(**data)


@pytest.mark.parametrize("full_name", ["Jo", "John Smith", "Anne-Marie O'Neil", "Dr. Stone"])
def test_user_register_accepts_valid_full_name(valid_user_register_data, full_name):
	data = valid_user_register_data
	data["full_name"] = full_name

	user = UserRegister(**data)

	assert user.full_name == full_name


def test_user_register_rejects_missing_full_name(valid_user_register_data):
	data = valid_user_register_data
	del data["full_name"]

	with pytest.raises(ValidationError):
		UserRegister(**data)


def test_user_register_rejects_null_full_name(valid_user_register_data):
	data = valid_user_register_data
	data["full_name"] = None

	with pytest.raises(ValidationError):
		UserRegister(**data)


# UserRegister gender field tests


@pytest.mark.parametrize("gender", ["male", "female", "other"])
def test_user_register_accepts_valid_gender(valid_user_register_data, gender):
	data = valid_user_register_data
	data["gender"] = gender

	user = UserRegister(**data)

	assert user.gender == gender


@pytest.mark.parametrize("gender", ["Male", " FEMALE", "other ", "unknown", 1, True])
def test_user_register_rejects_invalid_gender(valid_user_register_data, gender):
	data = valid_user_register_data
	data["gender"] = gender

	with pytest.raises(ValidationError):
		UserRegister(**data)


def test_user_register_rejects_missing_gender(valid_user_register_data):
	data = valid_user_register_data
	del data["gender"]

	with pytest.raises(ValidationError):
		UserRegister(**data)


# UserRegister phone field tests


def test_user_register_rejects_missing_phone(valid_user_register_data):
	data = valid_user_register_data
	del data["phone"]

	with pytest.raises(ValidationError):
		UserRegister(**data)


@pytest.mark.parametrize("phone", [None, "+919876543210", ["+91", "9876543210"]])
def test_user_register_rejects_invalid_phone_shape(valid_user_register_data, phone):
	data = valid_user_register_data
	data["phone"] = phone

	with pytest.raises(ValidationError):
		UserRegister(**data)


# UserRegister specialty field tests


@pytest.mark.parametrize("specialty", [None, "", "Cardiology", 123])
def test_user_register_accepts_optional_specialty_values(valid_user_register_data, specialty):
	data = valid_user_register_data
	data["specialty"] = specialty

	if isinstance(specialty, int):
		with pytest.raises(ValidationError):
			UserRegister(**data)
	else:
		user = UserRegister(**data)
		assert user.specialty == specialty


def test_user_register_accepts_missing_specialty(valid_user_register_data):
	data = valid_user_register_data
	del data["specialty"]

	user = UserRegister(**data)

	assert user.specialty is None


# UserRegister structure and type tests


@pytest.mark.parametrize(
	"field, value",
	[
		("email", 123),
		("password", 123),
		("full_name", 123),
		("gender", {"value": "male"}),
		("phone", 123),
		("specialty", ["Cardiology"]),
	],
)
def test_user_register_rejects_wrong_field_type(valid_user_register_data, field, value):
	data = valid_user_register_data
	data[field] = value

	with pytest.raises(ValidationError):
		UserRegister(**data)


def test_user_register_ignores_unexpected_fields(valid_user_register_data):
	data = valid_user_register_data
	data["unexpected"] = "ignored"

	user = UserRegister(**data)

	assert not hasattr(user, "unexpected")


def test_user_register_rejects_malformed_input_shape():
	with pytest.raises(ValidationError):
		UserRegister.model_validate(["user@example.com"])


# UserLogin schema tests


@pytest.fixture
def valid_user_login_data():
	return {
		"email": "user@example.com",
		"password": "any-password-value",
	}


def test_user_login_accepts_valid_data(valid_user_login_data):
	user_login = UserLogin(**valid_user_login_data)

	assert user_login.email == valid_user_login_data["email"]
	assert user_login.password == valid_user_login_data["password"]


@pytest.mark.parametrize("password", ["", "short", "not-a-valid-password"])
def test_user_login_accepts_any_string_password(valid_user_login_data, password):
	data = valid_user_login_data
	data["password"] = password

	user_login = UserLogin(**data)

	assert user_login.password == password


def test_user_login_rejects_missing_email(valid_user_login_data):
	data = valid_user_login_data
	del data["email"]

	with pytest.raises(ValidationError):
		UserLogin(**data)


def test_user_login_rejects_null_email(valid_user_login_data):
	data = valid_user_login_data
	data["email"] = None

	with pytest.raises(ValidationError):
		UserLogin(**data)


@pytest.mark.parametrize(
	"email",
	["user@", "user.example.com", "user@.com", "user name@example.com"],
)
def test_user_login_rejects_invalid_email(valid_user_login_data, email):
	data = valid_user_login_data
	data["email"] = email

	with pytest.raises(ValidationError):
		UserLogin(**data)


def test_user_login_rejects_missing_password(valid_user_login_data):
	data = valid_user_login_data
	del data["password"]

	with pytest.raises(ValidationError):
		UserLogin(**data)


def test_user_login_rejects_null_password(valid_user_login_data):
	data = valid_user_login_data
	data["password"] = None

	with pytest.raises(ValidationError):
		UserLogin(**data)


@pytest.mark.parametrize(
	"field, value",
	[
		("email", 123),
		("email", ["user@example.com"]),
		("password", 123),
		("password", ["password"]),
	],
)
def test_user_login_rejects_wrong_field_type(valid_user_login_data, field, value):
	data = valid_user_login_data
	data[field] = value

	with pytest.raises(ValidationError):
		UserLogin(**data)


def test_user_login_ignores_unexpected_fields(valid_user_login_data):
	data = valid_user_login_data
	data["unexpected"] = "ignored"

	user_login = UserLogin(**data)

	assert not hasattr(user_login, "unexpected")


def test_user_login_rejects_malformed_input_shape():
	with pytest.raises(ValidationError):
		UserLogin.model_validate(["user@example.com", "password"])


# RefreshRequest schema tests


@pytest.fixture
def valid_refresh_request_data():
	return {
		"refresh_token": "refresh-token-value",
	}


def test_refresh_request_accepts_valid_data(valid_refresh_request_data):
	request = RefreshRequest(**valid_refresh_request_data)

	assert request.refresh_token == valid_refresh_request_data["refresh_token"]


@pytest.mark.parametrize("refresh_token", ["", "invalid-token", "any-token-value"])
def test_refresh_request_accepts_any_string_token(valid_refresh_request_data, refresh_token):
	data = valid_refresh_request_data
	data["refresh_token"] = refresh_token

	request = RefreshRequest(**data)

	assert request.refresh_token == refresh_token


def test_refresh_request_rejects_missing_token(valid_refresh_request_data):
	data = valid_refresh_request_data
	del data["refresh_token"]

	with pytest.raises(ValidationError):
		RefreshRequest(**data)


def test_refresh_request_rejects_null_token(valid_refresh_request_data):
	data = valid_refresh_request_data
	data["refresh_token"] = None

	with pytest.raises(ValidationError):
		RefreshRequest(**data)


@pytest.mark.parametrize("refresh_token", [123, ["refresh-token"], {"token": "value"}])
def test_refresh_request_rejects_wrong_token_type(valid_refresh_request_data, refresh_token):
	data = valid_refresh_request_data
	data["refresh_token"] = refresh_token

	with pytest.raises(ValidationError):
		RefreshRequest(**data)


def test_refresh_request_ignores_unexpected_fields(valid_refresh_request_data):
	data = valid_refresh_request_data
	data["unexpected"] = "ignored"

	request = RefreshRequest(**data)

	assert not hasattr(request, "unexpected")


def test_refresh_request_rejects_malformed_input_shape():
	with pytest.raises(ValidationError):
		RefreshRequest.model_validate(["refresh-token-value"])
