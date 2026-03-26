"use client";

import { AppLayout } from "@/components/layout/AppLayout";
import {
  StatCard,
  Card,
  LoadingSpinner,
  ErrorState,
  EmptyState,
  Badge,
} from "@/components/ui";
import { OfferCard } from "@/components/cards/OfferCard";
import {
  BarChart3,
  Package,
  TrendingDown,
  Zap,
  Radio,
  ArrowRight,
} from "lucide-react";
import Link from "next/link";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

// ── Mock data (substituir por useAsync + API calls em produção) ──

const MOCK_STATS = {
  total_offers: 12847,
  offers_today: 342,
  avg_discount: 28.5,
  groups_active: 12,
};

const MOCK_TOP_OFFERS = [
  {
    id: 1,
    product_name_raw: "iPhone 15 Pro Max 256GB Titânio Natural",
    brand: "Apple",
    model: "iPhone 15 Pro Max",
    price_current: 5999.0,
    price_original: 9499.0,
    discount_pct: 36.8,
    store: "Magazine Luiza",
    installments: "12x R$ 599,92",
    installment_count: 12,
    installment_value: 599.92,
    pix_price: 5699.0,
    coupon: "TECH10",
    shipping: "Grátis",
    link: "https://magazineluiza.com.br/...",
    telegram_link: "https://t.me/c/123/456",
    confidence: 0.95,
    extraction_method: "regex",
    group_id: 100,
    offer_date: new Date().toISOString(),
    created_at: new Date().toISOString(),
    product_id: 1,
  },
  {
    id: 2,
    product_name_raw: "Notebook Lenovo IdeaPad 3 Ryzen 5 8GB 256GB SSD",
    brand: "Lenovo",
    model: "IdeaPad 3",
    price_current: 2499.0,
    price_original: 3299.0,
    discount_pct: 24.2,
    store: "Amazon",
    installments: "10x R$ 249,90",
    installment_count: 10,
    installment_value: 249.9,
    pix_price: null,
    coupon: null,
    shipping: "Grátis",
    link: "https://amzn.to/...",
    telegram_link: "https://t.me/c/123/457",
    confidence: 0.88,
    extraction_method: "regex",
    group_id: 100,
    offer_date: new Date(Date.now() - 3600000).toISOString(),
    created_at: new Date(Date.now() - 3600000).toISOString(),
    product_id: 2,
  },
  {
    id: 3,
    product_name_raw: "Air Fryer Mondial Family 5L Inox",
    brand: "Mondial",
    model: null,
    price_current: 199.9,
    price_original: 349.9,
    discount_pct: 42.9,
    store: "Shopee",
    installments: null,
    installment_count: null,
    installment_value: null,
    pix_price: 189.9,
    coupon: "AIRFRY20",
    shipping: "Grátis",
    link: "https://shope.ee/...",
    telegram_link: "https://t.me/c/123/458",
    confidence: 0.82,
    extraction_method: "regex",
    group_id: 101,
    offer_date: new Date(Date.now() - 7200000).toISOString(),
    created_at: new Date(Date.now() - 7200000).toISOString(),
    product_id: 3,
  },
];

const MOCK_VOLUME = Array.from({ length: 14 }, (_, i) => ({
  date: new Date(Date.now() - (13 - i) * 86400000)
    .toLocaleDateString("pt-BR", { day: "2-digit", month: "2-digit" }),
  offers: Math.floor(Math.random() * 200 + 200),
  messages: Math.floor(Math.random() * 500 + 400),
}));

// ── Page ──

export default function DashboardPage() {
  return (
    <AppLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="page-title">Dashboard</h1>
        <p className="page-subtitle">
          Visão geral das ofertas coletadas dos seus grupos de promoção
        </p>
      </div>

      {/* Stats grid */}
      <div className="mb-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Total de ofertas"
          value={MOCK_STATS.total_offers.toLocaleString("pt-BR")}
          sublabel="indexadas no banco"
          icon={<Package className="h-5 w-5" />}
        />
        <StatCard
          label="Ofertas hoje"
          value={MOCK_STATS.offers_today}
          icon={<Zap className="h-5 w-5" />}
          trend={{ value: 12, label: "vs ontem" }}
        />
        <StatCard
          label="Desconto médio"
          value={`${MOCK_STATS.avg_discount}%`}
          sublabel="nas últimas 24h"
          icon={<TrendingDown className="h-5 w-5" />}
        />
        <StatCard
          label="Grupos ativos"
          value={MOCK_STATS.groups_active}
          sublabel="monitorando em tempo real"
          icon={<Radio className="h-5 w-5" />}
        />
      </div>

      {/* Volume chart + Top offers */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Volume chart */}
        <Card className="lg:col-span-2">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="section-title">Volume de ofertas</h2>
            <Badge>Últimos 14 dias</Badge>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={MOCK_VOLUME}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 11, fill: "#64748b" }}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#64748b" }}
                tickLine={false}
                axisLine={false}
                width={40}
              />
              <Tooltip
                contentStyle={{
                  borderRadius: "8px",
                  border: "1px solid #e2e8f0",
                  fontSize: "13px",
                }}
              />
              <Bar
                dataKey="offers"
                fill="#22c55e"
                radius={[4, 4, 0, 0]}
                name="Ofertas"
              />
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Top offers today */}
        <div>
          <div className="mb-4 flex items-center justify-between">
            <h2 className="section-title">Destaques</h2>
            <Link
              href="/ranking"
              className="flex items-center gap-1 text-xs font-medium text-brand-600 hover:text-brand-700"
            >
              Ver ranking <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="space-y-3">
            {MOCK_TOP_OFFERS.map((offer) => (
              <OfferCard key={offer.id} offer={offer} compact />
            ))}
          </div>
        </div>
      </div>
    </AppLayout>
  );
}
