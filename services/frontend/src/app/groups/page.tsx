"use client";

import { AppLayout } from "@/components/layout/AppLayout";
import { Card, Badge, Button, EmptyState } from "@/components/ui";
import { Radio, Users, MessageSquare, TrendingUp, Pause, Play } from "lucide-react";

const MOCK_GROUPS = [
  {
    id: 1001, title: "Promoções Tech BR", username: "promos_tech_br",
    member_count: 45200, is_active: true, message_count: 12340, offer_count: 4521,
  },
  {
    id: 1002, title: "Achados da Amazon", username: "achados_amazon",
    member_count: 32100, is_active: true, message_count: 8920, offer_count: 3102,
  },
  {
    id: 1003, title: "Ofertas KaBuM e Pichau", username: "ofertas_kabum",
    member_count: 18700, is_active: true, message_count: 5640, offer_count: 2890,
  },
  {
    id: 1004, title: "Shopee Promos", username: null,
    member_count: 67800, is_active: false, message_count: 1200, offer_count: 340,
  },
];

export default function GroupsPage() {
  return (
    <AppLayout>
      <div className="mb-8">
        <h1 className="page-title">Grupos monitorados</h1>
        <p className="page-subtitle">
          Gerencie os grupos do Telegram que alimentam o PromoRadar
        </p>
      </div>

      {/* Summary */}
      <div className="mb-6 grid grid-cols-3 gap-4">
        <Card>
          <p className="text-sm text-surface-700/60">Grupos ativos</p>
          <p className="text-2xl font-bold text-surface-900">
            {MOCK_GROUPS.filter((g) => g.is_active).length}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-surface-700/60">Total mensagens</p>
          <p className="text-2xl font-bold text-surface-900">
            {MOCK_GROUPS.reduce((s, g) => s + g.message_count, 0).toLocaleString("pt-BR")}
          </p>
        </Card>
        <Card>
          <p className="text-sm text-surface-700/60">Total ofertas</p>
          <p className="text-2xl font-bold text-surface-900">
            {MOCK_GROUPS.reduce((s, g) => s + g.offer_count, 0).toLocaleString("pt-BR")}
          </p>
        </Card>
      </div>

      {/* Group list */}
      <div className="space-y-3">
        {MOCK_GROUPS.map((group) => (
          <Card key={group.id} className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${
                group.is_active ? "bg-brand-50 text-brand-600" : "bg-surface-100 text-surface-700/40"
              }`}>
                <Radio className="h-5 w-5" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="font-semibold text-surface-900">{group.title}</h3>
                  <Badge variant={group.is_active ? "success" : "default"}>
                    {group.is_active ? "Ativo" : "Pausado"}
                  </Badge>
                </div>
                <div className="mt-0.5 flex items-center gap-4 text-xs text-surface-700/50">
                  {group.username && <span>@{group.username}</span>}
                  <span className="flex items-center gap-1">
                    <Users className="h-3 w-3" />
                    {group.member_count?.toLocaleString("pt-BR")} membros
                  </span>
                  <span className="flex items-center gap-1">
                    <MessageSquare className="h-3 w-3" />
                    {group.message_count.toLocaleString("pt-BR")} msgs
                  </span>
                  <span className="flex items-center gap-1">
                    <TrendingUp className="h-3 w-3" />
                    {group.offer_count.toLocaleString("pt-BR")} ofertas
                  </span>
                </div>
              </div>
            </div>
            <Button
              variant={group.is_active ? "ghost" : "secondary"}
              size="sm"
            >
              {group.is_active ? (
                <><Pause className="h-3.5 w-3.5" /> Pausar</>
              ) : (
                <><Play className="h-3.5 w-3.5" /> Ativar</>
              )}
            </Button>
          </Card>
        ))}
      </div>
    </AppLayout>
  );
}
