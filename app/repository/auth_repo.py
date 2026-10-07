from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, UserGender, UserRole


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def is_email_taken(self, email: str) -> bool:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none() is not None

    async def add_user(self, email: str, hashed_password: str, username: str,
                        role: str, gender: str, country_code: str, phone_number: str) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=username,
            role=UserRole(role),
            gender=UserGender(gender),
            country_code=country_code,
            phone_number=phone_number,
        )
        self.db.add(user)
        await self.db.flush()  # id generate karne ke liye, commit route/controller karega
        return user

    async def get_user_by_email(self, email: str) -> User | None:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> User | None:
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()