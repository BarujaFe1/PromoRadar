"""Serviço de backfill — coleta histórico de mensagens de um grupo."""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone

from src.core.config import telegram_config
from src.core.logging import get_logger
from src.db.repository import MessageRepository
from src.models.message import CollectionState
from src.services.telegram_client import TelegramCollector

logger = get_logger(__name__)


class BackfillService:
    """
    Coleta mensagens históricas de grupos do Telegram.

    Estratégia:
    1. Verifica estado de coleta do grupo (cursor)
    2. Busca mensagens em lotes do mais recente ao mais antigo
    3. Salva cada lote no banco com idempotência
    4. Atualiza cursor a cada lote
    5. Respeita rate limits com delays entre lotes
    """

    def __init__(
        self,
        collector: TelegramCollector,
        repository: MessageRepository,
    ) -> None:
        self._collector = collector
        self._repo = repository

    async def backfill_group(self, group_id: int) -> int:
        """
        Executa backfill completo de um grupo.

        Returns:
            Total de novas mensagens inseridas.
        """
        start_time = time.monotonic()
        total_inserted = 0

        # Verifica se já tem estado de coleta
        state = await self._repo.get_collection_state(group_id)
        if state and state.backfill_done:
            logger.info(
                f"Backfill já concluído para grupo {group_id}, pulando",
                extra={"group_id": group_id, "operation": "backfill_skip"},
            )
            return 0

        logger.info(
            f"Iniciando backfill do grupo {group_id}",
            extra={"group_id": group_id, "operation": "backfill_start"},
        )

        # Itera sobre todos os lotes de mensagens
        async for batch in self._collector.iter_all_messages(group_id):
            if not batch:
                break

            # Insere lote no banco
            inserted = await self._repo.insert_messages_batch(batch)
            total_inserted += inserted

            # Atualiza estado de coleta com a mensagem mais recente do lote
            newest_msg = max(batch, key=lambda m: m.telegram_msg_id)
            await self._repo.update_collection_state(
                CollectionState(
                    group_id=group_id,
                    last_message_id=newest_msg.telegram_msg_id,
                    last_collected=datetime.now(timezone.utc),
                    backfill_done=False,
                )
            )

            # Delay entre lotes para não sobrecarregar
            await asyncio.sleep(telegram_config.backfill_delay_sec)

        # Marca backfill como concluído
        await self._repo.update_collection_state(
            CollectionState(
                group_id=group_id,
                last_message_id=state.last_message_id if state else None,
                last_collected=datetime.now(timezone.utc),
                backfill_done=True,
            )
        )

        elapsed = time.monotonic() - start_time
        logger.info(
            f"Backfill concluído para grupo {group_id}: {total_inserted} mensagens em {elapsed:.1f}s",
            extra={
                "group_id": group_id,
                "count": total_inserted,
                "duration_ms": int(elapsed * 1000),
                "operation": "backfill_complete",
            },
        )
        return total_inserted

    async def backfill_all_groups(self, group_ids: list[int]) -> dict[int, int]:
        """Executa backfill sequencial para múltiplos grupos."""
        results: dict[int, int] = {}
        for gid in group_ids:
            try:
                count = await self.backfill_group(gid)
                results[gid] = count
            except Exception:
                logger.error(
                    f"Erro no backfill do grupo {gid}",
                    extra={"group_id": gid, "operation": "backfill_error"},
                    exc_info=True,
                )
                results[gid] = -1
        return results
