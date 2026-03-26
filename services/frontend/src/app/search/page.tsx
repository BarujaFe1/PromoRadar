"use client";

import { useState, useCallback } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { OfferCard } from "@/components/cards/OfferCard";
import { FilterBar } from "@/components/filters/FilterBar";
import { EmptyState, LoadingSpinner } from "@/components/ui";
import { useDebounce } from "@/hooks";
import { Search as SearchIcon, Sparkles } from "lucide-react";
import type { SearchFilters } from "@/types";

const KNOWN_STORES = [
  "Amazon", "Magazine Luiza", "KaBuM!", "Shopee", "Mercado Livre",
  "Americanas", "Pichau", "AliExpress", "Carrefour", "Terabyte Shop",
];

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<SearchFilters>({
    page: 1,
    per_page: 20,
    sort_by: "date",
    sort_order: "desc",
  });

  const debouncedQuery = useDebounce(query, 300);

  // Em produção: const { data, loading, error } = useAsync(
  //   () => getOffers({ ...filters, q: debouncedQuery }),
  //   [debouncedQuery, filters]
  // );

  const hasSearched = debouncedQuery.length > 0;

  return (
    <AppLayout>
      {/* Header */}
      <div className="mb-8">
        <h1 className="page-title">Buscar ofertas</h1>
        <p className="page-subtitle">
          Pesquise por produto, marca ou modelo entre todas as ofertas coletadas
        </p>
      </div>

      {/* Search input */}
      <div className="relative mb-4">
        <SearchIcon className="absolute left-4 top-1/2 h-5 w-5 -translate-y-1/2 text-surface-700/40" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ex: iPhone 15 Pro Max, Notebook Lenovo, Air Fryer..."
          className="w-full rounded-xl border border-surface-200 bg-white py-3.5 pl-12 pr-4 text-base shadow-sm transition-colors placeholder:text-surface-700/30 focus:border-brand-400 focus:outline-none focus:ring-2 focus:ring-brand-100"
          autoFocus
        />
      </div>

      {/* Filters */}
      <div className="mb-6">
        <FilterBar
          filters={filters}
          onFilterChange={setFilters}
          stores={KNOWN_STORES}
        />
      </div>

      {/* Results */}
      {!hasSearched ? (
        <EmptyState
          title="Busque por um produto"
          description="Digite o nome de um produto para encontrar ofertas passadas e atuais com menor preço histórico, loja e condições."
          icon={<Sparkles className="h-12 w-12" />}
        />
      ) : (
        <div className="space-y-3">
          <p className="text-sm text-surface-700/60">
            Mostrando resultados para &ldquo;{debouncedQuery}&rdquo;
          </p>
          {/* Em produção, mapeia data.data aqui */}
          <EmptyState
            title="Nenhuma oferta encontrada"
            description={`Não encontramos ofertas para "${debouncedQuery}". Tente termos mais genéricos ou ajuste os filtros.`}
          />
        </div>
      )}
    </AppLayout>
  );
}
