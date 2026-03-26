"""Retry com exponential backoff para chamadas à API do Telegram."""

from __future__ import annotations

import asyncio
import functools
import random
from typing import Any, Callable, TypeVar

from src.core.logging import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def async_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """
    Decorator para retry assíncrono com backoff exponencial + jitter.

    Args:
        max_retries: número máximo de tentativas
        base_delay: delay base em segundos
        max_delay: delay máximo em segundos (cap)
        exponential_base: base da exponencial
        jitter: adiciona variação aleatória ao delay
        retryable_exceptions: tupla de exceções que disparam retry
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            last_exception: Exception | None = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as exc:
                    last_exception = exc

                    if attempt == max_retries:
                        logger.error(
                            f"Todas as {max_retries + 1} tentativas falharam para {func.__name__}",
                            extra={"operation": "retry_exhausted"},
                            exc_info=True,
                        )
                        raise

                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay,
                    )
                    if jitter:
                        delay = delay * (0.5 + random.random())

                    logger.warning(
                        f"Tentativa {attempt + 1}/{max_retries + 1} falhou para {func.__name__}: {exc}. "
                        f"Retentando em {delay:.1f}s",
                        extra={"operation": "retry", "duration_ms": int(delay * 1000)},
                    )
                    await asyncio.sleep(delay)

            raise last_exception  # type: ignore[misc]

        return wrapper  # type: ignore[return-value]

    return decorator
