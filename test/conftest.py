import asyncio
import sys
import pytest
from testcontainers.community.postgres import PostgresContainer
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from testcontainers.community.redis import RedisContainer
import redis.asyncio as aioredis

if sys.platform == "win32":
    # psycopg 3 does not support the default Windows ProactorEventLoop in async mode.
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.core.database import Base
from app.models.user import User  # noqa: F401  (Base ko model dikhane ke liye)

@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres


@pytest_asyncio.fixture(scope="session")
async def engine(postgres_container):
    raw_url = postgres_container.get_connection_url()
    async_url = "postgresql+psycopg://" + raw_url.split("://", 1)[1]
    engine = create_async_engine(async_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(engine):
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()

    async with engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            await conn.execute(table.delete())


@pytest.fixture(scope="session")
def redis_container():
    """Spins up a real Redis container ONCE for the entire test run."""
    with RedisContainer("redis:7-alpine") as redis_container:
        yield redis_container

@pytest.fixture
async def redis_client(redis_container):
    """Provides a fresh, connected async Redis client per test case."""

    host = redis_container.get_container_host_ip()
    port = redis_container.get_exposed_port(redis_container.port)

    client = aioredis.Redis(host=host, port=int(port), decode_responses=True)
    yield client

    await client.flushdb()
    await client.close()