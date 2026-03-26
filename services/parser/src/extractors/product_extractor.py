"""Extrator de nome de produto, marca e modelo via heurísticas."""

from __future__ import annotations

import re
from typing import NamedTuple


class ProductResult(NamedTuple):
    name: str
    brand: str | None
    model: str | None
    confidence: float


# Marcas conhecidas (case-insensitive)
KNOWN_BRANDS: dict[str, str] = {
    "apple": "Apple", "iphone": "Apple", "ipad": "Apple", "macbook": "Apple",
    "samsung": "Samsung", "galaxy": "Samsung",
    "xiaomi": "Xiaomi", "redmi": "Xiaomi", "poco": "Xiaomi",
    "motorola": "Motorola", "moto": "Motorola",
    "lg": "LG",
    "sony": "Sony", "playstation": "Sony", "ps5": "Sony", "ps4": "Sony",
    "microsoft": "Microsoft", "xbox": "Microsoft", "surface": "Microsoft",
    "nintendo": "Nintendo", "switch": "Nintendo",
    "dell": "Dell", "lenovo": "Lenovo", "thinkpad": "Lenovo",
    "hp": "HP", "asus": "ASUS", "rog": "ASUS",
    "acer": "Acer", "razer": "Razer",
    "logitech": "Logitech", "jbl": "JBL", "bose": "Bose",
    "philips": "Philips", "mondial": "Mondial", "electrolux": "Electrolux",
    "brastemp": "Brastemp", "consul": "Consul",
    "nike": "Nike", "adidas": "Adidas", "puma": "Puma",
    "havaianas": "Havaianas",
    "nvidia": "NVIDIA", "geforce": "NVIDIA", "rtx": "NVIDIA",
    "amd": "AMD", "ryzen": "AMD", "radeon": "AMD",
    "intel": "Intel",
    "kingston": "Kingston", "crucial": "Crucial",
    "wd": "Western Digital", "seagate": "Seagate",
    "gopro": "GoPro", "dji": "DJI",
    "kindle": "Amazon", "echo": "Amazon", "alexa": "Amazon",
    "airfryer": "Air Fryer",  # categoria genérica
}

# Padrões de modelo comuns
MODEL_PATTERNS = [
    # iPhone 15 Pro Max 256GB
    re.compile(r"(iphone\s+\d+\s*(?:pro\s*max|pro|plus|mini)?(?:\s+\d+\s*gb)?)", re.IGNORECASE),
    # Galaxy S24 Ultra 512GB
    re.compile(r"(galaxy\s+[a-z]?\d+\s*(?:ultra|plus|fe)?(?:\s+\d+\s*gb)?)", re.IGNORECASE),
    # RTX 4090 / GTX 1660
    re.compile(r"((?:rtx|gtx|rx)\s*\d{3,4}\s*(?:ti|super|xt)?)", re.IGNORECASE),
    # Ryzen 5 5600X / i7-13700K
    re.compile(r"((?:ryzen\s+[3579]|i[3579][-\s])\s*\d{4,5}[a-z]*)", re.IGNORECASE),
    # PS5 / Xbox Series X
    re.compile(r"(ps[45]\s*(?:slim|pro|digital)?|xbox\s+series\s+[xXsS])", re.IGNORECASE),
    # Modelo genérico: letras+números (ex: IdeaPad 3, Redmi Note 13)
    re.compile(r"([A-Z][a-zA-Z]+\s+(?:Note\s+)?\d+\s*(?:Pro|Plus|Max|Ultra|Lite|SE)?)", re.IGNORECASE),
]

