"use client";

import type { Offer } from "@/types";
import { formatBRL, formatDiscount, formatRelative, cn } from "@/lib/utils";
import { Badge } from "@/components/ui";
import {
  ExternalLink,
  MessageCircle,
  Tag,
  Truck,
  CreditCard,
} from "lucide-react";

interface OfferCardProps {
  offer: Offer;
  compact?: boolean;
}

export function OfferCard({ offer, compact = false }: OfferCardProps) {
  return (
    <div
      className={cn(
        "group rounded-xl border border-surface-200 bg-white transition-all hover:shadow-md hover:border-brand-200",
        compact ? "p-3" : "p-5"
      )}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <h3
            className={cn(
              "font-semibold text-surface-900 leading-tight",
              compact ? "text-sm" : "text-base"
            )}
          >
            {offer.product_name_raw}
          </h3>
          <div className="mt-1 flex flex-wrap items-center gap-2">
            {offer.store && (
              <Badge variant="info" size="sm">
                {offer.store}
              </Badge>
            )}
            {offer.brand && (
              <Badge size="sm">{offer.brand}</Badge>
            )}
            <span className="text-xs text-surface-700/50">
              {formatRelative(offer.offer_date)}
            </span>
          </div>
        </div>

        {/* Discount badge */}
        {offer.discount_pct && offer.discount_pct > 0 && (
          <div className="shrink-0 rounded-lg bg-red-500 px-2.5 py-1 text-sm font-bold text-white">
            {formatDiscount(offer.discount_pct)}
          </div>
        )}
      </div>

      {/* Price section */}
      <div className="mt-3 flex items-baseline gap-3">
        <span className="text-xl font-bold text-brand-700">
          {formatBRL(offer.price_current)}
        </span>
        {offer.price_original &&
          offer.price_original !== offer.price_current && (
            <span className="text-sm text-surface-700/40 line-through">
              {formatBRL(offer.price_original)}
            </span>
          )}
      </div>

      {/* Details */}
      {!compact && (
        <div className="mt-3 flex flex-wrap gap-3 text-xs text-surface-700/60">
          {offer.pix_price && (
            <span className="flex items-center gap-1">
              <CreditCard className="h-3.5 w-3.5" />
              PIX: {formatBRL(offer.pix_price)}
            </span>
          )}
          {offer.installments && (
            <span className="flex items-center gap-1">
              <CreditCard className="h-3.5 w-3.5" />
              {offer.installments}
            </span>
          )}
          {offer.coupon && (
            <span className="flex items-center gap-1">
              <Tag className="h-3.5 w-3.5" />
              {offer.coupon}
            </span>
          )}
          {offer.shipping && (
            <span className="flex items-center gap-1">
              <Truck className="h-3.5 w-3.5" />
              {offer.shipping}
            </span>
          )}
        </div>
      )}

      {/* Actions */}
      <div className="mt-3 flex items-center gap-2 border-t border-surface-100 pt-3">
        {offer.link && (
          <a
            href={offer.link}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 rounded-md bg-brand-50 px-3 py-1.5 text-xs font-medium text-brand-700 transition hover:bg-brand-100"
          >
            <ExternalLink className="h-3.5 w-3.5" />
            Ver oferta
          </a>
        )}
        {offer.telegram_link && (
          <a
            href={offer.telegram_link}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 rounded-md bg-blue-50 px-3 py-1.5 text-xs font-medium text-blue-700 transition hover:bg-blue-100"
          >
            <MessageCircle className="h-3.5 w-3.5" />
            Post original
          </a>
        )}
        <span
          className={cn(
            "ml-auto text-xs font-medium",
            offer.confidence >= 0.8
              ? "text-green-600"
              : offer.confidence >= 0.6
              ? "text-amber-600"
              : "text-red-500"
          )}
        >
          {Math.round(offer.confidence * 100)}% confiança
        </span>
      </div>
    </div>
  );
}
