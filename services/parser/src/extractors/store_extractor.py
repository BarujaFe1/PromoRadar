"""Extrator de lojas — dicionário de lojas BR + detecção por URL."""

from __future__ import annotations

import re
from typing import NamedTuple


class StoreResult(NamedTuple):
    name: str
    source: str  # 'url' ou 'text'
    confidence: float


# Mapeamento domínio → nome canônico da loja
STORE_DOMAINS: dict[str, str] = {
    "amazon.com.br": "Amazon",
    "amzn.to": "Amazon",
    "a.]co": "Amazon",
    "magazineluiza.com.br": "Magazine Luiza",
    "magalu.com": "Magazine Luiza",
    "kabum.com.br": "KaBuM!",
    "mercadolivre.com.br": "Mercado Livre",
    "produto.mercadolivre": "Mercado Livre",
    "americanas.com.br": "Americanas",
    "casasbahia.com.br": "Casas Bahia",
    "extra.com.br": "Extra",
    "pontofrio.com.br": "Ponto Frio",
    "shopee.com.br": "Shopee",
    "shope.ee": "Shopee",
    "aliexpress.com": "AliExpress",
    "pichau.com.br": "Pichau",
    "terabyteshop.com.br": "Terabyte Shop",
    "pelando.com.br": "Pelando",
    "submarino.com.br": "Submarino",
    "carrefour.com.br": "Carrefour",
    "fastshop.com.br": "Fast Shop",
    "girafa.com.br": "Girafa",
    "colombo.com.br": "Lojas Colombo",
    "samsung.com.br": "Samsung",
    "apple.com.br": "Apple",
    "dell.com.br": "Dell",
    "lenovo.com.br": "Lenovo",
    "hp.com.br": "HP",
    "banggood.com": "Banggood",
    "gearbest.com": "GearBest",
    "goboo.com": "Goboo",
    "hotmart.com": "Hotmart",
    "netshoes.com.br": "Netshoes",
    "centauro.com.br": "Centauro",
    "dafiti.com.br": "Dafiti",
    "zattini.com.br": "Zattini",
    "oboticario.com.br": "O Boticário",
    "natura.com.br": "Natura",
    "belezanaweb.com.br": "Beleza na Web",
    "droga raia": "Droga Raia",
    "drogasil.com.br": "Drogasil",
    "epocacosmeticos.com.br": "Época Cosméticos",
    "kalunga.com.br": "Kalunga",
    "staples.com.br": "Staples",
}

# Nomes de loja no texto (case insensitive)
STORE_TEXT_PATTERNS: dict[str, str] = {
    r"\bamazon\b": "Amazon",
    r"\bmagalu\b": "Magazine Luiza",
    r"\bmagazine\s*luiza\b": "Magazine Luiza",
    r"\bkabum\b": "KaBuM!",
    r"\bmercado\s*livre\b": "Mercado Livre",
    r"\bshopee\b": "Shopee",
    r"\baliexpress\b": "AliExpress",
    r"\bamericanas\b": "Americanas",
    r"\bcasas\s*bahia\b": "Casas Bahia",
    r"\bpichau\b": "Pichau",
    r"\bterabyte\b": "Terabyte Shop",
    r"\bsubmarino\b": "Submarino",
    r"\bcarrefour\b": "Carrefour",
    r"\bfast\s*shop\b": "Fast Shop",
    r"\bnetshoes\b": "Netshoes",
    r"\bcentauro\b": "Centauro",
}


def extract_store_from_url(url: str) -> StoreResult | None:
    """Detecta loja pelo domínio da URL."""
    url_lower = url.lower()
    for domain, store_name in STORE_DOMAINS.items():
        if domain in url_lower:
            return StoreResult(name=store_name, source="url", confidence=0.95)
    return None


def extract_store_from_text(text: str) -> StoreResult | None:
    """Detecta loja por menção no texto."""
    text_lower = text.lower()
    for pattern, store_name in STORE_TEXT_PATTERNS.items():
        if re.search(pattern, text_lower):
            return StoreResult(name=store_name, source="text", confidence=0.80)
    return None


def extract_store(text: str, links: list[str] | None = None) -> StoreResult | None:
    """
    Extrai loja da mensagem. Prioridade: URL > texto.

    Args:
        text: texto da mensagem
        links: URLs extraídas da mensagem
    """
    # Primeiro tenta pelas URLs (mais confiável)
    if links:
        for link in links:
            result = extract_store_from_url(link)
            if result:
                return result

    # Fallback: busca no texto
    return extract_store_from_text(text)
