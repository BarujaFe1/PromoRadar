"""Modelos de domínio para ofertas extraídas."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ExtractedOffer:
    """Resultado da extração de uma mensagem de promoção."""

    product_name: str | None = None
    brand: str | None = None
    model: str | None = None
    price_current: float | None = None
    price_original: float | None = None
    discount_pct: float | None = None
    store: str | None = None
    installments_raw: str | None = None
    installment_count: int | None = None
    installment_value: float | None = None
    pix_price: float | None = None
    coupon: str | None = None
    shipping: str | None = None
    link: str | None = None
    confidence: float = 0.0
    extraction_method: str = "regex"

    # Campos de controle
    raw_message_id: int | None = None
    group_id: int | None = None
    offer_date: datetime | None = None
    telegram_link: str | None = None

    @property
    def is_valid(self) -> bool:
        """Uma oferta precisa no mínimo de nome do produto OU preço."""
        return bool(self.product_name) or self.price_current is not None

    def compute_discount(self) -> None:
        """Calcula desconto percentual se tiver preço atual e original."""
        if self.price_current and self.price_original and self.price_original > 0:
            self.discount_pct = round(
                (1 - self.price_current / self.price_original) * 100, 2
            )


@dataclass
class ProductCandidate:
    """Candidato a produto normalizado para deduplicação."""

    name: str
    brand: str | None = None
    model: str | None = None
    aliases: list[str] = field(default_factory=list)
    fingerprint: str = ""  # hash normalizado para comparação rápida
