"""Configuração centralizada via variáveis de ambiente."""

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class TelegramConfig:
    api_id: int = int(os.getenv("TELEGRAM_API_ID", "0"))
    api_hash: str = os.getenv("TELEGRAM_API_HASH", "")
    session_name: str = os.getenv("TELEGRAM_SESSION_NAME", "promoradar")
    phone: str = os.getenv("TELEGRAM_PHONE", "")
    # Rate limit: máx mensagens por request no backfill
    backfill_batch_size: int = int(os.getenv("BACKFILL_BATCH_SIZE", "100"))
    backfill_delay_sec: float = float(os.getenv("BACKFILL_DELAY_SEC", "2.0"))
    # Delay entre iterações de coleta em tempo real
    realtime_poll_sec: float = float(os.getenv("REALTIME_POLL_SEC", "1.0"))


@dataclass(frozen=True)
class DatabaseConfig:
    host: str = os.getenv("DB_HOST", "localhost")
    port: int = int(os.getenv("DB_PORT", "5432"))
    name: str = os.getenv("DB_NAME", "promoradar")
    user: str = os.getenv("DB_USER", "promoradar")
    password: str = os.getenv("DB_PASSWORD", "promoradar")

    @property
    def dsn(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"

    @property
    def async_dsn(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


@dataclass(frozen=True)
class AppConfig:
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    environment: str = os.getenv("ENVIRONMENT", "development")
    # Grupos para monitorar (IDs separados por vírgula, vazio = todos)
    monitored_groups: list[int] = field(default_factory=lambda: [
        int(g) for g in os.getenv("MONITORED_GROUPS", "").split(",") if g.strip()
    ])


# Singletons
telegram_config = TelegramConfig()
db_config = DatabaseConfig()
app_config = AppConfig()
