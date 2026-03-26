"""Serviço de ingestão em tempo real — captura novas mensagens via event handler."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from telethon import events

from src.core.config import app_config
from src.core.logging import get_logger
from src.db.repository import MessageRepository
from src.models.message import CollectionState
from src.services.telegram_client import TelegramCollector

logger = get_logger(__name__)


class RealtimeService:
    """
    Escuta novas mensagens nos grupos monitorados em tempo real.

    Usa o event handler do Telethon para capturar mensagens assim que
    chegam, sem necessidade de polling.
    """

    def __init__(
        self,
        collector: TelegramCollector,
        repository: MessageRepository,
    ) -> None:
        self._collector = collector
        self._repo = repository
        self._running = False
        self._messages_processed = 0

    async def start(self, group_ids: list[int] | None = None) -> None:
        """
        Inicia a escuta em tempo real.

        Args:
            group_ids: IDs dos grupos para monitorar. Se None, monitora todos.
        """
        self._running = True
        client = self._collector.client

        # Filtra por grupos específicos se fornecido
        chats = group_ids if group_ids else None

        @client.on(events.NewMessage(chats=chats))
        async def handler(event: events.NewMessage.Event) -> None:
            await self._handle_new_message(event)

        logger.info(
            f"Escuta em tempo real iniciada para {len(group_ids) if group_ids else 'todos os'} grupo(s)",
            extra={
                "operation": "realtime_start",
                "count": len(group_ids) if group_ids else 0,
            },
        )

        # Mantém o client rodando
        try:
            while self._running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Escuta em tempo real cancelada")
        finally:
            self._running = False

    async def stop(self) -> None:
        """Para a escuta em tempo real."""
        self._running = False
        logger.info(
            f"Escuta em tempo real parada. Total processado: {self._messages_processed}",
            extra={"count": self._messages_processed, "operation": "realtime_stop"},
        )

    async def _handle_new_message(self, event: events.NewMessage.Event) -> None:
        """Processa uma nova mensagem recebida."""
        try:
            msg = event.message
            group_id = event.chat_id

            # Converte para modelo de domínio
            collected = self._collector._convert_message(msg, group_id)
            if not collected:
                return

            # Ignora mensagens sem texto (apenas mídia sem caption)
            if not collected.has_text:
                return

            # Insere no banco com idempotência
            was_new = await self._repo.insert_message(collected)

            if was_new:
                self._messages_processed += 1

                # Atualiza estado de coleta
                await self._repo.update_collection_state(
                    CollectionState(
                        group_id=group_id,
                        last_message_id=collected.telegram_msg_id,
                        last_collected=datetime.now(timezone.utc),
                        backfill_done=True,  # não afeta backfill
                    )
                )

                logger.info(
                    f"Nova mensagem coletada",
                    extra={
                        "group_id": group_id,
                        "message_id": collected.telegram_msg_id,
                        "operation": "realtime_message",
                    },
                )

        except Exception:
            logger.error(
                "Erro ao processar mensagem em tempo real",
                extra={"operation": "realtime_error"},
                exc_info=True,
            )
