"""Database connection pool manager with graceful degradation."""

import asyncpg
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DatabasePool:
    """Singleton connection pool manager for PostgreSQL."""

    _instance: Optional[asyncpg.Pool] = None
    _available: bool = False

    @classmethod
    async def get_pool(cls) -> asyncpg.Pool:
        """
        Get or create the database connection pool.

        Returns:
            asyncpg.Pool: Active connection pool

        Raises:
            RuntimeError: If database is unavailable and pool cannot be created
        """
        if cls._instance is None:
            cls._instance = await cls._create_pool()
        return cls._instance

    @classmethod
    async def _create_pool(cls) -> asyncpg.Pool:
        """
        Create an optimized connection pool.

        Configuration optimized for:
        - 15-20 minute daily sessions
        - Sub-second query performance (<500ms p95)
        - Multiple rapid tool calls
        """
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError(
                "DATABASE_URL environment variable not set. "
                "Please configure in .env file."
            )

        try:
            pool = await asyncpg.create_pool(
                dsn=database_url,
                # Connection limits
                min_size=2,  # Always keep 2 connections warm
                max_size=10,  # Max 10 concurrent connections

                # Performance tuning
                max_queries=50000,  # Recycle after 50k queries
                max_inactive_connection_lifetime=300.0,  # 5 min idle timeout

                # Timeouts for sub-second goal
                command_timeout=5.0,  # 5s query timeout (fail fast)
                timeout=10.0,  # 10s connection timeout

                # Connection setup
                setup=cls._setup_connection,
            )

            # Test connection
            async with pool.acquire() as conn:
                await conn.fetchval('SELECT 1')

            cls._available = True
            logger.info("Database connection pool initialized successfully")
            return pool

        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            cls._available = False
            raise RuntimeError(
                f"Database unavailable: {e}. "
                "Please ensure PostgreSQL is running and DATABASE_URL is correct."
            )

    @staticmethod
    async def _setup_connection(conn: asyncpg.Connection):
        """Configure each connection on creation."""
        # Set search path
        await conn.execute("SET search_path TO public")

    @classmethod
    async def close(cls):
        """Close the connection pool gracefully."""
        if cls._instance:
            await cls._instance.close()
            cls._instance = None
            cls._available = False
            logger.info("Database connection pool closed")

    @classmethod
    def is_available(cls) -> bool:
        """Check if database is available."""
        return cls._available


# Global instance for easy access
_pool_instance: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """
    Convenience function to get database pool.

    Returns:
        asyncpg.Pool: Active connection pool

    Raises:
        RuntimeError: If database is unavailable
    """
    return await DatabasePool.get_pool()


async def close_db_pool():
    """Convenience function to close database pool."""
    await DatabasePool.close()


def is_db_available() -> bool:
    """
    Check if database is available.

    Returns:
        bool: True if database connection pool is active
    """
    return DatabasePool.is_available()
