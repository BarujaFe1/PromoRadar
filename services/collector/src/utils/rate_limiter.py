"""Rate limiter com token bucket para respeitar limites da API do Telegram."""

from __future__ import annotations

import asyncio
import time

from src.core.logging import get_logger

logger = get_logger(__name__)


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter assíncrono.

    O Telegram aplica flood wait para requisições muito frequentes.
    Esse limiter garante que não ultrapassemos um número seguro de
    chamadas por segundo.

    Referência: Telegram recomenda ~30 requests/segundo para User API.
    Usamos um padrão mais conservador: 20 req/s.
    """

    def __init__(
        self,
        rate: float = 20.0,      # tokens por segundo
        max_tokens: float = 20.0,  # capacidade máxima do bucket
    ) -> None:
        self._rate = rate
        self._max_tokens = max_tokens
        self._tokens = max_tokens
        self._last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        """Repõe tokens baseado no tempo decorrido."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(
            self._max_tokens,
            self._tokens + elapsed * self._rate,
        )
        self._last_refill = now

    async def acquire(self, tokens: float = 1.0) -> None:
        """Aguarda até que tokens suficientes estejam disponíveis."""
        async with self._lock:
            while True:
                self._refill()
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return

                # Calcula quanto tempo esperar
                deficit = tokens - self._tokens
                wait_time = deficit / self._rate
                logger.debug(
                    f"Rate limit: aguardando {wait_time:.2f}s para {tokens} token(s)",
                    extra={"operation": "rate_limit_wait", "duration_ms": int(wait_time * 1000)},
                )
                await asyncio.sleep(wait_time)


class FloodWaitHandler:
    """
    Tratamento específico para FloodWaitError do Telegram.

    Quando o Telegram retorna FloodWaitError, devemos esperar
    exatamente o tempo indicado antes de tentar novamente.
    """

    @staticmethod
    async def handle_flood_wait(wait_seconds: int) -> None:
        """Aguarda o tempo de flood wait com log."""
        logger.warning(
            f"FloodWaitError do Telegram: aguardando {wait_seconds}s",
            extra={
                "operation": "flood_wait",
                "duration_ms": wait_seconds * 1000,
            },
        )
        # Adiciona 1s de margem
        await asyncio.sleep(wait_seconds + 1)


# Singleton para uso global
rate_limiter = TokenBucketRateLimiter()
flood_handler = FloodWaitHandler()
