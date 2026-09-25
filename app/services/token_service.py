import os
import time
import uuid
import jwt
from app.core.config import settings

class TokenGenerator:

    SECRET_KEY = os.getenv("JWT_SECRET_KEY", "medicoSync_fallback_secure_key_1111111")
    ALGORITHM = "HS256"

    def __init__(self, redis_client):
        self.redis = redis_client

    def create_access_token(self, user_id: str, role: str) -> str:
        payload = {
            "sub": user_id,
            "role": role,
            "iat": int(time.time()),
            "exp": int(time.time()) + (settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
        }
        return jwt.encode(payload, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def gen_refresh_token(self) -> str:
        return str(uuid.uuid4())

    async def cache_refresh_token(self, user_id: str, role: str) -> str:
        token_string = self.gen_refresh_token()
        await self.redis.hset(f"refresh:{token_string}", mapping={"user_id": user_id, "role": role})
        await self.redis.expire(
            f"refresh:{token_string}", settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        return token_string

    async def rotate_access_token(self, refresh_token_str: str) -> dict:
        redis_key = f"refresh:{refresh_token_str}"
        stored_data = await self.redis.hgetall(redis_key)

        if not stored_data:
            raise ValueError("Refresh token invalid or expired.")

        user_id = stored_data.get("user_id")
        role = stored_data.get("role")

        new_access_token = self.create_access_token(user_id=user_id, role=role)

        return {"access_token": new_access_token}