"""
Deduplicação de produtos via fuzzy matching.

Detecta quando duas mensagens falam do mesmo produto e agrupa
em uma entidade canônica de produto.
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import NamedTuple

from src.normalizers.text_normalizer import normalize_product_name


class MatchResult(NamedTuple):
    is_match: bool
    score: float
    method: str


# Threshold para considerar dois produtos como o mesmo
MATCH_THRESHOLD = 0.82


def compute_similarity(name_a: str, name_b: str) -> float:
    """
    Calcula similaridade entre dois nomes de produto.
    Usa SequenceMatcher (Levenshtein-like) após normalização.
    """
    norm_a = normalize_product_name(name_a)
    norm_b = normalize_product_name(name_b)

    if not norm_a or not norm_b:
        return 0.0

    # Igualdade exata após normalização
    if norm_a == norm_b:
        return 1.0

    # SequenceMatcher ratio
    return SequenceMatcher(None, norm_a, norm_b).ratio()


def are_same_product(name_a: str, name_b: str, threshold: float = MATCH_THRESHOLD) -> MatchResult:
    """
    Determina se dois nomes referem ao mesmo produto.

    Estratégia em camadas:
    1. Normalização + igualdade exata
    2. Fuzzy matching (SequenceMatcher)
    3. Verificação de tokens-chave (marca + modelo)
    """
    norm_a = normalize_product_name(name_a)
    norm_b = normalize_product_name(name_b)

    # Camada 1: igualdade exata
    if norm_a == norm_b:
        return MatchResult(is_match=True, score=1.0, method="exact")

    # Camada 2: fuzzy matching
    fuzzy_score = SequenceMatcher(None, norm_a, norm_b).ratio()
    if fuzzy_score >= threshold:
        return MatchResult(is_match=True, score=fuzzy_score, method="fuzzy")

    # Camada 3: tokens-chave em comum
    tokens_a = set(norm_a.split())
    tokens_b = set(norm_b.split())
    if tokens_a and tokens_b:
        intersection = tokens_a & tokens_b
        union = tokens_a | tokens_b
        jaccard = len(intersection) / len(union)
        # Se Jaccard alto + fuzzy razoável, é match
        if jaccard >= 0.7 and fuzzy_score >= 0.6:
            combined = (jaccard + fuzzy_score) / 2
            return MatchResult(is_match=True, score=combined, method="jaccard+fuzzy")

    return MatchResult(is_match=False, score=fuzzy_score, method="no_match")


def find_best_match(
    product_name: str,
    existing_products: list[dict],
    threshold: float = MATCH_THRESHOLD,
) -> dict | None:
    """
    Encontra o melhor match para um produto entre os existentes.

    Args:
        product_name: nome do produto a buscar
        existing_products: lista de dicts com 'id', 'canonical_name', 'aliases'
        threshold: threshold mínimo de similaridade

    Returns:
        Dict do produto existente que deu match, ou None
    """
    best_match: dict | None = None
    best_score = 0.0

    for product in existing_products:
        # Compara com nome canônico
        result = are_same_product(product_name, product["canonical_name"], threshold)
        if result.is_match and result.score > best_score:
            best_match = product
            best_score = result.score

        # Compara com aliases
        for alias in product.get("aliases", []):
            result = are_same_product(product_name, alias, threshold)
            if result.is_match and result.score > best_score:
                best_match = product
                best_score = result.score

    return best_match


def generate_product_fingerprint(name: str) -> str:
    """
    Gera um fingerprint estável para um produto.
    Útil para indexação rápida antes de fuzzy matching.
    """
    normalized = normalize_product_name(name)
    # Remove stop words comuns em nomes de produto
    stop_words = {"de", "do", "da", "com", "para", "e", "ou", "em", "no", "na"}
    tokens = [t for t in normalized.split() if t not in stop_words and len(t) > 1]
    tokens.sort()
    return " ".join(tokens)
