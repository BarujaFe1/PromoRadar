"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { Card, Badge, Button } from "@/components/ui";
import { OfferCard } from "@/components/cards/OfferCard";
import { Trophy, Flame, Clock, TrendingDown } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Offer } from "@/types";

type Period = "day" | "week" | "month";

const PERIODS: { key: Period; label: string; icon: typeof Clock }[] = [
  { key: "day", label: "Hoje", icon: Flame },
  { key: "week", label: "Semana", icon: Clock },
  { key: "month", label: "Mês", icon: TrendingDown },
];

// Mock
const MOCK_RANKING: Offer[] = [
  {
    id: 10, product_name_raw: "Headset HyperX Cloud III Wireless", brand: "HyperX", model: "Cloud III",
    price_current: 499.9, price_original: 999.9, discount_pct: 50.0, store: "KaBuM!",
    installments: "10x R$ 49,99", installment_count: 10, installment_value: 49.99,
    pix_price: 474.9, coupon: null, shipping: "Grátis",
    link: "#", telegram_link: "#", confidence: 0.92, extraction_method: "regex",
    group_id: 100, offer_date: new Date().toISOString(), created_at: new Date().toISOString(), product_id: 10,
  },
  {
    id: 11, product_name_raw: "SSD Kingston NV2 1TB NVMe M.2", brand: "Kingston", model: "NV2 1TB",
    price_current: 289.9, price_original: 549.9, discount_pct: 47.3, store: "Amazon",
    installments: null, installment_count: null, installment_value: null,
    pix_price: 275.0, coupon: "STORAGE20", shipping: "Grátis",
    link: "#", telegram_link: "#", confidence: 0.89, extraction_method: "regex",
    group_id: 100, offer_date: new Date(Date.now() - 3600000).toISOString(),
    created_at: new Date(Date.now() - 3600000).toISOString(), product_id: 11,
  },
  {
    id: 12, product_name_raw: "Monitor LG UltraGear 27\" 165Hz IPS", brand: "LG", model: "UltraGear 27",
    price_current: 1099.0, price_original: 1999.0, discount_pct: 45.0, store: "Pichau",
    installments: "12x R$ 91,58", installment_count: 12, installment_value: 91.58,
    pix_price: null, coupon: null, shipping: "R$ 29,90",
    link: "#", telegram_link: "#", confidence: 0.85, extraction_method: "regex",
    group_id: 101, offer_date: new Date(Date.now() - 7200000).toISOString(),
    created_at: new Date(Date.now() - 7200000).toISOString(), product_id: 12,
  },
  {
    id: 13, product_name_raw: "Teclado Mecânico Redragon Kumara K552 RGB", brand: "Redragon", model: "Kumara K552",
    price_current: 139.9, price_original: 249.9, discount_pct: 44.0, store: "Amazon",
    installments: null, installment_count: null, installment_value: null,
    pix_price: 132.9, coupon: null, shipping: "Grátis",
    link: "#", telegram_link: "#", confidence: 0.91, extraction_method: "regex",
    group_id: 100, offer_date: new Date(Date.now() - 10800000).toISOString(),
    created_at: new Date(Date.now() - 10800000).toISOString(), product_id: 13,
  },
];

export default function RankingPage() {
  const [period, setPeriod] = useState<Period>("week");

  return (
    <AppLayout>
      <div className="mb-8">
        <h1 className="page-title flex items-center gap-3">
          <Trophy className="h-7 w-7 text-amber-500" />
          Ranking de ofertas
        </h1>
        <p className="page-subtitle">
          Melhores ofertas classificadas por percentual de desconto
        </p>
      </div>

      {/* Period selector */}
      <div className="mb-6 flex gap-2">
        {PERIODS.map((p) => {
          const Icon = p.icon;
          return (
            <button
              key={p.key}
              onClick={() => setPeriod(p.key)}
              className={cn(
                "flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition",
                period === p.key
                  ? "bg-brand-600 text-white shadow-sm"
                  : "bg-white text-surface-700 border border-surface-200 hover:bg-surface-50"
              )}
            >
              <Icon className="h-4 w-4" />
              {p.label}
            </button>
          );
        })}
      </div>

      {/* Ranking list */}
      <div className="space-y-4">
        {MOCK_RANKING.map((offer, index) => (
          <div key={offer.id} className="flex items-start gap-4">
            {/* Position badge */}
            <div className={cn(
              "flex h-10 w-10 shrink-0 items-center justify-center rounded-xl text-base font-bold",
              index === 0 ? "bg-amber-100 text-amber-700" :
              index === 1 ? "bg-gray-100 text-gray-600" :
              index === 2 ? "bg-orange-100 text-orange-700" :
              "bg-surface-100 text-surface-700/50"
            )}>
              {index + 1}
            </div>
            <div className="flex-1">
              <OfferCard offer={offer} />
            </div>
          </div>
        ))}
      </div>
    </AppLayout>
  );
}
