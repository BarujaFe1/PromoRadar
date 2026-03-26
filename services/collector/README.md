# Collector Service

Serviço de coleta de mensagens do Telegram para o PromoRadar.

## Responsabilidades

- Conectar via Telegram User API (Telethon)
- Backfill histórico de grupos monitorados
- Ingestão em tempo real via event handler
- Persistência idempotente no PostgreSQL
- Rate limiting e retry com backoff exponencial

## Arquitetura em Camadas

```
src/
├── main.py              # Orquestrador principal
├── core/
│   ├── config.py        # Variáveis de ambiente
│   └── logging.py       # Logs estruturados JSON
├── models/
│   └── message.py       # Dataclasses de domínio
├── db/
│   ├── connection.py    # Pool asyncpg
│   ├── repository.py    # Acesso a dados (idempotente)
│   └── migrations/      # SQL DDL
├── services/
│   ├── telegram_client.py  # Wrapper Telethon
│   ├── backfill.py         # Coleta histórica
│   └── realtime.py         # Event handler
└── utils/
    ├── retry.py          # Decorator de retry
    └── rate_limiter.py   # Token bucket
```

## Como rodar

```bash
# 1. Copie e configure o .env
cp ../../.env.example ../../.env

# 2. Suba o banco
docker compose -f ../../docker-compose.yml up -d postgres

# 3. Execute as migrations
psql -U promoradar -d promoradar -f src/db/migrations/001_initial_schema.sql

# 4. Na primeira execução, o Telethon pedirá código de verificação
python -m src.main
```

## Testes

```bash
pytest tests/ -v
```

## Idempotência

A constraint `UNIQUE(group_id, telegram_msg_id)` garante que a mesma mensagem nunca é inserida duas vezes, mesmo em caso de reprocessamento ou restart.

## Rate Limiting

- Token bucket: 20 req/s (conservador para Telegram User API)
- FloodWaitError: espera exatamente o tempo indicado + 1s de margem
- Retry: até 3 tentativas com backoff exponencial + jitter
