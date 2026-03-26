# Frontend — PromoRadar Telegram

Interface web construída com Next.js 14 + TypeScript + Tailwind CSS.

## Telas

| Rota | Descrição |
|------|-----------|
| `/dashboard` | Cards de estatísticas, gráfico de volume, destaques do dia |
| `/search` | Full-text search com filtros combinados (loja, preço, parcelas, grupo) |
| `/product` | Detalhes do produto, histórico de preços com gráfico, estatísticas |
| `/ranking` | Top ofertas por desconto (dia / semana / mês) |
| `/wishlist` | CRUD de itens monitorados com preço-alvo |
| `/alerts` | Histórico de alertas disparados |
| `/groups` | Grupos monitorados com estatísticas e toggle ativo/pausado |

## Componentes reutilizáveis

```
src/components/
├── ui/          → Badge, Card, StatCard, Button, Skeleton, Loading, Empty/Error states
├── cards/       → OfferCard (compacto e expandido)
├── charts/      → PriceChart (Recharts LineChart com ReferenceLine)
├── filters/     → FilterBar (loja, preço, parcelas, grupo, ordenação)
└── layout/      → AppLayout (sidebar + main content area)
```

## Como rodar

```bash
npm install
npm run dev        # http://localhost:3000
```

## Stack

- **Next.js 14** (App Router)
- **TypeScript** (strict mode)
- **Tailwind CSS** (design system via CSS variables)
- **Recharts** (gráficos de preço e volume)
- **Lucide React** (ícones)

## Design

- Color system: brand green + neutral slate
- Inter (body) + JetBrains Mono (código/números)
- Loading, empty state e error state em todas as telas
- Sidebar fixa com navegação por ícones
- Cards com hover states e micro-interações
