"""Testes unitários para o serviço de coleta."""

import asyncio
import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.models.message import CollectedMessage, CollectionState, TelegramGroup
from src.utils.rate_limiter import TokenBucketRateLimiter


# ============================================================
# Testes do Modelo
# ============================================================

class TestCollectedMessage:
    """Testes para o modelo CollectedMessage."""

    def test_has_text_with_content(self):
        msg = CollectedMessage(
            telegram_msg_id=1,
            group_id=100,
            text="iPhone 15 por R$ 4.999",
            date=datetime.now(timezone.utc),
        )
        assert msg.has_text is True

    def test_has_text_empty(self):
        msg = CollectedMessage(
            telegram_msg_id=2,
            group_id=100,
            text="",
            date=datetime.now(timezone.utc),
        )
        assert msg.has_text is False

    def test_has_text_none(self):
        msg = CollectedMessage(
            telegram_msg_id=3,
            group_id=100,
            text=None,
            date=datetime.now(timezone.utc),
        )
        assert msg.has_text is False

    def test_idempotency_key(self):
        msg = CollectedMessage(
            telegram_msg_id=42,
            group_id=100,
            text="oferta",
            date=datetime.now(timezone.utc),
        )
        assert msg.idempotency_key == (100, 42)

    def test_idempotency_key_uniqueness(self):
        msg1 = CollectedMessage(
            telegram_msg_id=1, group_id=100,
            text="a", date=datetime.now(timezone.utc),
        )
        msg2 = CollectedMessage(
            telegram_msg_id=1, group_id=200,
            text="a", date=datetime.now(timezone.utc),
        )
        assert msg1.idempotency_key != msg2.idempotency_key

    def test_links_extraction(self):
        msg = CollectedMessage(
            telegram_msg_id=5,
            group_id=100,
            text="Compre aqui",
            date=datetime.now(timezone.utc),
            links=["https://amazon.com.br/dp/B123", "https://kabum.com.br/produto/456"],
        )
        assert len(msg.links) == 2
        assert "amazon.com.br" in msg.links[0]


class TestTelegramGroup:
    """Testes para o modelo TelegramGroup."""

    def test_creation(self):
        group = TelegramGroup(
            id=123456,
            title="Promoções Tech",
            username="promos_tech",
            member_count=5000,
        )
        assert group.id == 123456
        assert group.is_active is True


class TestCollectionState:
    """Testes para o modelo CollectionState."""

    def test_initial_state(self):
        state = CollectionState(group_id=100)
        assert state.last_message_id is None
        assert state.backfill_done is False


# ============================================================
# Testes do Rate Limiter
# ============================================================

class TestTokenBucketRateLimiter:
    """Testes para o rate limiter."""

    @pytest.mark.asyncio
    async def test_acquire_within_limit(self):
        limiter = TokenBucketRateLimiter(rate=100.0, max_tokens=100.0)
        # Deve ser instantâneo
        await limiter.acquire(1.0)
        assert True  # Se chegou aqui, não bloqueou

    @pytest.mark.asyncio
    async def test_acquire_respects_capacity(self):
        limiter = TokenBucketRateLimiter(rate=10.0, max_tokens=5.0)
        # Consome todos os tokens
        for _ in range(5):
            await limiter.acquire(1.0)
        # Próximo deve causar espera (mas com rate=10, a espera é curta)
        await limiter.acquire(1.0)

    @pytest.mark.asyncio
    async def test_token_refill(self):
        limiter = TokenBucketRateLimiter(rate=1000.0, max_tokens=10.0)
        # Esgota tokens
        for _ in range(10):
            await limiter.acquire(1.0)
        # Espera um pouquinho para recarregar
        await asyncio.sleep(0.02)
        # Deve conseguir adquirir novamente
        await limiter.acquire(1.0)


# ============================================================
# Testes do Retry
# ============================================================

