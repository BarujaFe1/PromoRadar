"""Wrapper sobre o Telethon com rate limiting e conversão de entidades."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import AsyncGenerator

from telethon import TelegramClient
from telethon.errors import FloodWaitError
from telethon.tl.types import Channel, Chat, Message, User

from src.core.config import telegram_config
from src.core.logging import get_logger
from src.models.message import CollectedMessage, TelegramGroup
from src.utils.rate_limiter import flood_handler, rate_limiter
from src.utils.retry import async_retry

logger = get_logger(__name__)

# Regex para extrair URLs de texto
URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)


class TelegramCollector:
    """
    Cliente Telegram de alto nível para coleta de mensagens.

    Encapsula Telethon com:
    - Rate limiting via token bucket
    - Tratamento de FloodWaitError
    - Conversão de entidades Telegram → modelos de domínio
    - Retry automático
    """

    def __init__(self) -> None:
        self._client: TelegramClient | None = None

    async def connect(self) -> None:
        """Inicializa e autentica o cliente Telegram."""
        self._client = TelegramClient(
            telegram_config.session_name,
            telegram_config.api_id,
            telegram_config.api_hash,
        )
        await self._client.start(phone=telegram_config.phone)
        me = await self._client.get_me()
        logger.info(
            f"Conectado ao Telegram como {me.first_name} ({me.id})",
            extra={"operation": "telegram_connect"},
        )

    async def disconnect(self) -> None:
        """Desconecta o cliente."""
        if self._client:
            await self._client.disconnect()
            logger.info("Desconectado do Telegram")

    @property
    def client(self) -> TelegramClient:
        if not self._client:
            raise RuntimeError("Cliente Telegram não conectado. Chame connect() primeiro.")
        return self._client

    async def list_groups(self) -> list[TelegramGroup]:
        """Lista todos os grupos/canais dos quais o usuário participa."""
        await rate_limiter.acquire()
        groups: list[TelegramGroup] = []

        async for dialog in self.client.iter_dialogs():
            entity = dialog.entity
            if isinstance(entity, (Channel, Chat)):
                group = TelegramGroup(
                    id=entity.id,
                    title=dialog.title or "Sem título",
                    username=getattr(entity, "username", None),
                    member_count=getattr(entity, "participants_count", None),
                )
                groups.append(group)

        logger.info(
            f"Encontrados {len(groups)} grupos/canais",
            extra={"count": len(groups), "operation": "list_groups"},
        )
        return groups

    @async_retry(max_retries=3, base_delay=2.0, retryable_exceptions=(Exception,))
    async def fetch_messages(
        self,
        group_id: int,
        limit: int = 100,
        offset_id: int = 0,
        min_id: int = 0,
    ) -> list[CollectedMessage]:
        """
        Busca mensagens de um grupo com rate limiting.

        Args:
            group_id: ID do grupo/canal
            limit: quantidade máxima de mensagens
            offset_id: ID da mensagem para paginação (mensagens ANTES desse ID)
            min_id: ID mínimo (não busca mensagens com ID menor que esse)
        """
        await rate_limiter.acquire(tokens=2)  # fetch consome mais quota

        try:
            messages: list[CollectedMessage] = []
            async for msg in self.client.iter_messages(
                group_id,
                limit=limit,
                offset_id=offset_id,
                min_id=min_id,
            ):
                collected = self._convert_message(msg, group_id)
                if collected:
                    messages.append(collected)

            return messages

        except FloodWaitError as e:
            await flood_handler.handle_flood_wait(e.seconds)
            raise  # retry decorator vai tentar de novo

    async def iter_all_messages(
        self,
        group_id: int,
        offset_id: int = 0,
        batch_size: int | None = None,
    ) -> AsyncGenerator[list[CollectedMessage], None]:
        """
        Iterator que busca TODAS as mensagens de um grupo em lotes.
        Usado para backfill histórico.

        Yields lotes de mensagens do mais recente para o mais antigo.
        """
        if batch_size is None:
            batch_size = telegram_config.backfill_batch_size

        current_offset = offset_id
        total_fetched = 0

        while True:
            await rate_limiter.acquire(tokens=2)

            try:
                batch: list[CollectedMessage] = []
                async for msg in self.client.iter_messages(
                    group_id,
                    limit=batch_size,
                    offset_id=current_offset,
                ):
                    collected = self._convert_message(msg, group_id)
                    if collected:
                        batch.append(collected)

                if not batch:
                    logger.info(
                        f"Backfill completo para grupo {group_id}: {total_fetched} mensagens",
                        extra={"group_id": group_id, "count": total_fetched, "operation": "backfill_done"},
                    )
                    break

                # Atualiza offset para a mensagem mais antiga do lote
                current_offset = min(m.telegram_msg_id for m in batch)
                total_fetched += len(batch)

                logger.info(
                    f"Lote de {len(batch)} mensagens (total: {total_fetched})",
                    extra={
                        "group_id": group_id,
                        "count": len(batch),
                        "operation": "backfill_batch",
                    },
                )

                yield batch

            except FloodWaitError as e:
                await flood_handler.handle_flood_wait(e.seconds)
                continue

    def _convert_message(self, msg: Message, group_id: int) -> CollectedMessage | None:
        """Converte Message do Telethon para modelo de domínio."""
        if msg is None:
            return None

        # Extrai texto
        text = msg.text or msg.message or ""

        # Extrai links do texto
        links = URL_PATTERN.findall(text) if text else []

        # Identifica tipo de mídia
        media_type = None
        if msg.photo:
            media_type = "photo"
        elif msg.video:
            media_type = "video"
        elif msg.document:
            media_type = "document"

        # Autor
        author_id = None
        author_name = None
        if msg.sender:
            author_id = msg.sender_id
            if isinstance(msg.sender, User):
                parts = [msg.sender.first_name or "", msg.sender.last_name or ""]
                author_name = " ".join(p for p in parts if p).strip() or None

        # Garante timezone
        msg_date = msg.date
        if msg_date and msg_date.tzinfo is None:
            msg_date = msg_date.replace(tzinfo=timezone.utc)

        return CollectedMessage(
            telegram_msg_id=msg.id,
            group_id=group_id,
            text=text if text else None,
            date=msg_date or datetime.now(timezone.utc),
            author_id=author_id,
            author_name=author_name,
            links=links,
            media_type=media_type,
            reply_to_msg_id=msg.reply_to_msg_id if msg.reply_to else None,
            raw_json={"id": msg.id, "peer_id": str(group_id)},
        )
