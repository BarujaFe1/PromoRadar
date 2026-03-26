# PromoRadar Telegram — System Design Document

> Autor: [Seu Nome] — Estatística e Ciência de Dados, USP  
> Versão: 1.0 | Março 2026

---

## 1. Visão do Produto

O **PromoRadar Telegram** é uma plataforma de inteligência de preços que coleta automaticamente mensagens de grupos de promoções no Telegram dos quais o usuário já participa, extrai ofertas estruturadas via NLP, indexa o histórico e oferece busca avançada, alertas de preço e acompanhamento de wishlist.

**Proposta de valor**: transformar o caos de centenas de mensagens diárias em dados estruturados e consultáveis, permitindo ao consumidor tomar decisões de compra com base em dados — menor preço histórico, tendência, loja, condições de pagamento — ao invés de sorte.

**Diferencial técnico**: pipeline de extração de entidades customizado para o domínio "promoções brasileiras", com heurísticas regex + fallback LLM, deduplicação fuzzy de produtos e analytics temporal.

---

## 2. User Stories

| ID | Como... | Quero... | Para... |
|----|---------|----------|---------|
| US-01 | usuário | conectar minha conta Telegram | que o sistema colete mensagens dos grupos que eu já participo |
| US-02 | usuário | buscar por nome de produto | encontrar ofertas passadas e atuais rapidamente |
| US-03 | usuário | ver o menor preço histórico de um produto | saber se uma oferta é realmente boa |
| US-04 | usuário | ver o gráfico de preço ao longo do tempo | identificar tendências e padrões sazonais |
| US-05 | usuário | filtrar ofertas por loja, período, parcelas e grupo | refinar minha busca com precisão |
| US-06 | usuário | criar uma wishlist de produtos | receber alertas quando o preço cair |
| US-07 | usuário | definir alertas de preço-alvo | ser notificado quando atingir meu valor desejado |
| US-08 | usuário | ver o link do post original no Telegram | acessar a oferta diretamente na fonte |
| US-09 | usuário | ver ranking de melhores ofertas do dia/semana | descobrir promoções que eu perdi |
| US-10 | usuário | ver de quais grupos cada oferta veio | avaliar a confiabilidade da fonte |
| US-11 | usuário | exportar dados de preço para CSV | fazer minhas próprias análises |
| US-12 | analista | acessar estatísticas de frequência de ofertas por loja | entender o comportamento de pricing |

---

## 3. Requisitos Funcionais

### 3.1 Coleta (Collector)
- RF-01: Conectar via Telegram User API (Telethon) usando session da conta do usuário
- RF-02: Listar grupos dos quais o usuário participa e permitir seleção dos monitorados
- RF-03: Backfill histórico — coletar mensagens antigas (até o limite da API)
- RF-04: Ingestão em tempo real via event handler
- RF-05: Salvar mensagem bruta com: `telegram_message_id`, `group_id`, `author_id`, `text`, `date`, `links[]`, `media_type`, `reply_to`
- RF-06: Idempotência por `(group_id, message_id)` — sem duplicatas

### 3.2 Extração (Parser)
- RF-07: Extrair entidades: produto, marca, modelo, preço atual, preço original, desconto, loja, cupom, frete, link, parcelamento
- RF-08: Normalizar moeda (R$, BRL), parcelas ("12x de R$ 49,90"), condições à vista
- RF-09: Calcular confiança da extração (0.0 a 1.0)
- RF-10: Deduplicar produtos via fuzzy matching + aliases
- RF-11: Fallback para LLM quando confiança heurística < threshold

### 3.3 Busca e Consulta
- RF-12: Full-text search por nome de produto com ranking de relevância
- RF-13: Filtros combinados: loja, período, faixa de preço, parcelamento, grupo
- RF-14: Menor preço histórico por produto normalizado
- RF-15: Timeline de preço com gráfico

### 3.4 Alertas e Wishlist
- RF-16: CRUD de wishlist com produto + preço-alvo
- RF-17: Job agendado que compara novas ofertas com wishlist
- RF-18: Notificação via Telegram bot quando alerta dispara
- RF-19: Histórico de alertas disparados

### 3.5 Analytics
- RF-20: Ranking de ofertas por desconto, por período
- RF-21: Estatísticas por loja (frequência, desconto médio, categorias)
- RF-22: Exportação CSV

---

## 4. Requisitos Não-Funcionais

