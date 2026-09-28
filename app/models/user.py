import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, func, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from typing import TYPE_CHECKING

import enum

# if TYPE_CHECKING:
#     from . import MedicalRecord, ShareLink, DoctorPatientLink


class UserRole(str, enum.Enum):
    DOCTOR = "doctor"
    ADMIN = "admin"
    ASSISTANT = "assistant"


class UserGender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class User(Base):
    __tablename__ = "user"

    id              : Mapped[uuid.UUID]    = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email           : Mapped[str]          = mapped_column(String(255), unique=True, nullable=False)
    hashed_password : Mapped[str]          = mapped_column(String(255), nullable=False)
    full_name       : Mapped[str]          = mapped_column(String(255), nullable=False)
    role            : Mapped[UserRole]     = mapped_column(SAEnum(UserRole, name="test_user_role_enum"), nullable=False)
    gender          : Mapped[UserGender]   = mapped_column(SAEnum(UserGender, name="test_user_gender_enum"), nullable=False)
    country_code    : Mapped[str]          = mapped_column(String(3), nullable=False)
    phone_number    : Mapped[str]          = mapped_column(String(15), nullable=False)
    specialty       : Mapped[str]          = mapped_column(String(100), nullable=True)
    is_active       : Mapped[bool]         = mapped_column(Boolean, default=True, nullable=False)
    created_at      : Mapped[datetime]     = mapped_column(DateTime(timezone=True), server_default=func.now())