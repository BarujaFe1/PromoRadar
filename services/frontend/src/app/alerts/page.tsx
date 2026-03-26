"use client";

import { AppLayout } from "@/components/layout/AppLayout";
import { Card, Badge, EmptyState } from "@/components/ui";
import { formatBRL, formatRelative } from "@/lib/utils";
import { Bell, CheckCircle2, ExternalLink } from "lucide-react";

const MOCK_ALERTS = [
  {
    id: 1, wishlist_id: 1, offer_id: 42, notified_at: new Date(Date.now() - 3600000).toISOString(),
    channel: "telegram",
    product: "iPhone 15 Pro Max", price: 5399, target: 5500, store: "Amazon",
  },
  {
    id: 2, wishlist_id: 3, offer_id: 87, notified_at: new Date(Date.now() - 86400000).toISOString(),
    channel: "telegram",
    product: "Air Fryer Mondial 5L", price: 169.9, target: 180, store: "Shopee",
  },
];

export default function AlertsPage() {
  return (
    <AppLayout>
      <div className="mb-8">
        <h1 className="page-title">Alertas</h1>
        <p className="page-subtitle">
          Histórico de alertas disparados quando produtos da wishlist atingiram o preço alvo
        </p>
      </div>

      {MOCK_ALERTS.length === 0 ? (
        <EmptyState
          title="Nenhum alerta disparado"
          description="Quando um produto da sua wishlist atingir o preço alvo, o alerta aparecerá aqui."
          icon={<Bell className="h-12 w-12" />}
        />
      ) : (
        <div className="space-y-3">
          {MOCK_ALERTS.map((alert) => (
            <Card key={alert.id} className="flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-green-50 text-green-600">
                  <CheckCircle2 className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="font-semibold text-surface-900">
                    {alert.product}
                  </h3>
                  <p className="text-sm text-surface-700/60">
                    {formatBRL(alert.price)} na {alert.store} — abaixo do alvo de {formatBRL(alert.target)}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <Badge variant="success">
                  <Bell className="mr-1 h-3 w-3" />
                  {alert.channel}
                </Badge>
                <span className="text-xs text-surface-700/50">
                  {formatRelative(alert.notified_at)}
                </span>
              </div>
            </Card>
          ))}
        </div>
      )}
    </AppLayout>
  );
}
