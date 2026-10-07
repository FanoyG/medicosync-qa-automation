from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import PasswordHandler
from app.core.redis_client import redis_client
from app.services.session_service import SessionManager
from app.services.token_service import TokenGenerator
from app.services.auth_orchestrator import AuthOrchestrator
from app.repository.auth_repo import UserRepository
from app.schemas.auth_schemas import UserRegister, UserLogin, RefreshRequest

router = APIRouter()

GLOBAL_PWD_HANDLER = PasswordHandler()
GLOBAL_SESSION_MGR = SessionManager(redis_client=redis_client)
GLOBAL_TOKEN_GEN = TokenGenerator(redis_client=redis_client)


def get_user_repository(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)


def get_auth_orchestrator(
    repo: UserRepository = Depends(get_user_repository),
) -> AuthOrchestrator:
    return AuthOrchestrator(GLOBAL_PWD_HANDLER, GLOBAL_SESSION_MGR, repo, GLOBAL_TOKEN_GEN)


@router.post("/auth/register")
async def register_endpoint(payload: UserRegister, orchestrator: AuthOrchestrator = Depends(get_auth_orchestrator)):
    result = await orchestrator.register_user(
        email=payload.email, plain_pwd=payload.password, username=payload.full_name,
        gender=payload.gender,
        country_code=payload.phone.country_code, phone_number=payload.phone.number,
    )
    await orchestrator.user_reg.db.commit()
    return result


@router.post("/auth/login")
async def login_endpoint(payload: UserLogin, orchestrator: AuthOrchestrator = Depends(get_auth_orchestrator)):
    return await orchestrator.login_user(email=payload.email, plain_pwd=payload.password)


@router.post("/auth/refresh")
async def refresh_endpoint(payload: RefreshRequest, orchestrator: AuthOrchestrator = Depends(get_auth_orchestrator)):
    return await orchestrator.refresh_access_token(refresh_token_str=payload.refresh_token)