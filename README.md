<h1 align="center">
  <br>
  📡 PromoRadar Telegram
  <br>
</h1>

<p align="center">
  <strong>Plataforma de inteligência de preços que transforma mensagens caóticas de grupos de promoção do Telegram em dados estruturados e consultáveis.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11-blue?logo=python&logoColor=white" alt="Python 3.11" />
  <img src="https://img.shields.io/badge/Next.js-14-black?logo=next.js" alt="Next.js 14" />
  <img src="https://img.shields.io/badge/PostgreSQL-16-336791?logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white" alt="Docker" />
  <img src="https://img.shields.io/badge/TypeScript-strict-3178C6?logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT License" />
</p>

---

## O Problema

Grupos brasileiros de promoção no Telegram recebem **centenas de mensagens por dia** com ofertas de dezenas de lojas. Essas mensagens são:

- **Desestruturadas**: cada admin formata diferente (emojis, abreviações, links encurtados)
- **Efêmeras**: rolam no chat e se perdem em minutos
- **Impossíveis de comparar**: não há como saber se R$ 5.999 no iPhone é bom ou não sem contexto histórico
- **Dispersas**: o consumidor participa de 5–15 grupos e perde ofertas relevantes

O resultado? Decisões de compra baseadas em **sorte**, não em **dados**.

## A Solução

O **PromoRadar Telegram** coleta automaticamente mensagens dos grupos que o usuário já participa, extrai ofertas estruturadas via pipeline NLP, indexa o histórico e oferece:

- 🔍 **Busca full-text** por produto com filtros combinados
- 📉 **Menor preço histórico** com gráfico de tendência temporal
- 🏪 **Detecção de loja** por URL e texto (40+ lojas brasileiras)
- 💳 **Parcelamento, PIX e cupom** extraídos automaticamente
- 🎯 **Wishlist + alertas** — monitore produtos e receba notificação no Telegram
- 🏆 **Ranking de ofertas** por desconto (dia/semana/mês)
- 📊 **Analytics por loja** — frequência, desconto médio, categorias

---

## Arquitetura

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Telegram    │────▶│  Collector    │────▶│  PostgreSQL   │
│   Groups      │     │  (Telethon)  │     │  raw_messages │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                          ┌───────▼───────┐
                                          │  Parser Job    │
                                          │  Regex + NLP   │
                                          └───────┬───────┘
                                                  │
                     ┌────────────────────────────┤
                     │                            │
              ┌──────▼──────┐            ┌───────▼────────┐
              │  REST API    │            │  Alert Worker   │
              │  (FastAPI)   │            │  (Cron)         │
              └──────┬──────┘            └───────┬────────┘
                     │                            │
              ┌──────▼──────┐            ┌───────▼────────┐
              │  Frontend    │            │  Telegram Bot   │
              │  (Next.js)   │            │  Notificações   │
              └─────────────┘            └────────────────┘
