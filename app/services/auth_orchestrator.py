from app.core.security import PasswordHandler
from app.services.session_service import SessionManager
from app.services.token_service import TokenGenerator
from app.repository.auth_repo import UserRepository


class AuthOrchestrator:
    def __init__(self, pwd_handler: PasswordHandler, session_mgr: SessionManager,
                 user_reg: UserRepository, token_gen: TokenGenerator):
        self.pwd_handler = pwd_handler
        self.session_mgr = session_mgr
        self.user_reg = user_reg
        self.token_gen = token_gen

    async def register_user(self, email: str, plain_pwd: str, username: str, role: str,
                            gender: str, country_code: str, phone_number: str) -> dict:
        if await self.user_reg.is_email_taken(email=email):
            raise ValueError("Account already exists with this email.")

        hashed_pwd = self.pwd_handler.hash_plain_pwd(pln_pwd=plain_pwd)
        user = await self.user_reg.add_user(
            email=email, hashed_password=hashed_pwd, username=username,
            role=role, gender=gender, country_code=country_code, phone_number=phone_number,
        )

        access_token = self.token_gen.create_access_token(user_id=str(user.id), role=role)
        refresh_token = await self.token_gen.cache_refresh_token(user_id=str(user.id), role=role)
        return {"message": "Registration successful", "user_id": str(user.id),
                "access_token": access_token, "refresh_token": refresh_token}

    async def login_user(self, email: str, plain_pwd: str) -> dict:
        if await self.session_mgr.is_locked_out(email):
            raise PermissionError("Too many attempts. Locked out.")

        user = await self.user_reg.get_user_by_email(email=email)
        if not user:
            raise ValueError("Invalid credentials provided.")

        if self.pwd_handler.verify_pwd(pln_pwd=plain_pwd, stored_hash=user.hashed_password):
            await self.session_mgr.reset_attempts(identifier=email)

            #Saftey check if user.role have .value property.
            user_role = user.role.value if hasattr(user.role, "value") else user.role
            access_token = self.token_gen.create_access_token(user_id=str(user.id), role=user_role)
            refresh_token = await self.token_gen.cache_refresh_token(user_id=str(user.id), role=user_role)
            return {"message": "Login successful", "user_id": str(user.id),
                    "access_token": access_token, "refresh_token": refresh_token}
        else:
            await self.session_mgr.record_failed_attempt(identifier=email)
            raise ValueError("Invalid credentials provided.")

    async def refresh_access_token(self, refresh_token_str: str) -> dict:
        return await self.token_gen.rotate_access_token(refresh_token_str=refresh_token_str)