class TestRetry:
    """Testes para o decorator de retry."""

    @pytest.mark.asyncio
    async def test_retry_succeeds_after_failure(self):
        from src.utils.retry import async_retry

        call_count = 0

        @async_retry(max_retries=3, base_delay=0.01, retryable_exceptions=(ValueError,))
        async def flaky_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("falhou")
            return "sucesso"

        result = await flaky_function()
        assert result == "sucesso"
        assert call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exhausted(self):
        from src.utils.retry import async_retry

        @async_retry(max_retries=2, base_delay=0.01, retryable_exceptions=(ValueError,))
        async def always_fails():
            raise ValueError("sempre falha")

        with pytest.raises(ValueError, match="sempre falha"):
            await always_fails()

    @pytest.mark.asyncio
    async def test_retry_non_retryable_exception(self):
        from src.utils.retry import async_retry

        @async_retry(max_retries=3, base_delay=0.01, retryable_exceptions=(ValueError,))
        async def raises_type_error():
            raise TypeError("tipo errado")

        with pytest.raises(TypeError):
            await raises_type_error()


# ============================================================
# Testes de Integração Simulados (Repository)
# ============================================================

class TestMessageRepository:
    """Testes para o repositório com mock do pool."""

    @pytest.mark.asyncio
    async def test_insert_message_success(self):
        mock_pool = AsyncMock()
        mock_pool.execute = AsyncMock(return_value=None)

        from src.db.repository import MessageRepository
        repo = MessageRepository(mock_pool)

        msg = CollectedMessage(
            telegram_msg_id=1,
            group_id=100,
            text="Galaxy S24 por R$ 3.499",
            date=datetime.now(timezone.utc),
            author_id=999,
            author_name="Bot Promos",
            links=["https://amzn.to/abc123"],
        )

        result = await repo.insert_message(msg)
        assert result is True
        mock_pool.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count_messages(self):
        mock_pool = AsyncMock()
        mock_pool.fetchrow = AsyncMock(return_value={"cnt": 42})

        from src.db.repository import MessageRepository
        repo = MessageRepository(mock_pool)

        count = await repo.count_messages()
        assert count == 42


# ============================================================
# Testes de Mensagens de Promoção (Fixture de dados reais)
# ============================================================

class TestPromotionMessages:
    """Valida que mensagens reais de promoção são tratadas corretamente."""

    SAMPLE_MESSAGES = [
        {
            "text": "🔥 iPhone 15 Pro Max 256GB por R$ 6.499,00 à vista no PIX\n"
                    "Ou 12x de R$ 599,92\n"
                    "Frete grátis | Cupom: TECH10\n"
                    "https://www.magazineluiza.com.br/iphone-15/p/abc123",
            "expected_links": 1,
        },
        {
            "text": "Notebook Lenovo IdeaPad 3 - Ryzen 5 / 8GB / 256GB SSD\n"
                    "De R$ 3.299,00 por R$ 2.499,00 (24% OFF)\n"
                    "10x sem juros de R$ 249,90\n"
                    "https://amzn.to/3xyzABC",
            "expected_links": 1,
        },
        {
            "text": "⚡ RELÂMPAGO ⚡\n"
                    "Air Fryer Mondial 5L - R$ 199,90\n"
                    "Shopee: https://shope.ee/abc123\n"
                    "Kabum: https://www.kabum.com.br/produto/456",
            "expected_links": 2,
        },
        {
            "text": "Apenas uma mensagem sem oferta, pessoal.",
            "expected_links": 0,
        },
    ]

    def test_link_count_extraction(self):
        import re
        url_pattern = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)

        for sample in self.SAMPLE_MESSAGES:
            links = url_pattern.findall(sample["text"])
            assert len(links) == sample["expected_links"], (
                f"Esperava {sample['expected_links']} links, encontrou {len(links)} "
                f"em: {sample['text'][:50]}..."
            )

    def test_message_model_from_sample(self):
        import re
        url_pattern = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)

        for i, sample in enumerate(self.SAMPLE_MESSAGES):
            links = url_pattern.findall(sample["text"])
            msg = CollectedMessage(
                telegram_msg_id=i + 1,
                group_id=100,
                text=sample["text"],
                date=datetime.now(timezone.utc),
                links=links,
            )
            assert msg.has_text is True
            assert len(msg.links) == sample["expected_links"]
