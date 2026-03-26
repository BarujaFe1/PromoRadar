// ============================================================
// PromoRadar Telegram — Domain Types
// ============================================================

export interface Offer {
  id: number;
  product_name_raw: string;
  brand: string | null;
  model: string | null;
  price_current: number | null;
  price_original: number | null;
  discount_pct: number | null;
  store: string | null;
  installments: string | null;
  installment_count: number | null;
  installment_value: number | null;
  pix_price: number | null;
  coupon: string | null;
  shipping: string | null;
  link: string | null;
  telegram_link: string | null;
  confidence: number;
  extraction_method: string;
  group_id: number;
  offer_date: string;
  created_at: string;
  product_id: number | null;
}

export interface Product {
  id: number;
  canonical_name: string;
  brand: string | null;
  model: string | null;
  category: string | null;
  aliases: string[];
  created_at: string;
}

export interface PriceHistoryPoint {
  date: string;
  price: number;
  store: string | null;
  offer_id: number;
}

export interface ProductStats {
  min_price: number;
  max_price: number;
  avg_price: number;
  median_price: number;
  offer_count: number;
  store_count: number;
  first_seen: string;
  last_seen: string;
}

export interface WishlistItem {
  id: number;
  user_id: string;
  product_query: string;
  product_id: number | null;
  target_price: number | null;
  is_active: boolean;
  created_at: string;
}

export interface Alert {
  id: number;
  wishlist_id: number;
  offer_id: number;
  notified_at: string;
  channel: string;
  offer?: Offer;
}

export interface TelegramGroup {
  id: number;
  title: string;
  username: string | null;
  member_count: number | null;
  is_active: boolean;
  message_count?: number;
  offer_count?: number;
}

export interface StoreStats {
  store: string;
  offer_count: number;
  avg_discount: number;
  min_price_seen: number;
  categories: string[];
}

export interface DailyVolume {
  date: string;
  messages: number;
  offers: number;
}

// ── API response wrappers ──

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  has_more: boolean;
}

export interface SearchFilters {
  q?: string;
  store?: string;
  min_price?: number;
  max_price?: number;
  date_from?: string;
  date_to?: string;
  group_id?: number;
  installment_max?: number;
  sort_by?: "price" | "date" | "discount";
  sort_order?: "asc" | "desc";
  page?: number;
  per_page?: number;
}
