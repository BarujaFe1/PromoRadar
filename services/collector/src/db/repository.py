"""Repositório — camada de acesso a dados com idempotência."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from asyncpg import Pool, UniqueViolationError

from src.core.logging import get_logger
from src.models.message import CollectedMessage, CollectionState, TelegramGroup

logger = get_logger(__name__)


class MessageRepository:
    """Operações de persistência para mensagens coletadas."""

    def __init__(self, pool: Pool) -> None:
        self._pool = pool

    async def upsert_group(self, group: TelegramGroup) -> None:
        """Insere ou atualiza um grupo monitorado."""
        await self._pool.execute(
            """
            INSERT INTO groups (id, title, username, member_count, is_active, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (id) DO UPDATE SET
                title = EXCLUDED.title,
                username = EXCLUDED.username,
                member_count = EXCLUDED.member_count,
                updated_at = EXCLUDED.updated_at
            """,
            group.id,
            group.title,
            group.username,
            group.member_count,
            group.is_active,
            datetime.now(timezone.utc),
        )
        logger.info(
            f"Grupo upserted: {group.title}",
            extra={"group_id": group.id, "operation": "upsert_group"},
        )

    async def insert_message(self, msg: CollectedMessage) -> bool:
        """
        Insere mensagem com idempotência via UNIQUE(group_id, telegram_msg_id).
        Retorna True se inseriu, False se já existia (duplicata).
        """
        try:
            await self._pool.execute(
                """
                INSERT INTO raw_messages
                    (telegram_msg_id, group_id, author_id, author_name, text,
                     date, links, media_type, reply_to_msg_id, raw_json)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                """,
                msg.telegram_msg_id,
                msg.group_id,
                msg.author_id,
                msg.author_name,
                msg.text,
                msg.date,
                json.dumps(msg.links),
                msg.media_type,
                msg.reply_to_msg_id,
                json.dumps(msg.raw_json) if msg.raw_json else None,
            )
            return True
        except UniqueViolationError:
            logger.debug(
                "Mensagem duplicada ignorada",
                extra={
                    "group_id": msg.group_id,
                    "message_id": msg.telegram_msg_id,
                    "operation": "skip_duplicate",
                },
            )
            return False

    async def insert_messages_batch(self, messages: list[CollectedMessage]) -> int:
        """
        Insere lote de mensagens, ignorando duplicatas.
        Retorna quantidade de novas mensagens inseridas.
        """
        inserted = 0
        # Usa transação para performance, mas trata cada insert individualmente
        # para não perder o lote inteiro por causa de uma duplicata
        async with self._pool.acquire() as conn:
            for msg in messages:
                try:
                    await conn.execute(
                        """
                        INSERT INTO raw_messages
                            (telegram_msg_id, group_id, author_id, author_name, text,
                             date, links, media_type, reply_to_msg_id, raw_json)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                        ON CONFLICT (group_id, telegram_msg_id) DO NOTHING
                        """,
                        msg.telegram_msg_id,
                        msg.group_id,
                        msg.author_id,
                        msg.author_name,
                        msg.text,
                        msg.date,
                        json.dumps(msg.links),
                        msg.media_type,
                        msg.reply_to_msg_id,
                        json.dumps(msg.raw_json) if msg.raw_json else None,
                    )
                    inserted += 1
                except UniqueViolationError:
                    continue

        logger.info(
            f"Batch inserido: {inserted}/{len(messages)} novas mensagens",
            extra={"count": inserted, "operation": "batch_insert"},
        )
        return inserted

    async def get_collection_state(self, group_id: int) -> CollectionState | None:
        """Retorna o estado de coleta de um grupo."""
        row = await self._pool.fetchrow(
            "SELECT * FROM collection_state WHERE group_id = $1",
            group_id,
        )
        if not row:
            return None
        return CollectionState(
            group_id=row["group_id"],
            last_message_id=row["last_message_id"],
            last_collected=row["last_collected"],
            backfill_done=row["backfill_done"],
        )

    async def update_collection_state(self, state: CollectionState) -> None:
        """Atualiza o estado de coleta (cursor) de um grupo."""
        await self._pool.execute(
            """
            INSERT INTO collection_state (group_id, last_message_id, last_collected, backfill_done)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (group_id) DO UPDATE SET
                last_message_id = EXCLUDED.last_message_id,
                last_collected = EXCLUDED.last_collected,
                backfill_done = EXCLUDED.backfill_done
            """,
            state.group_id,
            state.last_message_id,
            state.last_collected,
            state.backfill_done,
        )

    async def count_messages(self, group_id: int | None = None) -> int:
        """Conta mensagens no banco, opcionalmente filtrado por grupo."""
        if group_id:
            row = await self._pool.fetchrow(
                "SELECT COUNT(*) as cnt FROM raw_messages WHERE group_id = $1",
                group_id,
            )
        else:
            row = await self._pool.fetchrow("SELECT COUNT(*) as cnt FROM raw_messages")
        return row["cnt"] if row else 0
