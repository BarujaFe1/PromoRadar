"""
PromoRadar Telegram — Collector Service

Ponto de entrada principal que orquestra:
1. Conexão com Telegram e PostgreSQL
2. Registro dos grupos monitorados
3. Backfill histórico (se necessário)
4. Escuta em tempo real de novas mensagens
"""

from __future__ import annotations

import asyncio
import signal
import sys

from src.core.config import app_config, telegram_config
from src.core.logging import get_logger
from src.db.connection import close_pool, get_pool
from src.db.repository import MessageRepository
from src.services.backfill import BackfillService
from src.services.realtime import RealtimeService
from src.services.telegram_client import TelegramCollector

logger = get_logger("collector.main")


async def main() -> None:
    """Fluxo principal do collector."""
    logger.info("=" * 60)
    logger.info("PromoRadar Telegram — Collector iniciando")
    logger.info("=" * 60)

    # 1. Inicializa componentes
    collector = TelegramCollector()
    await collector.connect()

    pool = await get_pool()
    repo = MessageRepository(pool)

    # 2. Lista e registra grupos
    groups = await collector.list_groups()
    monitored_ids = app_config.monitored_groups

    for group in groups:
        # Se há filtro de grupos, aplica
        if monitored_ids and group.id not in monitored_ids:
            continue
        await repo.upsert_group(group)

    # Determina quais grupos monitorar
    if monitored_ids:
        target_groups = [g for g in groups if g.id in monitored_ids]
    else:
        target_groups = groups

    group_ids = [g.id for g in target_groups]
    logger.info(
        f"Monitorando {len(group_ids)} grupo(s)",
        extra={"count": len(group_ids), "operation": "setup"},
    )

    # 3. Backfill histórico
    backfill = BackfillService(collector, repo)
    backfill_results = await backfill.backfill_all_groups(group_ids)
    for gid, count in backfill_results.items():
        status = f"{count} mensagens" if count >= 0 else "ERRO"
        logger.info(f"  Grupo {gid}: {status}")

    # 4. Inicia escuta em tempo real
    realtime = RealtimeService(collector, repo)

    # Graceful shutdown
    loop = asyncio.get_event_loop()
    shutdown_event = asyncio.Event()

    def _signal_handler() -> None:
        logger.info("Sinal de shutdown recebido")
        shutdown_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _signal_handler)

    # Roda realtime até receber sinal de parada
    realtime_task = asyncio.create_task(realtime.start(group_ids))

    logger.info("Collector rodando. Pressione Ctrl+C para parar.")
    await shutdown_event.wait()

    # Cleanup
    await realtime.stop()
    realtime_task.cancel()
    try:
        await realtime_task
    except asyncio.CancelledError:
        pass

    total = await repo.count_messages()
    logger.info(f"Total de mensagens no banco: {total}", extra={"count": total})

    await collector.disconnect()
    await close_pool()
    logger.info("Collector finalizado com sucesso")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception:
        logger.error("Erro fatal no collector", exc_info=True)
        sys.exit(1)
