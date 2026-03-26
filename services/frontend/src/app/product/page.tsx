"use client";

import { AppLayout } from "@/components/layout/AppLayout";
import { Card, StatCard, Badge, Button } from "@/components/ui";
import { PriceChart } from "@/components/charts/PriceChart";
import { OfferCard } from "@/components/cards/OfferCard";
import { formatBRL } from "@/lib/utils";
import { Heart, TrendingDown, BarChart3, Calendar, Store } from "lucide-react";

// Mock data para demonstração
const MOCK_PRODUCT = {
  id: 1,
  canonical_name: "iPhone 15 Pro Max 256GB",
  brand: "Apple",
  model: "iPhone 15 Pro Max",
  category: "Smartphones",
  aliases: ["Apple iPhone 15 Pro Max 256", "iPhone 15 PM 256GB"],
};

const MOCK_STATS = {
  min_price: 5699.0,
  max_price: 9499.0,
  avg_price: 7234.5,
  median_price: 6999.0,
  offer_count: 47,
  store_count: 6,
  first_seen: "2024-10-15",
  last_seen: new Date().toISOString(),
};

const MOCK_HISTORY = Array.from({ length: 30 }, (_, i) => ({
  date: new Date(Date.now() - (29 - i) * 86400000).toISOString(),
  price: 6500 + Math.random() * 2000 - Math.random() * 800,
  store: ["Amazon", "Magazine Luiza", "KaBuM!"][Math.floor(Math.random() * 3)],
  offer_id: i + 1,
}));

export default function ProductDetailPage() {
  return (
    <AppLayout>
      {/* Header */}
      <div className="mb-8 flex items-start justify-between">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="info">{MOCK_PRODUCT.brand}</Badge>
            <Badge>{MOCK_PRODUCT.category}</Badge>
          </div>
          <h1 className="page-title">{MOCK_PRODUCT.canonical_name}</h1>
          <p className="text-sm text-surface-700/50 mt-1">
            Aliases: {MOCK_PRODUCT.aliases.join(" · ")}
          </p>
        </div>
        <Button variant="secondary">
          <Heart className="h-4 w-4" />
          Adicionar à wishlist
        </Button>
      </div>

      {/* Stats */}
      <div className="mb-8 grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard
          label="Menor preço"
          value={formatBRL(MOCK_STATS.min_price)}
          icon={<TrendingDown className="h-5 w-5" />}
        />
        <StatCard
          label="Preço médio"
          value={formatBRL(MOCK_STATS.avg_price)}
          icon={<BarChart3 className="h-5 w-5" />}
        />
        <StatCard
          label="Total de ofertas"
          value={MOCK_STATS.offer_count}
          sublabel={`em ${MOCK_STATS.store_count} lojas`}
          icon={<Store className="h-5 w-5" />}
        />
        <StatCard
          label="Mediana"
          value={formatBRL(MOCK_STATS.median_price)}
          icon={<Calendar className="h-5 w-5" />}
        />
      </div>

      {/* Price history chart */}
      <Card className="mb-8">
        <h2 className="section-title mb-4">Histórico de preços</h2>
        <PriceChart
          data={MOCK_HISTORY}
          minPrice={MOCK_STATS.min_price}
          height={350}
        />
        <p className="mt-3 text-xs text-surface-700/40 text-center">
          O menor preço registrado foi {formatBRL(MOCK_STATS.min_price)} — 
          {" "}{Math.round((1 - MOCK_STATS.min_price / MOCK_STATS.max_price) * 100)}%
          abaixo do maior preço visto
        </p>
      </Card>

      {/* Recent offers for this product */}
      <div>
        <h2 className="section-title mb-4">Ofertas recentes</h2>
        <p className="text-sm text-surface-700/50 mb-4">
          Em produção, aqui seriam listadas as ofertas mais recentes deste produto,
          ordenadas por data, com link para o post original no Telegram.
        </p>
      </div>
    </AppLayout>
  );
}
