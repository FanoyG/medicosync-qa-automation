class SessionManager:
    MAX_ATTEMPTS = 5
    LOCKOUT_DURATION = 300

    def __init__(self, redis_client):
        self.redis = redis_client

    async def is_locked_out(self, identifier: str) -> bool:
        if not identifier:
            return False
        return await self.redis.exists(f"lockout:{identifier}") == 1

    async def record_failed_attempt(self, identifier: str) -> None:
        if not identifier:
            raise ValueError("No identifier provided.")
        new_count = await self.redis.incr(f"failed_attempts:{identifier}")
        if new_count >= self.MAX_ATTEMPTS:
            await self.redis.set(f"lockout:{identifier}", "1", ex=self.LOCKOUT_DURATION)

    async def reset_attempts(self, identifier: str) -> None:
        await self.redis.delete(f"failed_attempts:{identifier}", f"lockout:{identifier}")