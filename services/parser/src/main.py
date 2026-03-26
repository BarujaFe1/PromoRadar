"""
PromoRadar Telegram — Parser Service

Job que roda em loop:
1. Busca mensagens não parseadas no banco
2. Executa o pipeline de extração
3. Salva ofertas extraídas
4. Marca mensagens como parseadas
"""

from __future__ import annotations

import asyncio
import json
import os
import signal
import sys
import time

import asyncpg

from src.extractors.pipeline import OfferExtractionPipeline

# ── Config ──
DB_DSN = (
    f"postgresql://{os.getenv('DB_USER', 'promoradar')}:"
    f"{os.getenv('DB_PASSWORD', 'promoradar')}@"
    f"{os.getenv('DB_HOST', 'localhost')}:"
    f"{os.getenv('DB_PORT', '5432')}/"
    f"{os.getenv('DB_NAME', 'promoradar')}"
)
BATCH_SIZE = int(os.getenv("PARSER_BATCH_SIZE", "50"))
INTERVAL_SEC = int(os.getenv("PARSER_INTERVAL_SEC", "30"))
LLM_ENABLED = os.getenv("LLM_FALLBACK_ENABLED", "false").lower() == "true"


async def fetch_unparsed(pool: asyncpg.Pool, limit: int) -> list[dict]:
    """Busca mensagens brutas ainda não parseadas."""
    rows = await pool.fetch(
        """
        SELECT id, telegram_msg_id, group_id, text, links, date
        FROM raw_messages
        WHERE is_parsed = false AND text IS NOT NULL AND text != ''
        ORDER BY date DESC
        LIMIT $1
        """,
        limit,
    )
    messages = []
    for r in rows:
        links = []
        if r["links"]:
            try:
                links = json.loads(r["links"]) if isinstance(r["links"], str) else r["links"]
            except (json.JSONDecodeError, TypeError):
                pass
        messages.append({
            "id": r["id"],
            "telegram_msg_id": r["telegram_msg_id"],
            "group_id": r["group_id"],
            "text": r["text"],
            "links": links,
            "date": r["date"],
        })
    return messages


async def save_offer(pool: asyncpg.Pool, offer) -> int | None:
    """Persiste uma oferta extraída."""
    row = await pool.fetchrow(
        """
        INSERT INTO offers (
            raw_message_id, product_name_raw, brand, model,
            price_current, price_original, discount_pct,
            store, installments, installment_count, installment_value,
            pix_price, coupon, shipping, link, telegram_link,
            confidence, extraction_method, group_id, offer_date
        ) VALUES (
            $1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20
        ) RETURNING id
        """,
        offer.raw_message_id,
        offer.product_name,
        offer.brand,
        offer.model,
        offer.price_current,
        offer.price_original,
        offer.discount_pct,
        offer.store,
        offer.installments_raw,
        offer.installment_count,
        offer.installment_value,
        offer.pix_price,
        offer.coupon,
        offer.shipping,
        offer.link,
        offer.telegram_link,
        offer.confidence,
        offer.extraction_method,
        offer.group_id,
        offer.offer_date,
    )
    return row["id"] if row else None


async def mark_parsed(pool: asyncpg.Pool, message_ids: list[int]) -> None:
    """Marca mensagens como parseadas."""
    await pool.execute(
        "UPDATE raw_messages SET is_parsed = true WHERE id = ANY($1::bigint[])",
        message_ids,
    )


async def process_batch(pool: asyncpg.Pool, pipeline: OfferExtractionPipeline) -> int:
    """Processa um lote de mensagens. Retorna número de ofertas extraídas."""
    messages = await fetch_unparsed(pool, BATCH_SIZE)
    if not messages:
        return 0

    offers = pipeline.extract_batch(messages)

    saved = 0
    for offer in offers:
        try:
            offer_id = await save_offer(pool, offer)
            if offer_id:
                saved += 1
        except Exception as e:
            print(f"[ERROR] Falha ao salvar oferta: {e}")

    # Marca TODAS as mensagens do lote como parseadas (mesmo as que não geraram oferta)
    msg_ids = [m["id"] for m in messages]
    await mark_parsed(pool, msg_ids)

    print(
        f"[INFO] Lote processado: {len(messages)} mensagens → {saved} ofertas "
        f"(confiança média: {sum(o.confidence for o in offers) / len(offers):.2f})"
        if offers else f"[INFO] Lote processado: {len(messages)} mensagens → 0 ofertas"
    )
    return saved


async def main() -> None:
    """Loop principal do parser."""
    print("=" * 60)
    print("PromoRadar Telegram — Parser Service")
    print(f"Batch size: {BATCH_SIZE} | Intervalo: {INTERVAL_SEC}s | LLM: {LLM_ENABLED}")
    print("=" * 60)

    pool = await asyncpg.create_pool(DB_DSN, min_size=2, max_size=5)
    pipeline = OfferExtractionPipeline(llm_enabled=LLM_ENABLED)

    running = True

    def _stop(*_):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    total_offers = 0
    while running:
        try:
            count = await process_batch(pool, pipeline)
            total_offers += count
        except Exception as e:
            print(f"[ERROR] Erro no processamento: {e}")

        await asyncio.sleep(INTERVAL_SEC)

    await pool.close()
    print(f"Parser finalizado. Total de ofertas extraídas: {total_offers}")


if __name__ == "__main__":
    asyncio.run(main())
