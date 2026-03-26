"""
Testes do pipeline de extração com mensagens simuladas de promoção reais.

Cada mensagem reflete o estilo caótico de grupos brasileiros de promoção.
"""

import pytest
from datetime import datetime, timezone

from src.extractors.price_extractor import (
    extract_discount_pct,
    extract_installments,
    extract_original_price,
    extract_pix_price,
    extract_prices,
    parse_brl,
)
from src.extractors.product_extractor import extract_product
from src.extractors.store_extractor import extract_store
from src.extractors.coupon_extractor import extract_coupon, extract_shipping
from src.extractors.pipeline import OfferExtractionPipeline
from src.dedup.matcher import are_same_product, compute_similarity, generate_product_fingerprint
from src.normalizers.text_normalizer import normalize_for_search, normalize_product_name


# ============================================================
# Mensagens de teste (simulam grupos reais)
# ============================================================

MESSAGES = {
    "iphone_magalu": (
        "🔥🔥 PRECÃO!! 🔥🔥\n"
        "iPhone 15 Pro Max 256GB Titânio Natural\n"
        "De R$ 9.499,00 por R$ 6.499,00 à vista no PIX\n"
        "Ou 12x de R$ 599,92 sem juros\n"
        "Frete grátis | Cupom: TECH10\n"
        "Magazine Luiza: https://www.magazineluiza.com.br/iphone-15/p/abc123\n"
        "🏃 CORRE QUE ACABA!"
    ),
    "notebook_amazon": (
        "⚡ Notebook Lenovo IdeaPad 3 - Ryzen 5 5500U / 8GB / 256GB SSD\n"
        "De R$ 3.299,00 por R$ 2.499,00 (24% OFF)\n"
        "10x sem juros de R$ 249,90\n"
        "Frete GRÁTIS para Prime\n"
        "https://amzn.to/3xyzABC"
    ),
    "airfryer_shopee": (
        "⚡ RELÂMPAGO ⚡\n"
        "Air Fryer Mondial Family 5L Inox\n"
        "R$ 199,90 no Pix\n"
        "Shopee: https://shope.ee/abc123\n"
        "cupom: AIRFRY20"
    ),
    "galaxy_kabum": (
        "Samsung Galaxy S24 Ultra 512GB\n"
        "R$ 5.999,00 no pix ou 12x R$ 549,92\n"
        "Link: https://www.kabum.com.br/produto/456789"
    ),
    "monitor_pichau": (
        "Monitor Gamer LG UltraGear 27\" 144Hz IPS 1ms\n"
        "por R$ 1.299,00\n"
        "https://www.pichau.com.br/monitor-lg-ultragear\n"
        "Frete: R$ 29,90"
    ),
    "sem_oferta": (
        "Bom dia pessoal! Alguém sabe se o fone JBL T110 é bom?\n"
        "Meu amigo recomendou mas tô na dúvida."
    ),
    "oferta_bagunçada": (
        "olha issooo\n"
        "headset gamer hiper mega 7.1 surround rgb com led\n"
        "tava 299 agora 149,90!!! metade do preço\n"
        "kabum"
    ),
}


# ============================================================
# Testes do extrator de preço
# ============================================================

class TestPriceExtractor:

    def test_parse_brl_with_dots_and_comma(self):
        assert parse_brl("1.234,56") == 1234.56

    def test_parse_brl_without_dots(self):
        assert parse_brl("199,90") == 199.90

    def test_parse_brl_integer(self):
        assert parse_brl("299") == 299.0

    def test_extract_prices_from_iphone(self):
        prices = extract_prices(MESSAGES["iphone_magalu"])
        values = [p.value for p in prices]
        assert 9499.0 in values
        assert 6499.0 in values

    def test_extract_original_price(self):
        result = extract_original_price(MESSAGES["iphone_magalu"])
        assert result is not None
        assert result.value == 9499.0

    def test_extract_pix_price(self):
        result = extract_pix_price(MESSAGES["airfryer_shopee"])
        assert result is not None
        assert result.value == 199.90

    def test_extract_installments(self):
        result = extract_installments(MESSAGES["iphone_magalu"])
        assert result is not None
        assert result.count == 12
        assert abs(result.value - 599.92) < 0.01

    def test_extract_discount_pct(self):
        result = extract_discount_pct(MESSAGES["notebook_amazon"])
        assert result is not None
        assert result == 24.0

    def test_no_prices_in_non_offer(self):
        prices = extract_prices(MESSAGES["sem_oferta"])
        assert len(prices) == 0


# ============================================================
# Testes do extrator de produto
# ============================================================

class TestProductExtractor:

    def test_extract_iphone(self):
        result = extract_product(MESSAGES["iphone_magalu"])
        assert result is not None
        assert "iPhone" in result.name or "iphone" in result.name.lower()
        assert result.brand == "Apple"

    def test_extract_notebook(self):
        result = extract_product(MESSAGES["notebook_amazon"])
        assert result is not None
        assert "lenovo" in result.name.lower() or "ideapad" in result.name.lower()

    def test_extract_galaxy(self):
        result = extract_product(MESSAGES["galaxy_kabum"])
        assert result is not None
        assert "samsung" in result.name.lower() or "galaxy" in result.name.lower()
        assert result.brand == "Samsung"

    def test_extract_messy_message(self):
        result = extract_product(MESSAGES["oferta_bagunçada"])
        assert result is not None
        assert "headset" in result.name.lower()


# ============================================================
# Testes do extrator de loja
# ============================================================

