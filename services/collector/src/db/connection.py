"""Pool de conexões PostgreSQL com asyncpg."""

from __future__ import annotations

import asyncpg
from asyncpg import Pool

from src.core.config import db_config
from src.core.logging import get_logger

logger = get_logger(__name__)

_pool: Pool | None = None


async def get_pool() -> Pool:
    """Retorna o pool de conexões, criando se necessário."""
    global _pool
    if _pool is None:
        logger.info("Criando pool de conexões PostgreSQL", extra={"operation": "db_connect"})
        _pool = await asyncpg.create_pool(
            dsn=db_config.dsn,
            min_size=2,
            max_size=10,
            command_timeout=30,
        )
        logger.info("Pool criado com sucesso")
    return _pool


async def close_pool() -> None:
    """Fecha o pool de conexões."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("Pool de conexões fechado")
