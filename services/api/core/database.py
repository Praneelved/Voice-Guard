import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in environment variables")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True to log SQL queries
    future=True,
    pool_pre_ping=True
)

async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def get_db() -> AsyncSession:
    """FastAPI dependency for database sessions"""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
