"use client";

import { useState } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { Card, Button, Badge, EmptyState } from "@/components/ui";
import { formatBRL, formatDate } from "@/lib/utils";
import { Heart, Plus, Trash2, Bell } from "lucide-react";

const MOCK_WISHLIST = [
  {
    id: 1, user_id: "user1", product_query: "iPhone 15 Pro Max",
    product_id: 1, target_price: 5500, is_active: true,
    created_at: "2024-12-01T00:00:00Z",
  },
  {
    id: 2, user_id: "user1", product_query: "RTX 4070 Super",
    product_id: null, target_price: 3000, is_active: true,
    created_at: "2025-01-15T00:00:00Z",
  },
  {
    id: 3, user_id: "user1", product_query: "Air Fryer Mondial 5L",
    product_id: 3, target_price: 180, is_active: true,
    created_at: "2025-02-20T00:00:00Z",
  },
];

export default function WishlistPage() {
  const [showAdd, setShowAdd] = useState(false);
  const [newQuery, setNewQuery] = useState("");
  const [newPrice, setNewPrice] = useState("");

  return (
    <AppLayout>
      <div className="mb-8 flex items-start justify-between">
        <div>
          <h1 className="page-title">Wishlist</h1>
          <p className="page-subtitle">
            Monitore produtos e receba alertas quando o preço atingir seu alvo
          </p>
        </div>
        <Button onClick={() => setShowAdd(!showAdd)}>
          <Plus className="h-4 w-4" />
          Adicionar
        </Button>
      </div>

      {/* Add form */}
      {showAdd && (
        <Card className="mb-6">
          <div className="flex gap-4">
            <div className="flex-1">
              <label className="mb-1 block text-xs font-medium text-surface-700/60">
                Produto
              </label>
              <input
                type="text"
                value={newQuery}
                onChange={(e) => setNewQuery(e.target.value)}
                placeholder="Ex: iPhone 15 Pro Max, RTX 4070..."
                className="w-full rounded-lg border border-surface-200 px-3 py-2 text-sm focus:border-brand-400 focus:outline-none"
              />
            </div>
            <div className="w-40">
              <label className="mb-1 block text-xs font-medium text-surface-700/60">
                Preço alvo (R$)
              </label>
              <input
                type="number"
                value={newPrice}
                onChange={(e) => setNewPrice(e.target.value)}
                placeholder="5.000"
                className="w-full rounded-lg border border-surface-200 px-3 py-2 text-sm focus:border-brand-400 focus:outline-none"
              />
            </div>
            <div className="flex items-end">
              <Button
                onClick={() => {
                  setShowAdd(false);
                  setNewQuery("");
                  setNewPrice("");
                }}
              >
                Salvar
              </Button>
            </div>
          </div>
        </Card>
      )}

      {/* List */}
      {MOCK_WISHLIST.length === 0 ? (
        <EmptyState
          title="Sua wishlist está vazia"
          description="Adicione produtos para monitorar e receba alertas quando o preço cair."
          icon={<Heart className="h-12 w-12" />}
        />
      ) : (
        <div className="space-y-3">
          {MOCK_WISHLIST.map((item) => (
            <Card key={item.id} className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-surface-900">
                  {item.product_query}
                </h3>
                <div className="mt-1 flex items-center gap-3 text-sm text-surface-700/60">
                  <span>
                    Preço alvo: <strong className="text-brand-700">{formatBRL(item.target_price)}</strong>
                  </span>
                  <span>·</span>
                  <span>Desde {formatDate(item.created_at)}</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Badge variant={item.is_active ? "success" : "default"}>
                  <Bell className="mr-1 h-3 w-3" />
                  {item.is_active ? "Ativo" : "Pausado"}
                </Badge>
                <button className="rounded-lg p-2 text-surface-700/40 hover:bg-red-50 hover:text-red-500 transition">
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </AppLayout>
  );
}
