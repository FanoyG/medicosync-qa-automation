import pytest
import pytest_asyncio
from app.core.database import Base
from app.models.user import User
from testcontainers.community.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from testcontainers.community.redis import RedisContainer
from redis import asyncio as aioredis

import httpx
from main import app

@pytest.fixture(scope='session')
def postgres_container():
    with PostgresContainer('postgres:16-alpine') as postgres:
        yield postgres

@pytest_asyncio.fixture(scope='session')
async def engine(postgres_container : PostgresContainer):
    
    # Getting Raw Address From the Container.
    raw_url = postgres_container.get_connection_url()
    
    async_url = "postgresql+psycopg://" + raw_url.split('://', 1)[1]
    engine = create_async_engine(url=async_url)

    # Build the room inside the Factory (Table)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine # pass the engine.
    finally:
        await engine.dispose() # close the highway pipline.

@pytest_asyncio.fixture
async def db_session(engine):
    session_factory = async_sessionmaker(
        bind=engine,
        expire_on_commit=False
    )

    async with session_factory() as session:
        yield session
        await session.rollback()

@pytest.fixture(scope='session')
def redis_container():
    """Spins up a real Redis container ONCE for the entire test run."""
    with RedisContainer('redis:7-alpine') as redis:
        yield redis

@pytest_asyncio.fixture
async def redis_client(redis_container):
    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(redis_container.port)
    redis_url = f"redis://{host}:{port}"

    client = aioredis.from_url(url=redis_url, decode_responses=True)

    try:
        yield client
    finally:
        await client.flushdb()
        await client.aclose()

#===============================================
# TEST DATA FIXTURES
#===============================================
import uuid

@pytest.fixture
def register_payload():
    return {
        "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
        "password": "StrongPass123!",
        "full_name": "Test Doctor",
        "gender": "male",
        "phone": {"country_code": "+91", "number": "9876543210"},
    }

@pytest.fixture
def login_payload(register_payload):
    return {
        "email": register_payload["email"],
        "password": register_payload["password"],
    }

@pytest_asyncio.fixture
async def registered_user(auth_service, register_payload):
    response = await auth_service.register(register_payload)
    assert response.status_code == 200

#================================================
# SERVICES FIXTURES
#================================================
from tests.clients.services.auth_services import AuthService
@pytest.fixture
def auth_service(client):
    return AuthService(client)

#===========================================================
# CLIENT HAND OVER API TESTING
#===========================================================
from app.core.database import get_db
from app.routes.auth_routes import get_session_manager, get_token_generator
from app.services.session_service import SessionManager
from app.services.token_service import TokenGenerator

@pytest.fixture(scope="session")
def transport():
    return httpx.ASGITransport(app=app)

@pytest_asyncio.fixture
async def client(transport, db_session, redis_client):

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_session_manager] = lambda: SessionManager(redis_client=redis_client)
    app.dependency_overrides[get_token_generator] = lambda: TokenGenerator(redis_client=redis_client)

    async with httpx.AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    ) as c:
        yield c

    app.dependency_overrides.clear()