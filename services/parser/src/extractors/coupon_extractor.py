"""Extrator de cupom e frete."""

from __future__ import annotations

import re


# Cupom: CUPOM10, cupom: TECH20, use o código ABC123
COUPON_PATTERNS = [
    re.compile(
        r"(?:cupom|c[oó]digo|voucher|promo(?:code)?)\s*:?\s*[\"']?([A-Z0-9]{3,20})[\"']?",
        re.IGNORECASE,
    ),
    re.compile(
        r"use\s+(?:o\s+)?(?:cupom|c[oó]digo)\s+[\"']?([A-Z0-9]{3,20})[\"']?",
        re.IGNORECASE,
    ),
]

# Frete grátis ou valor do frete
SHIPPING_FREE_PATTERN = re.compile(
    r"frete\s*(?:gr[aá]tis|free|zero|0)",
    re.IGNORECASE,
)
SHIPPING_PRICE_PATTERN = re.compile(
    r"frete\s*:?\s*R\$\s?(\d{1,3}(?:,\d{2})?)",
    re.IGNORECASE,
)


def extract_coupon(text: str) -> str | None:
    """Extrai código de cupom da mensagem."""
    for pattern in COUPON_PATTERNS:
        match = pattern.search(text)
        if match:
            coupon = match.group(1).upper().strip()
            # Filtra falsos positivos
            if len(coupon) >= 3 and not coupon.isdigit():
                return coupon
    return None


def extract_shipping(text: str) -> str | None:
    """Extrai informação de frete."""
    if SHIPPING_FREE_PATTERN.search(text):
        return "Grátis"

    match = SHIPPING_PRICE_PATTERN.search(text)
    if match:
        return f"R$ {match.group(1)}"

    return None
