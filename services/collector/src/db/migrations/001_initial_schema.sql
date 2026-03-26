-- Migration: 001_initial_schema.sql
-- PromoRadar Telegram — Schema inicial
-- Executar: psql -U promoradar -d promoradar -f 001_initial_schema.sql

BEGIN;

-- Extensões necessárias
CREATE EXTENSION IF NOT EXISTS pg_trgm;  -- para busca fuzzy/trigram

-- ============================================================
-- GRUPOS MONITORADOS
-- ============================================================
CREATE TABLE IF NOT EXISTS groups (
    id              BIGINT PRIMARY KEY,          -- telegram chat_id
    title           TEXT NOT NULL,
    username        TEXT,
    member_count    INT,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- MENSAGENS BRUTAS COLETADAS
-- ============================================================
CREATE TABLE IF NOT EXISTS raw_messages (
    id              BIGSERIAL PRIMARY KEY,
    telegram_msg_id BIGINT NOT NULL,
    group_id        BIGINT NOT NULL REFERENCES groups(id),
    author_id       BIGINT,
    author_name     TEXT,
    text            TEXT,
    date            TIMESTAMPTZ NOT NULL,
    links           JSONB DEFAULT '[]',
    media_type      TEXT,
    reply_to_msg_id BIGINT,
    raw_json        JSONB,
    is_parsed       BOOLEAN DEFAULT false,
    created_at      TIMESTAMPTZ DEFAULT now(),

    -- Chave de idempotência: mesmo grupo + mesmo ID de mensagem = duplicata
    UNIQUE(group_id, telegram_msg_id)
);

CREATE INDEX IF NOT EXISTS idx_raw_messages_group
    ON raw_messages(group_id);
CREATE INDEX IF NOT EXISTS idx_raw_messages_date
    ON raw_messages(date DESC);
CREATE INDEX IF NOT EXISTS idx_raw_messages_unparsed
    ON raw_messages(is_parsed) WHERE is_parsed = false;

-- ============================================================
-- PRODUTOS NORMALIZADOS (entidade canônica)
-- ============================================================
CREATE TABLE IF NOT EXISTS products (
    id              BIGSERIAL PRIMARY KEY,
    canonical_name  TEXT NOT NULL,
    brand           TEXT,
    model           TEXT,
    category        TEXT,
    aliases         TEXT[] DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_products_name_trgm
    ON products USING gin(canonical_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_products_brand
    ON products(brand);

-- ============================================================
-- OFERTAS EXTRAÍDAS
-- ============================================================
CREATE TABLE IF NOT EXISTS offers (
    id                  BIGSERIAL PRIMARY KEY,
    raw_message_id      BIGINT REFERENCES raw_messages(id),
    product_id          BIGINT REFERENCES products(id),
    product_name_raw    TEXT NOT NULL,
    brand               TEXT,
    model               TEXT,
    price_current       NUMERIC(12,2),
    price_original      NUMERIC(12,2),
    discount_pct        NUMERIC(5,2),
    store               TEXT,
    installments        TEXT,
    installment_count   INT,
    installment_value   NUMERIC(12,2),
    pix_price           NUMERIC(12,2),
    coupon              TEXT,
    shipping            TEXT,
    link                TEXT,
    telegram_link       TEXT,
    confidence          NUMERIC(3,2),
    extraction_method   TEXT,
    group_id            BIGINT REFERENCES groups(id),
    offer_date          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_offers_product    ON offers(product_id);
CREATE INDEX IF NOT EXISTS idx_offers_store      ON offers(store);
CREATE INDEX IF NOT EXISTS idx_offers_date       ON offers(offer_date DESC);
CREATE INDEX IF NOT EXISTS idx_offers_price      ON offers(price_current);
CREATE INDEX IF NOT EXISTS idx_offers_confidence ON offers(confidence);
CREATE INDEX IF NOT EXISTS idx_offers_fts
    ON offers USING gin(to_tsvector('portuguese', product_name_raw));

-- ============================================================
-- WISHLIST
-- ============================================================
CREATE TABLE IF NOT EXISTS wishlist (
    id              BIGSERIAL PRIMARY KEY,
    user_id         TEXT NOT NULL,
    product_query   TEXT NOT NULL,
    product_id      BIGINT REFERENCES products(id),
    target_price    NUMERIC(12,2),
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_wishlist_user
    ON wishlist(user_id) WHERE is_active = true;

-- ============================================================
-- ALERTAS DISPARADOS
-- ============================================================
CREATE TABLE IF NOT EXISTS alerts (
    id              BIGSERIAL PRIMARY KEY,
    wishlist_id     BIGINT REFERENCES wishlist(id),
    offer_id        BIGINT REFERENCES offers(id),
    notified_at     TIMESTAMPTZ DEFAULT now(),
    channel         TEXT DEFAULT 'telegram'
);

-- ============================================================
-- ESTADO DE COLETA (cursor por grupo)
-- ============================================================
CREATE TABLE IF NOT EXISTS collection_state (
    group_id        BIGINT PRIMARY KEY REFERENCES groups(id),
    last_message_id BIGINT,
    last_collected  TIMESTAMPTZ,
    backfill_done   BOOLEAN DEFAULT false
);

COMMIT;
