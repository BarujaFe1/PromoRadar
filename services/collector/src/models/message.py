"""Modelos de domínio para mensagens coletadas."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class CollectedMessage:
    """Representa uma mensagem coletada de um grupo do Telegram."""

    telegram_msg_id: int
    group_id: int
    text: str | None
    date: datetime
    author_id: int | None = None
    author_name: str | None = None
    links: list[str] = field(default_factory=list)
    media_type: str | None = None
    reply_to_msg_id: int | None = None
    raw_json: dict[str, Any] | None = None

    @property
    def has_text(self) -> bool:
        return bool(self.text and self.text.strip())

    @property
    def idempotency_key(self) -> tuple[int, int]:
        """Chave única para evitar duplicatas: (group_id, message_id)."""
        return (self.group_id, self.telegram_msg_id)


@dataclass
class TelegramGroup:
    """Representa um grupo do Telegram monitorado."""

    id: int
    title: str
    username: str | None = None
    member_count: int | None = None
    is_active: bool = True


@dataclass
class CollectionState:
    """Estado de coleta de um grupo — controle de cursor."""

    group_id: int
    last_message_id: int | None = None
    last_collected: datetime | None = None
    backfill_done: bool = False