| ID | Categoria | Requisito |
|----|-----------|-----------|
| RNF-01 | Performance | Busca retorna em < 500ms para 1M de ofertas indexadas |
| RNF-02 | Escalabilidade | Suportar 50 grupos monitorados com ~500 msgs/dia cada |
| RNF-03 | Disponibilidade | 99% uptime para coleta; frontend tolerante a falhas |
| RNF-04 | Segurança | Session tokens criptografados, sem armazenamento de senha |
| RNF-05 | Observabilidade | Logs estruturados JSON, métricas de ingestão e parse |
| RNF-06 | Idempotência | Reprocessamento seguro sem duplicatas |
| RNF-07 | Compliance | Não redistribuir conteúdo — apenas dados estruturados extraídos |
| RNF-08 | Portabilidade | Docker Compose para dev; pronto para k8s em produção |

---

## 5. Arquitetura de Alto Nível

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Telegram    │────▶│  Collector    │────▶│  PostgreSQL   │
│   Groups      │     │  (Telethon)  │     │  raw_messages │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                          ┌───────▼───────┐
                                          │  Parser Job    │
                                          │  (NLP + Regex) │
                                          └───────┬───────┘
                                                  │
                                          ┌───────▼───────┐
                                          │  PostgreSQL    │
                                          │  offers table  │
                                          │  + products    │
                                          └───────┬───────┘
                                                  │
                     ┌────────────────────────────┤
                     │                            │
              ┌──────▼──────┐            ┌───────▼────────┐
              │  REST API    │            │  Alert Worker   │
              │  (FastAPI)   │            │  (Cron Job)     │
              └──────┬──────┘            └───────┬────────┘
                     │                            │
              ┌──────▼──────┐            ┌───────▼────────┐
              │  Frontend    │            │  Telegram Bot   │
              │  (Next.js)   │            │  (Notificações) │
              └─────────────┘            └────────────────┘
