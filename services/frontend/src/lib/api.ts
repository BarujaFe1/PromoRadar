// ============================================================
// API Client — Fetch wrapper com tipagem e tratamento de erros
// ============================================================

import type {
  Alert,
  DailyVolume,
  Offer,
  PaginatedResponse,
  PriceHistoryPoint,
  Product,
  ProductStats,
  SearchFilters,
  StoreStats,
  TelegramGroup,
  WishlistItem,
} from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    ...options,
  });

  if (!res.ok) {
    throw new ApiError(res.status, `API error: ${res.status} ${res.statusText}`);
  }

  return res.json();
}

function buildQuery(params: Record<string, unknown>): string {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, val]) => {
    if (val !== undefined && val !== null && val !== "") {
      search.set(key, String(val));
    }
  });
  const qs = search.toString();
  return qs ? `?${qs}` : "";
}

// ── Offers ──

export async function getOffers(
  filters: SearchFilters = {}
): Promise<PaginatedResponse<Offer>> {
  return request(`/api/offers${buildQuery(filters)}`);
}

export async function getOffer(id: number): Promise<Offer> {
  return request(`/api/offers/${id}`);
}

export async function getOfferRanking(
  period: "day" | "week" | "month" = "week",
  limit: number = 20
): Promise<Offer[]> {
  return request(`/api/offers/ranking?period=${period}&limit=${limit}`);
}

// ── Products ──

export async function searchProducts(q: string): Promise<Product[]> {
  return request(`/api/products/search?q=${encodeURIComponent(q)}`);
}

export async function getProduct(id: number): Promise<Product> {
  return request(`/api/products/${id}`);
}

export async function getProductHistory(id: number): Promise<PriceHistoryPoint[]> {
  return request(`/api/products/${id}/history`);
}

export async function getProductStats(id: number): Promise<ProductStats> {
  return request(`/api/products/${id}/stats`);
}

// ── Wishlist ──

export async function getWishlist(): Promise<WishlistItem[]> {
  return request("/api/wishlist");
}

export async function addToWishlist(
  product_query: string,
  target_price?: number
): Promise<WishlistItem> {
  return request("/api/wishlist", {
    method: "POST",
    body: JSON.stringify({ product_query, target_price }),
  });
}

export async function removeFromWishlist(id: number): Promise<void> {
  return request(`/api/wishlist/${id}`, { method: "DELETE" });
}

// ── Alerts ──

export async function getAlerts(): Promise<Alert[]> {
  return request("/api/alerts");
}

// ── Groups ──

export async function getGroups(): Promise<TelegramGroup[]> {
  return request("/api/groups");
}

export async function toggleGroup(
  id: number,
  is_active: boolean
): Promise<void> {
  return request(`/api/groups/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ is_active }),
  });
}

// ── Analytics ──

export async function getStoreStats(): Promise<StoreStats[]> {
  return request("/api/analytics/stores");
}

export async function getVolumeData(days: number = 30): Promise<DailyVolume[]> {
  return request(`/api/analytics/volume?days=${days}`);
}
