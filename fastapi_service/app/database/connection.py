import asyncpg
import logging
from typing import Optional
from app.config import settings

_logger = logging.getLogger(__name__)

# Global connection pool
_pool: Optional[asyncpg.Pool] = None


async def init_db():
    """Initialize database connection pool"""
    global _pool
    try:
        _pool = await asyncpg.create_pool(
            settings.database_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        _logger.info("Database connection pool initialized")
        
        # Test connection
        async with _pool.acquire() as conn:
            await conn.execute("SELECT 1")
            _logger.info("Database connection test successful")
            
    except Exception as e:
        _logger.error(f"Failed to initialize database: {str(e)}")
        raise


async def close_db():
    """Close database connection pool"""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        _logger.info("Database connection pool closed")


async def get_database() -> asyncpg.Pool:
    """Get database connection pool"""
    global _pool
    if not _pool:
        await init_db()
    return _pool


async def execute_query(query: str, *args, fetch_one: bool = False, fetch_all: bool = False):
    """Execute a database query"""
    pool = await get_database()
    async with pool.acquire() as conn:
        if fetch_one:
            return await conn.fetchrow(query, *args)
        elif fetch_all:
            return await conn.fetch(query, *args)
        else:
            return await conn.execute(query, *args)