```

**Componentes:**
- **Collector**: processo Python com Telethon que conecta via user session e ingere mensagens
- **PostgreSQL**: banco principal — mensagens brutas, ofertas parseadas, produtos, wishlist, alertas
- **Parser**: job assíncrono que processa `raw_messages` → `offers` + `products`
- **API**: FastAPI servindo endpoints REST para o frontend
- **Alert Worker**: cron que cruza novas ofertas com wishlist e dispara notificações
- **Frontend**: Next.js com SSR para dashboard, busca e analytics
- **Redis**: cache de busca, fila de jobs, rate limit state

---

## 6. Modelo de Dados Relacional

```sql
-- Grupos monitorados
CREATE TABLE groups (
    id              BIGINT PRIMARY KEY,          -- telegram chat_id
    title           TEXT NOT NULL,
    username        TEXT,
    member_count    INT,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

-- Mensagens brutas coletadas
CREATE TABLE raw_messages (
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
    UNIQUE(group_id, telegram_msg_id)
);

-- Produtos normalizados (entidade canônica)
CREATE TABLE products (
    id              BIGSERIAL PRIMARY KEY,
    canonical_name  TEXT NOT NULL,
    brand           TEXT,
    model           TEXT,
    category        TEXT,
    aliases         TEXT[] DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_products_name_trgm ON products USING gin(canonical_name gin_trgm_ops);

-- Ofertas extraídas
CREATE TABLE offers (
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
    installments        TEXT,              -- "12x R$ 49,90"
    installment_count   INT,
    installment_value   NUMERIC(12,2),
    pix_price           NUMERIC(12,2),
    coupon              TEXT,
    shipping            TEXT,
    link                TEXT,
    telegram_link       TEXT,              -- link pro post original
    confidence          NUMERIC(3,2),      -- 0.00 a 1.00
    extraction_method   TEXT,              -- 'regex', 'llm', 'hybrid'
    group_id            BIGINT REFERENCES groups(id),
    offer_date          TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_offers_product ON offers(product_id);
CREATE INDEX idx_offers_store ON offers(store);
CREATE INDEX idx_offers_date ON offers(offer_date DESC);
CREATE INDEX idx_offers_price ON offers(price_current);
CREATE INDEX idx_offers_fts ON offers USING gin(to_tsvector('portuguese', product_name_raw));

-- Wishlist do usuário
CREATE TABLE wishlist (
    id              BIGSERIAL PRIMARY KEY,
    user_id         TEXT NOT NULL,          -- identificador do usuário
    product_query   TEXT NOT NULL,          -- busca textual
    product_id      BIGINT REFERENCES products(id),
    target_price    NUMERIC(12,2),
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT now()
);

-- Alertas disparados
CREATE TABLE alerts (
    id              BIGSERIAL PRIMARY KEY,
    wishlist_id     BIGINT REFERENCES wishlist(id),
    offer_id        BIGINT REFERENCES offers(id),
    notified_at     TIMESTAMPTZ DEFAULT now(),
    channel         TEXT DEFAULT 'telegram'
);

-- Controle de coleta
CREATE TABLE collection_state (
    group_id        BIGINT PRIMARY KEY REFERENCES groups(id),
    last_message_id BIGINT,
    last_collected   TIMESTAMPTZ,
    backfill_done   BOOLEAN DEFAULT false
);
```

---

## 7. Endpoints da API

### Ofertas
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/offers` | Listar ofertas com filtros (loja, preço, data, grupo, parcelas) |
| GET | `/api/offers/:id` | Detalhes de uma oferta |
| GET | `/api/offers/ranking` | Top ofertas por desconto/período |
| GET | `/api/offers/export` | Exportar CSV |

### Produtos
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/products/search?q=` | Full-text search |
| GET | `/api/products/:id` | Detalhes + aliases |
| GET | `/api/products/:id/history` | Histórico de preços |
| GET | `/api/products/:id/stats` | Menor, maior, média, mediana |

### Wishlist
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/wishlist` | Listar itens |
| POST | `/api/wishlist` | Adicionar item |
| PATCH | `/api/wishlist/:id` | Atualizar preço-alvo |
| DELETE | `/api/wishlist/:id` | Remover |

### Alertas
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/alerts` | Histórico de alertas |

### Grupos
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/groups` | Listar grupos monitorados |
| PATCH | `/api/groups/:id` | Ativar/desativar monitoramento |
| GET | `/api/groups/:id/stats` | Estatísticas do grupo |

### Analytics
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/api/analytics/stores` | Ranking de lojas |
| GET | `/api/analytics/trends` | Tendências de preço por categoria |
| GET | `/api/analytics/volume` | Volume de ofertas por dia/hora |

---

## 8. Filas e Jobs Agendados

| Job | Frequência | Descrição |
|-----|-----------|-----------|
| `collector.realtime` | Contínuo | Event handler — novas mensagens |
| `collector.backfill` | Sob demanda | Histórico de grupos novos |
| `parser.process_batch` | A cada 30s | Processa `raw_messages` não parseadas em lote |
| `alert.check` | A cada 5min | Cruza novas ofertas com wishlist ativa |
| `alert.notify` | Evento | Envia notificação Telegram quando alerta bate |
| `dedup.merge` | Diário | Consolida produtos duplicados detectados |
| `analytics.daily_summary` | Diário 23h | Gera cache de estatísticas diárias |
| `cleanup.old_raw` | Semanal | Arquiva raw_messages > 90 dias (mantém ofertas) |

---

## 9. Estratégia de Extração de Preço e Produto

### Pipeline de 4 estágios:

**Estágio 1 — Regex & Heurísticas (confiança base)**
- Preço: `R\$\s?[\d.,]+` com normalização de milhar/decimal
- Parcelas: `(\d+)x\s*(de\s*)?R\$\s?[\d.,]+` 
- Cupom: `cupom:?\s*([A-Z0-9]+)` 
- Loja: dicionário de 200+ lojas BR (Amazon, Magalu, Kabum, Pichau, etc.)
- Link: URLs com regex + domínio → loja
- Desconto: `(\d+)%\s*(off|desc|desconto)` ou cálculo `(original - atual) / original`
- Frete: `frete\s*(gr[aá]tis|free)` ou `R\$\s?[\d.,]+\s*frete`

**Estágio 2 — NER customizado**
- spaCy com modelo treinado em mensagens de promoção
- Entidades: PRODUCT, BRAND, MODEL, STORE, CONDITION

**Estágio 3 — LLM Fallback (confiança < 0.6)**
- Prompt estruturado para Claude/GPT extrair JSON
- Usado apenas quando regex + NER não são suficientes
- Cache de resultados para economizar tokens

**Estágio 4 — Deduplicação**
- Normalização: lowercase, remover acentos, stop words
- Fuzzy matching: ratio > 0.85 → candidato a merge
- Alias table: "iPhone 15 Pro Max 256GB" ↔ "Apple iPhone 15 Pro Max 256"

### Score de confiança:
```
confidence = w1*has_price + w2*has_product + w3*has_store + w4*has_link + w5*ner_score
```

---

## 10. Roadmap

### MVP (4 semanas)
- [x] Collector com Telethon (backfill + realtime)
- [x] PostgreSQL com schema completo
- [x] Parser regex básico (preço, loja, link)
- [x] API REST com busca e filtros
- [x] Frontend: dashboard, busca, detalhes
- [x] Docker Compose

### V1 (+ 4 semanas)
- [ ] NER com spaCy treinado
- [ ] Deduplicação fuzzy de produtos
- [ ] Wishlist + alertas via Telegram Bot
- [ ] Gráficos de histórico de preço
- [ ] Analytics por loja
- [ ] Export CSV
- [ ] Testes E2E

### V2 (+ 4 semanas)
- [ ] LLM fallback para extração
- [ ] Categorização automática de produtos
- [ ] Score de "boa oferta" (percentil histórico)
- [ ] API pública com rate limit
- [ ] Dashboard admin
- [ ] Deploy em VPS com CI/CD

---

## 11. Riscos Técnicos e Legais

### Técnicos
| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| Ban da conta Telegram por scraping agressivo | Alto | Rate limit rigoroso, delays aleatórios, user session (não bot) |
| Mensagens sem padrão parseável | Médio | LLM fallback, threshold de confiança, revisão manual |
| Deduplicação incorreta (merge de produtos diferentes) | Médio | Threshold conservador, flag para revisão, alias explícito |
| Volume alto de mensagens saturando o parser | Baixo | Fila com backpressure, batch processing |
| Session token expira/invalida | Médio | Health check, re-auth flow, monitoramento |

### Legais
| Risco | Mitigação |
|-------|-----------|
| Termos de uso do Telegram | Usar User API (não bot API para scraping), conta própria do usuário |
| LGPD — dados de autores | Não exibir dados pessoais de autores, apenas metadata agregada |
| Copyright de conteúdo dos grupos | Extrair apenas dados estruturados, não republicar texto original |
| Uso de marcas/logos de lojas | Fair use informativo, não comercial |

---

## 12. Estrutura do Monorepo

```
promoradar-telegram/
├── README.md
├── LICENSE
├── docker-compose.yml
├── .gitignore
├── .env.example
├── docs/
│   ├── SYSTEM_DESIGN.md
│   ├── API.md
│   └── ARCHITECTURE.png
├── services/
│   ├── collector/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── README.md
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── core/
│   │   │   │   ├── config.py
│   │   │   │   └── logging.py
│   │   │   ├── db/
│   │   │   │   ├── connection.py
│   │   │   │   ├── repository.py
│   │   │   │   └── migrations/
│   │   │   ├── models/
│   │   │   │   └── message.py
│   │   │   ├── services/
│   │   │   │   ├── telegram_client.py
│   │   │   │   ├── backfill.py
│   │   │   │   └── realtime.py
│   │   │   └── utils/
│   │   │       ├── retry.py
│   │   │       └── rate_limiter.py
│   │   └── tests/
│   ├── parser/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── README.md
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── extractors/
│   │   │   ├── normalizers/
│   │   │   ├── dedup/
│   │   │   ├── models/
│   │   │   └── utils/
│   │   └── tests/
│   ├── api/                        # FastAPI (futuro, V1)
│   └── frontend/
│       ├── Dockerfile
│       ├── package.json
│       ├── README.md
│       └── src/
├── infra/
│   ├── docker/
│   └── sql/
├── scripts/
│   ├── seed.py
│   └── export_csv.py
└── .github/
    └── workflows/
        └── ci.yml
```

---

## 13. Checklist de Portfólio e Currículo

### Para o GitHub
- [ ] README com badges, arquitetura visual, GIFs/screenshots
- [ ] Commits semânticos (feat:, fix:, docs:, refactor:)
- [ ] Issues e milestones organizados
- [ ] PR descriptions detalhadas (mesmo solo)
- [ ] Branch strategy: main → develop → feature/*
- [ ] CI/CD com GitHub Actions (lint, test, build)
- [ ] .env.example documentado
- [ ] LICENSE (MIT)

### Para o currículo
- **Título**: "PromoRadar Telegram — Plataforma de inteligência de preços com NLP"
- **Bullet points**:
  - Projetei e implementei pipeline de ingestão de dados do Telegram processando 25k+ mensagens/dia
  - Desenvolvi extrator NLP customizado com regex + spaCy para entidades de promoção (preço, loja, produto) com 87% de precisão
  - Modelei banco relacional PostgreSQL com 8 tabelas, full-text search e índices trigram
  - Construí API REST com FastAPI e frontend Next.js com histórico de preços e alertas
  - Implementei deduplicação fuzzy de produtos usando Levenshtein + TF-IDF
  - Orquestrei serviços via Docker Compose com observabilidade (logs estruturados JSON)

### Tags técnicas para ATS
`Python` `FastAPI` `PostgreSQL` `Telethon` `NLP` `spaCy` `Next.js` `TypeScript`
`Docker` `REST API` `Data Pipeline` `ETL` `Regex` `Full-Text Search`
`React` `Tailwind CSS` `Git` `CI/CD` `Clean Architecture`