# Linhas/frases que NÃO são nomes de produto (ruído)
NOISE_PATTERNS = [
    re.compile(r"^(🔥|⚡|💥|🚨|📢|‼️|✅|❗|👉)"),  # emojis de chamada
    re.compile(r"^(link|compre|aproveite|corre|oferta|promo|cupom|frete)", re.IGNORECASE),
    re.compile(r"^(de r\$|por r\$|r\$)", re.IGNORECASE),
    re.compile(r"^\d+x\s", re.IGNORECASE),  # "12x de..."
    re.compile(r"^(prec|olha|gente|pessoal|bom dia|boa tarde|boa noite)", re.IGNORECASE),  # conversacional
    re.compile(r"^[A-ZÁÉÍÓÚÂÊÔÃÕ\s!?]{3,}$"),  # linhas ALL CAPS curtas como "PRECÃO!!"
]


def extract_product(text: str) -> ProductResult | None:
    """
    Extrai nome do produto, marca e modelo do texto da mensagem.

    Estratégia:
    1. Procura modelos conhecidos (alta confiança)
    2. Identifica marca por dicionário
    3. Usa a primeira linha "substancial" como nome do produto
    """
    if not text or not text.strip():
        return None

    brand: str | None = None
    model: str | None = None
    confidence = 0.0

    text_lower = text.lower()

    # 1. Detecta marca
    for keyword, brand_name in KNOWN_BRANDS.items():
        if keyword in text_lower:
            brand = brand_name
            confidence += 0.2
            break

    # 2. Detecta modelo
    for pattern in MODEL_PATTERNS:
        match = pattern.search(text)
        if match:
            model = match.group(1).strip()
            confidence += 0.3
            break

    # 3. Extrai nome do produto: prefere linha que contém o modelo
    product_name = None
    if model:
        product_name = _extract_line_containing(text, model)
    if not product_name:
        product_name = _extract_first_product_line(text)
    if product_name:
        confidence += 0.3

    # Se temos modelo mas não nome, usa o modelo como nome
    if not product_name and model:
        product_name = model
        if brand:
            product_name = f"{brand} {model}"

    if not product_name:
        return None

    # Limpa o nome
    product_name = _clean_product_name(product_name)
    if len(product_name) < 3:
        return None

    return ProductResult(
        name=product_name,
        brand=brand,
        model=model,
        confidence=min(confidence, 1.0),
    )


def _extract_line_containing(text: str, keyword: str) -> str | None:
    """Extrai a primeira linha que contém a keyword (modelo/marca)."""
    keyword_lower = keyword.lower()
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or len(line) < 5:
            continue
        if keyword_lower in line.lower():
            cleaned = _clean_product_name(line)
            if len(cleaned) >= 5:
                return cleaned
    return None


def _extract_first_product_line(text: str) -> str | None:
    """
    Extrai a primeira linha do texto que parece ser um nome de produto.
    Ignora emojis, frases de chamada e linhas de preço.
    """
    lines = text.strip().split("\n")

    for line in lines:
        line = line.strip()
        if not line or len(line) < 5:
            continue

        # Pula linhas que são ruído
        is_noise = any(p.search(line) for p in NOISE_PATTERNS)
        if is_noise:
            # Remove o emoji/prefixo e tenta de novo
            cleaned = re.sub(r"^[🔥⚡💥🚨📢‼️✅❗👉\s]+", "", line).strip()
            if cleaned and len(cleaned) > 5:
                line = cleaned
            else:
                continue

        # Pula linhas que são apenas preço
        if re.match(r"^R\$\s?\d", line):
            continue

        return line

    return None


def _clean_product_name(name: str) -> str:
    """Remove ruído do nome do produto."""
    # Remove emojis
    name = re.sub(r"[🔥⚡💥🚨📢‼️✅❗👉🎁🎉💰📦🛒]+", "", name)
    # Remove "por R$..." e "de R$..."
    name = re.sub(r"\s*(?:por|de|a partir de)\s+R\$.*", "", name, flags=re.IGNORECASE)
    # Remove "- R$..."
    name = re.sub(r"\s*[-–]\s*R\$.*", "", name)
    # Remove URLs
    name = re.sub(r"https?://\S+", "", name)
    # Normaliza espaços
    name = re.sub(r"\s+", " ", name).strip()
    # Remove pontuação final
    name = name.rstrip("!.,-–")
    return name.strip()