```

**Fluxo de dados:**
1. **Collector** conecta via Telegram User API (Telethon) e ingere mensagens em tempo real + backfill histórico
2. Mensagens brutas são salvas no **PostgreSQL** com idempotência (`UNIQUE(group_id, msg_id)`)
3. **Parser** processa em lotes: regex para preço/loja/cupom, heurísticas para produto, score de confiança
4. Ofertas estruturadas alimentam a **API REST** (FastAPI) e o **Alert Worker**
5. **Frontend** (Next.js) consome a API com busca, filtros, gráficos e wishlist

---

## Stack Técnica

| Camada | Tecnologia | Justificativa |
|--------|-----------|---------------|
| Coleta | Python 3.11 + Telethon | User API nativa, async, rate limiting embutido |
| Banco | PostgreSQL 16 | Full-text search nativo, pg_trgm para fuzzy, JSONB |
| Parser | Regex + SequenceMatcher | Zero dependência de ML para MVP, LLM fallback para V2 |
| API | FastAPI | Async, auto-docs OpenAPI, tipagem Pydantic |
| Frontend | Next.js 14 + TypeScript | SSR, App Router, performance, tipagem estrita |
| UI | Tailwind CSS + Recharts | Design system consistente, gráficos interativos |
| Infra | Docker Compose | Ambiente reproduzível, 1 comando para subir tudo |
| CI | GitHub Actions | Testes + lint + build em cada PR |

---

## Features

### Collector Service
- ✅ Conexão via Telegram User API (conta própria do usuário)
- ✅ Backfill histórico completo de grupos
- ✅ Ingestão em tempo real via event handler
- ✅ Idempotência por `(group_id, message_id)`
- ✅ Rate limiting com token bucket (20 req/s)
- ✅ Retry com exponential backoff + jitter
- ✅ Tratamento de FloodWaitError do Telegram
- ✅ Logs estruturados em JSON

### Parser NLP
- ✅ Extração de preço (`R$ X.XXX,XX`), preço original, PIX, parcelamento
- ✅ Detecção de loja por URL (40+ domínios) e por texto
- ✅ Extração de cupom, frete, desconto percentual
- ✅ Identificação de produto, marca e modelo (dicionário de 50+ marcas)
- ✅ Score de confiança ponderado (0.0–1.0)
- ✅ Deduplicação fuzzy via SequenceMatcher (threshold 0.82)
- ✅ Normalização de texto para busca (remoção de acentos, stop words)
- 🔮 LLM fallback para confiança < 0.6 (V2)

### Frontend
- ✅ Dashboard com stats, gráfico de volume, destaques
- ✅ Busca com filtros (loja, preço, parcelas, grupo, ordenação)
- ✅ Página de produto com gráfico de histórico de preços
- ✅ Ranking de ofertas por desconto
- ✅ Wishlist com preço-alvo
- ✅ Histórico de alertas
- ✅ Gestão de grupos monitorados
- ✅ Loading, empty states e error states em todas as telas
- ✅ Componentes reutilizáveis com design system

---

## Capturas Sugeridas

> As seguintes capturas devem ser adicionadas ao README após implementação completa:

| # | Tela | Descrição |
|---|------|-----------|
| 1 | Dashboard | Cards de estatísticas + gráfico de barras de volume |
| 2 | Busca | Input de busca + FilterBar expandido + resultados |
| 3 | Produto | Gráfico de histórico de preços com menor preço marcado |
| 4 | Ranking | Top 5 ofertas com badges de posição e desconto |
| 5 | Wishlist | Lista com preço-alvo e status de alerta |
| 6 | Terminal | Logs estruturados JSON do collector rodando |

---

## Desafios Técnicos

### 1. Extração de entidades de texto não-estruturado
Mensagens de promoção não seguem padrão. A mesma informação aparece como:
- `R$ 5.999,00`, `R$5999`, `5999 reais`, `por 5.999`
- `12x R$ 499,92`, `12x de 499,92`, `12x s/ juros`
- Emojis misturados com dados (`🔥 PREÇÃO 🔥 iPhone 15 Pro Max`)

**Solução**: pipeline de 4 estágios (normalização → regex → heurísticas → score) com possibilidade de LLM fallback.

### 2. Deduplicação de produtos
"iPhone 15 Pro Max 256GB Titânio" e "Apple iPhone 15 PM 256 GB" são o mesmo produto.

**Solução**: normalização agressiva + SequenceMatcher com threshold 0.82 + fingerprint por tokens ordenados.

### 3. Rate limiting da API do Telegram
O Telegram bane contas que fazem requests demais.

**Solução**: token bucket limiter (20 req/s), tratamento explícito de FloodWaitError, delays aleatórios entre batches de backfill.

### 4. Idempotência em ambiente distribuído
O collector pode reiniciar a qualquer momento sem perder ou duplicar dados.

**Solução**: `UNIQUE(group_id, telegram_msg_id)` + `ON CONFLICT DO NOTHING` + cursor de coleta persistido.

---

## Roadmap

### MVP ✅
- [x] Collector (backfill + realtime)
- [x] Schema PostgreSQL completo
- [x] Parser regex (preço, loja, produto, cupom)
- [x] Frontend (dashboard, busca, produto, ranking, wishlist, alertas, grupos)
- [x] Docker Compose
- [x] CI com GitHub Actions
- [x] Testes unitários

### V1 🚧
- [ ] API REST com FastAPI
- [ ] NER com spaCy treinado em promoções BR
- [ ] Deduplicação ativa no banco (merge de produtos)
- [ ] Alertas via Telegram Bot
- [ ] Export CSV
- [ ] Testes E2E

### V2 🔮
- [ ] LLM fallback (Claude API) para extração de baixa confiança
- [ ] Categorização automática de produtos
- [ ] Score de "boa oferta" (percentil vs histórico)
- [ ] API pública documentada
- [ ] Deploy em VPS com CI/CD automático
- [ ] Dashboard admin com métricas de ingestão

---

## Aprendizados

| Área | O que aprendi |
|------|-------------|
| **Data Engineering** | Pipelines de ingestão com idempotência, backpressure e cursor-based pagination |
| **NLP aplicado** | Extração de entidades em domínio específico (promoções BR) sem ML supervisionado |
| **Backend** | Arquitetura em camadas, repository pattern, structured logging, retry patterns |
| **Frontend** | Design system com Tailwind, composição de componentes, estados de UI (loading/empty/error) |
| **DevOps** | Docker multi-stage, Compose com healthchecks, CI com GitHub Actions |
| **Product** | System design completo — do user story ao modelo de dados, passando por API design |

---

## Como rodar localmente

### Pré-requisitos
- Docker e Docker Compose
- Python 3.11+ (para rodar testes localmente)
- Node.js 20+ (para desenvolvimento do frontend)
- Conta no Telegram com API credentials ([my.telegram.org](https://my.telegram.org/apps))

### Setup

```bash
# 1. Clone o repo
git clone https://github.com/seu-usuario/promoradar-telegram.git
cd promoradar-telegram

# 2. Configure variáveis de ambiente
cp .env.example .env
# Edite .env com suas credenciais do Telegram

