from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import os
from dotenv import load_dotenv

load_dotenv()

# Use PostgreSQL if available, otherwise SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./vocalprint.db")

# Adjust engine parameters based on database type
if DATABASE_URL.startswith("postgresql"):
    # SQLAlchemy asyncpg requires 'postgresql+asyncpg://'
    if not DATABASE_URL.startswith("postgresql+asyncpg://"):
        DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    engine = create_async_engine(DATABASE_URL, echo=True)
else:
    engine = create_async_engine(DATABASE_URL, echo=True)

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
