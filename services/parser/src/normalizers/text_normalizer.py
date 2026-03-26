"""Normalizadores de texto para pré-processamento."""

from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    """
    Normaliza texto de mensagem de promoção.

    - Remove emojis duplicados
    - Normaliza espaços e quebras de linha
    - Mantém acentos (importante para português)
    """
    if not text:
        return ""

    # Remove variações de emojis repetidos
    text = re.sub(r"([\U00010000-\U0010ffff])\1{2,}", r"\1", text)

    # Normaliza espaços múltiplos
    text = re.sub(r"[ \t]+", " ", text)

    # Normaliza quebras de linha múltiplas
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def normalize_for_search(text: str) -> str:
    """
    Normaliza texto para busca e comparação.

    - Lowercase
    - Remove acentos
    - Remove caracteres especiais
    """
    if not text:
        return ""

    text = text.lower().strip()

    # Remove acentos
    nfkd = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in nfkd if not unicodedata.combining(c))

    # Remove caracteres especiais exceto espaço e hífen
    text = re.sub(r"[^a-z0-9\s\-]", "", text)

    # Normaliza espaços
    text = re.sub(r"\s+", " ", text).strip()

    return text


def normalize_product_name(name: str) -> str:
    """
    Normaliza nome de produto para deduplicação.

    - Remove variações de capacidade (256GB, 256 GB, 256gb)
    - Padroniza separadores
    """
    if not name:
        return ""

    normalized = normalize_for_search(name)

    # Padroniza unidades de armazenamento
    normalized = re.sub(r"(\d+)\s*(gb|tb|mb)", r"\1\2", normalized)

    # Padroniza "pro max" → "promax" etc.
    normalized = re.sub(r"pro\s+max", "promax", normalized)

    return normalized
