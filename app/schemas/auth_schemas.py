import re
from typing import Literal
from pydantic import BaseModel, EmailStr, Field, field_validator


class PhoneSchema(BaseModel):
    country_code: str = Field(..., description="Example: +91 or +1")
    number: str = Field(..., min_length=4, max_length=15)

    @field_validator("number")
    @classmethod
    def validate_number_digits(cls, v: str) -> str:
        if not v.isdigit():
            raise ValueError("Phone number must contain only digits")
        return v


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=18)
    full_name: str = Field(min_length=2)
    role: Literal["doctor"] = "doctor"
    gender: Literal["male", "female", "other"]
    phone: PhoneSchema
    specialty: str | None = None

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role_case(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        pattern = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{12,18}$"
        if not re.match(pattern, v):
            raise ValueError("Password must contain uppercase, lowercase, a number, and a special character.")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_name_characters(cls, v: str) -> str:
        if not re.match(r"^[A-Za-z\s\.\-\']+$", v):
            raise ValueError("Name can only contain letters, spaces, periods, hyphens, or apostrophes.")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str