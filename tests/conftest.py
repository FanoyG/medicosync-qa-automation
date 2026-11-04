import pytest
import pytest_asyncio
from app.core.database import Base
from app.models.user import User
from testcontainers.community.postgres import PostgresContainer
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from testcontainers.community.redis import RedisContainer
from redis import asyncio as aioredis

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
        await client.close()