# 3. Suba tudo com Docker Compose
docker compose up -d postgres redis

# 4. Execute as migrations
docker compose exec postgres psql -U promoradar -d promoradar \
  -f /docker-entrypoint-initdb.d/001_initial_schema.sql

# 5. Rode o collector (primeira vez pedirá código do Telegram)
docker compose run --rm collector

# 6. Rode o parser
docker compose up -d parser

# 7. Rode o frontend
cd services/frontend
npm install
npm run dev  # http://localhost:3000
```

### Rodando testes

```bash
# Collector
cd services/collector && pytest tests/ -v

# Parser
cd services/parser && pytest tests/ -v

# Frontend
cd services/frontend && npm run lint
```

---

## Estrutura do Projeto

```
promoradar-telegram/
├── README.md                          # ← Você está aqui
├── LICENSE
├── docker-compose.yml                 # Orquestração de todos os serviços
├── .env.example                       # Template de variáveis de ambiente
├── .gitignore
│
├── docs/
│   └── SYSTEM_DESIGN.md               # Spec completa (13 seções)
│
├── services/
│   ├── collector/                      # 🔌 Ingestão de dados do Telegram
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   ├── README.md
│   │   ├── src/
│   │   │   ├── main.py                # Orquestrador
│   │   │   ├── core/config.py         # Env vars
│   │   │   ├── core/logging.py        # Logs JSON
│   │   │   ├── models/message.py      # Dataclasses
│   │   │   ├── db/connection.py       # Pool asyncpg
│   │   │   ├── db/repository.py       # CRUD idempotente
│   │   │   ├── db/migrations/         # DDL SQL
│   │   │   ├── services/telegram_client.py
│   │   │   ├── services/backfill.py
│   │   │   ├── services/realtime.py
│   │   │   └── utils/retry.py, rate_limiter.py
│   │   └── tests/
│   │
│   ├── parser/                         # 🧠 NLP — extração de ofertas
│   │   ├── Dockerfile
│   │   ├── README.md
│   │   ├── src/
│   │   │   ├── main.py                # Batch processor
│   │   │   ├── extractors/
│   │   │   │   ├── pipeline.py        # Orquestrador de 4 estágios
│   │   │   │   ├── price_extractor.py
│   │   │   │   ├── product_extractor.py
│   │   │   │   ├── store_extractor.py
│   │   │   │   └── coupon_extractor.py
│   │   │   ├── normalizers/text_normalizer.py
│   │   │   ├── dedup/matcher.py       # Fuzzy matching
│   │   │   └── models/offer.py
│   │   └── tests/                      # 50+ testes com msgs simuladas
│   │
│   └── frontend/                       # 🖥️ Interface web
│       ├── Dockerfile
│       ├── package.json
│       ├── README.md
│       └── src/
│           ├── app/                    # Next.js App Router (7 páginas)
│           ├── components/             # UI, cards, charts, filters, layout
│           ├── hooks/                  # useAsync, useDebounce
│           ├── lib/                    # API client, formatters
│           ├── types/                  # TypeScript interfaces
│           └── styles/
│
├── infra/                              # Configs de deploy
├── scripts/                            # Seed, export, utils
└── .github/workflows/ci.yml           # CI: test + lint + build
```

---

## Por que esse projeto demonstra capacidade técnica

Este projeto foi projetado para demonstrar competências que empresas de tecnologia buscam em engenheiros de dados, backend e full-stack:

| Competência | Como é demonstrada |
|-------------|-------------------|
| **System Design** | Documento de design com 13 seções: desde user stories até modelo de dados, API, filas e riscos |
| **Data Engineering** | Pipeline de ingestão com idempotência, backfill histórico, cursor-based pagination, batch processing |
| **NLP / Information Extraction** | Extração de entidades em texto não-estruturado com regex + heurísticas + score de confiança |
| **Backend Architecture** | Camadas limpas (core → models → db → services → utils), repository pattern, dependency injection |
| **Database Design** | Schema relacional normalizado, full-text search, índices trigram, JSONB |
| **API Design** | REST com filtros combinados, paginação, sorting, versionamento |
| **Frontend Engineering** | Next.js com TypeScript strict, design system, componentes reutilizáveis, estados de UI |
| **DevOps** | Docker multi-stage, Compose com healthchecks, CI/CD, logs estruturados |
| **Observabilidade** | Logs JSON com campos semânticos (operation, duration_ms, count) |
| **Resiliência** | Retry com backoff exponencial + jitter, rate limiting, graceful shutdown |
| **Qualidade** | Testes unitários, testes com dados simulados reais, type hints |
| **Documentação** | READMEs em cada serviço, SYSTEM_DESIGN.md, .env.example documentado |
| **Git profissional** | Commits semânticos, CI, branch strategy, .gitignore robusto |

---

## Licença

MIT — veja [LICENSE](LICENSE) para detalhes.

---

<p align="center">
  Desenvolvido como projeto de portfólio por um estudante de Estatística e Ciência de Dados da USP.<br>
  <strong>Feedback e contribuições são bem-vindos.</strong>
</p>
