"use client";

import { useState } from "react";
import type { SearchFilters } from "@/types";
import { Button } from "@/components/ui";
import { SlidersHorizontal, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface FilterBarProps {
  filters: SearchFilters;
  onFilterChange: (filters: SearchFilters) => void;
  stores?: string[];
  groups?: { id: number; title: string }[];
}

export function FilterBar({
  filters,
  onFilterChange,
  stores = [],
  groups = [],
}: FilterBarProps) {
  const [expanded, setExpanded] = useState(false);

  const update = (patch: Partial<SearchFilters>) => {
    onFilterChange({ ...filters, ...patch, page: 1 });
  };

  const clearAll = () => {
    onFilterChange({ page: 1, per_page: filters.per_page });
  };

  const hasFilters =
    filters.store ||
    filters.min_price ||
    filters.max_price ||
    filters.date_from ||
    filters.group_id ||
    filters.installment_max;

  return (
    <div className="rounded-xl border border-surface-200 bg-white">
      {/* Toggle row */}
      <div className="flex items-center justify-between px-4 py-3">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-2 text-sm font-medium text-surface-700 hover:text-surface-900 transition"
        >
          <SlidersHorizontal className="h-4 w-4" />
          Filtros
          {hasFilters && (
            <span className="ml-1 rounded-full bg-brand-100 px-2 py-0.5 text-xs font-semibold text-brand-700">
              ativos
            </span>
          )}
        </button>
        <div className="flex items-center gap-2">
          {hasFilters && (
            <button
              onClick={clearAll}
              className="flex items-center gap-1 text-xs text-red-500 hover:text-red-600"
            >
              <X className="h-3 w-3" /> Limpar
            </button>
          )}
          {/* Sort */}
          <select
            value={`${filters.sort_by || "date"}-${filters.sort_order || "desc"}`}
            onChange={(e) => {
              const [sort_by, sort_order] = e.target.value.split("-") as [
                SearchFilters["sort_by"],
                SearchFilters["sort_order"]
              ];
              update({ sort_by, sort_order });
            }}
            className="rounded-lg border border-surface-200 bg-white px-3 py-1.5 text-xs text-surface-700 focus:border-brand-400 focus:outline-none"
          >
            <option value="date-desc">Mais recentes</option>
            <option value="date-asc">Mais antigos</option>
            <option value="price-asc">Menor preço</option>
            <option value="price-desc">Maior preço</option>
            <option value="discount-desc">Maior desconto</option>
          </select>
        </div>
      </div>

      {/* Expanded filters */}
      {expanded && (
        <div className="border-t border-surface-100 px-4 py-4">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
            {/* Store */}
            <div>
              <label className="mb-1 block text-xs font-medium text-surface-700/60">
                Loja
              </label>
              <select
                value={filters.store || ""}
                onChange={(e) => update({ store: e.target.value || undefined })}
                className="w-full rounded-lg border border-surface-200 bg-white px-3 py-2 text-sm focus:border-brand-400 focus:outline-none"
              >
                <option value="">Todas</option>
                {stores.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>

            {/* Min price */}
            <div>
              <label className="mb-1 block text-xs font-medium text-surface-700/60">
                Preço mín.
              </label>
              <input
                type="number"
                placeholder="R$ 0"
                value={filters.min_price || ""}
                onChange={(e) =>
                  update({
                    min_price: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
                className="w-full rounded-lg border border-surface-200 px-3 py-2 text-sm focus:border-brand-400 focus:outline-none"
              />
            </div>

            {/* Max price */}
            <div>
              <label className="mb-1 block text-xs font-medium text-surface-700/60">
                Preço máx.
              </label>
              <input
                type="number"
                placeholder="R$ ∞"
                value={filters.max_price || ""}
                onChange={(e) =>
                  update({
                    max_price: e.target.value ? Number(e.target.value) : undefined,
                  })
                }
                className="w-full rounded-lg border border-surface-200 px-3 py-2 text-sm focus:border-brand-400 focus:outline-none"
              />
            </div>

            {/* Group */}
            {groups.length > 0 && (
              <div>
                <label className="mb-1 block text-xs font-medium text-surface-700/60">
                  Grupo
                </label>
                <select
                  value={filters.group_id || ""}
                  onChange={(e) =>
                    update({
                      group_id: e.target.value ? Number(e.target.value) : undefined,
                    })
                  }
                  className="w-full rounded-lg border border-surface-200 bg-white px-3 py-2 text-sm focus:border-brand-400 focus:outline-none"
                >
                  <option value="">Todos</option>
                  {groups.map((g) => (
                    <option key={g.id} value={g.id}>
                      {g.title}
                    </option>
                  ))}
                </select>
              </div>
            )}

            {/* Max installments */}
            <div>
              <label className="mb-1 block text-xs font-medium text-surface-700/60">
                Máx. parcelas
              </label>
              <select
                value={filters.installment_max || ""}
                onChange={(e) =>
                  update({
                    installment_max: e.target.value
                      ? Number(e.target.value)
                      : undefined,
                  })
                }
                className="w-full rounded-lg border border-surface-200 bg-white px-3 py-2 text-sm focus:border-brand-400 focus:outline-none"
              >
                <option value="">Qualquer</option>
                <option value="1">À vista</option>
                <option value="3">Até 3x</option>
                <option value="6">Até 6x</option>
                <option value="10">Até 10x</option>
                <option value="12">Até 12x</option>
              </select>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