class TestStoreExtractor:

    def test_store_from_magalu_url(self):
        result = extract_store(
            MESSAGES["iphone_magalu"],
            ["https://www.magazineluiza.com.br/iphone-15/p/abc123"],
        )
        assert result is not None
        assert result.name == "Magazine Luiza"

    def test_store_from_amazon_short_url(self):
        result = extract_store(
            MESSAGES["notebook_amazon"],
            ["https://amzn.to/3xyzABC"],
        )
        assert result is not None
        assert result.name == "Amazon"

    def test_store_from_shopee_url(self):
        result = extract_store(
            MESSAGES["airfryer_shopee"],
            ["https://shope.ee/abc123"],
        )
        assert result is not None
        assert result.name == "Shopee"

    def test_store_from_text_kabum(self):
        result = extract_store(MESSAGES["oferta_bagunçada"])
        assert result is not None
        assert result.name == "KaBuM!"

    def test_no_store_in_question(self):
        result = extract_store(MESSAGES["sem_oferta"])
        # JBL não é loja
        assert result is None


# ============================================================
# Testes do extrator de cupom e frete
# ============================================================

class TestCouponShipping:

    def test_extract_coupon(self):
        assert extract_coupon(MESSAGES["iphone_magalu"]) == "TECH10"
        assert extract_coupon(MESSAGES["airfryer_shopee"]) == "AIRFRY20"

    def test_no_coupon(self):
        assert extract_coupon(MESSAGES["galaxy_kabum"]) is None

    def test_shipping_free(self):
        assert extract_shipping(MESSAGES["iphone_magalu"]) == "Grátis"
        assert extract_shipping(MESSAGES["notebook_amazon"]) == "Grátis"

    def test_shipping_with_price(self):
        assert extract_shipping(MESSAGES["monitor_pichau"]) == "R$ 29,90"


# ============================================================
# Testes do pipeline completo
# ============================================================

class TestPipeline:

    def setup_method(self):
        self.pipeline = OfferExtractionPipeline()

    def test_iphone_full_extraction(self):
        offer = self.pipeline.extract(
            text=MESSAGES["iphone_magalu"],
            links=["https://www.magazineluiza.com.br/iphone-15/p/abc123"],
            raw_message_id=1,
            group_id=100,
        )
        assert offer is not None
        assert offer.product_name is not None
        assert offer.price_current is not None
        assert offer.price_current <= 6499.0
        assert offer.store == "Magazine Luiza"
        assert offer.coupon == "TECH10"
        assert offer.shipping == "Grátis"
        assert offer.confidence >= 0.7

    def test_notebook_extraction(self):
        offer = self.pipeline.extract(
            text=MESSAGES["notebook_amazon"],
            links=["https://amzn.to/3xyzABC"],
        )
        assert offer is not None
        assert offer.store == "Amazon"
        assert offer.price_current is not None
        assert offer.installment_count == 10

    def test_airfryer_extraction(self):
        offer = self.pipeline.extract(
            text=MESSAGES["airfryer_shopee"],
            links=["https://shope.ee/abc123"],
        )
        assert offer is not None
        assert offer.pix_price == 199.90 or offer.price_current == 199.90
        assert offer.coupon == "AIRFRY20"

    def test_non_offer_returns_none(self):
        offer = self.pipeline.extract(text=MESSAGES["sem_oferta"])
        # Pode retornar None ou oferta com baixa confiança
        if offer:
            assert offer.confidence < 0.4

    def test_messy_message_extraction(self):
        offer = self.pipeline.extract(text=MESSAGES["oferta_bagunçada"])
        assert offer is not None
        assert offer.price_current is not None
        assert offer.store == "KaBuM!"

    def test_batch_extraction(self):
        messages = [
            {"id": 1, "text": MESSAGES["iphone_magalu"], "group_id": 100},
            {"id": 2, "text": MESSAGES["notebook_amazon"], "group_id": 100},
            {"id": 3, "text": MESSAGES["sem_oferta"], "group_id": 100},
        ]
        results = self.pipeline.extract_batch(messages)
        # Pelo menos iPhone e Notebook devem ser extraídos
        assert len(results) >= 2


# ============================================================
# Testes de deduplicação
# ============================================================

class TestDedup:

    def test_exact_match(self):
        result = are_same_product("iPhone 15 Pro Max 256GB", "iPhone 15 Pro Max 256GB")
        assert result.is_match is True
        assert result.score == 1.0

    def test_case_insensitive_match(self):
        result = are_same_product("iphone 15 pro max", "iPhone 15 Pro Max")
        assert result.is_match is True

    def test_similar_names_match(self):
        result = are_same_product(
            "iPhone 15 Pro Max 256GB",
            "Apple iPhone 15 Pro Max 256GB",
        )
        assert result.is_match is True
        assert result.score >= 0.8

    def test_different_products_no_match(self):
        result = are_same_product("iPhone 15 Pro Max", "Samsung Galaxy S24 Ultra")
        assert result.is_match is False

    def test_similarity_score(self):
        score = compute_similarity(
            "Lenovo IdeaPad 3 Notebook",
            "Lenovo IdeaPad 3",
        )
        assert score >= 0.6

    def test_fingerprint_stability(self):
        fp1 = generate_product_fingerprint("iPhone 15 Pro Max 256GB")
        fp2 = generate_product_fingerprint("256GB iPhone 15 Pro Max")
        assert fp1 == fp2  # tokens ordenados → mesmo fingerprint


# ============================================================
# Testes de normalização
# ============================================================

class TestNormalization:

    def test_normalize_for_search(self):
        result = normalize_for_search("iPhone 15 Próximo à Vista!")
        assert result == "iphone 15 proximo a vista"

    def test_normalize_product_name(self):
        result = normalize_product_name("iPhone 15 Pro Max 256 GB")
        assert "256gb" in result
        assert "iphone" in result

    def test_normalize_product_name_promax(self):
        result = normalize_product_name("Galaxy S24 Pro Max")
        assert "promax" in result
