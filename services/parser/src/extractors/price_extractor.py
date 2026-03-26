"""Extrator de preços e condições de pagamento via regex."""

from __future__ import annotations

import re
from typing import NamedTuple


class PriceResult(NamedTuple):
    value: float
    raw: str
    is_pix: bool = False
    is_original: bool = False


class InstallmentResult(NamedTuple):
    count: int
    value: float
    raw: str


# ── Regex patterns ──

# Preço: R$ 1.234,56 ou R$1234.56 ou 1.234,56
PRICE_PATTERN = re.compile(
    r"R\$\s?"                          # prefixo R$
    r"(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)"  # 1.234,56
    r"|"
    r"R\$\s?"
    r"(\d+(?:,\d{2})?)",              # 1234,56 sem ponto de milhar
    re.IGNORECASE,
)

# Preço original ("De R$ X" ou "de R$ X por")
ORIGINAL_PRICE_PATTERN = re.compile(
    r"(?:de|era|antes|custava)\s+R\$\s?"
    r"(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
    re.IGNORECASE,
)

# Preço PIX/à vista
PIX_PATTERN = re.compile(
    r"(?:pix|à\s*vista|a\s*vista|boleto)\s*:?\s*R\$\s?"
    r"(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)"
    r"|"
    r"R\$\s?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)"
    r"\s*(?:no\s+pix|à\s*vista|a\s*vista|no\s+boleto)",
    re.IGNORECASE,
)

# Parcelamento: 12x de R$ 99,90 ou 12x R$99,90 ou 12x sem juros de R$ 99,90
INSTALLMENT_PATTERN = re.compile(
    r"(\d{1,2})x\s*(?:de\s+|s/?(?:em\s+)?juros\s+(?:de\s+)?|sem\s+juros\s+(?:de\s+)?)?"
    r"R\$\s?(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
    re.IGNORECASE,
)

# Desconto percentual
DISCOUNT_PATTERN = re.compile(
    r"(\d{1,2})%\s*(?:off|desc(?:onto)?|de\s+desconto)",
    re.IGNORECASE,
)


def parse_brl(raw: str) -> float:
    """Converte string de preço BR para float. Ex: '1.234,56' → 1234.56"""
    cleaned = raw.strip()
    # Remove pontos de milhar, troca vírgula por ponto
    cleaned = cleaned.replace(".", "").replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def extract_prices(text: str) -> list[PriceResult]:
    """Extrai todos os preços encontrados no texto."""
    results: list[PriceResult] = []

    for match in PRICE_PATTERN.finditer(text):
        raw = match.group(1) or match.group(2)
        if raw:
            value = parse_brl(raw)
            if value > 0:
                results.append(PriceResult(value=value, raw=match.group(0)))

    # Fallback: preços sem prefixo R$ em contexto de oferta ("por 149,90", "agora 299")
    if not results:
        bare_pattern = re.compile(
            r"(?:por|agora|tava|era|de)\s+(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)",
            re.IGNORECASE,
        )
        for match in bare_pattern.finditer(text):
            value = parse_brl(match.group(1))
            if value > 1:
                results.append(PriceResult(value=value, raw=match.group(0)))

    return results


def extract_original_price(text: str) -> PriceResult | None:
    """Extrai preço original ('De R$ X')."""
    match = ORIGINAL_PRICE_PATTERN.search(text)
    if match:
        value = parse_brl(match.group(1))
        if value > 0:
            return PriceResult(value=value, raw=match.group(0), is_original=True)
    return None


def extract_pix_price(text: str) -> PriceResult | None:
    """Extrai preço no PIX/à vista."""
    match = PIX_PATTERN.search(text)
    if match:
        raw = match.group(1) or match.group(2)
        if raw:
            value = parse_brl(raw)
            if value > 0:
                return PriceResult(value=value, raw=match.group(0), is_pix=True)
    return None


def extract_installments(text: str) -> InstallmentResult | None:
    """Extrai informação de parcelamento."""
    match = INSTALLMENT_PATTERN.search(text)
    if match:
        count = int(match.group(1))
        value = parse_brl(match.group(2))
        if count > 0 and value > 0:
            return InstallmentResult(
                count=count,
                value=value,
                raw=match.group(0),
            )
    return None


def extract_discount_pct(text: str) -> float | None:
    """Extrai percentual de desconto."""
    match = DISCOUNT_PATTERN.search(text)
    if match:
        pct = float(match.group(1))
        if 0 < pct <= 99:
            return pct
    return None
