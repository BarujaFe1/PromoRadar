"""
Pipeline principal de extração de ofertas.

Orquestra os extratores individuais (preço, produto, loja, cupom, frete)
e compõe o resultado final com score de confiança.
"""

from __future__ import annotations

import json
import re
from datetime import datetime

from src.extractors.coupon_extractor import extract_coupon, extract_shipping
from src.extractors.price_extractor import (
    extract_discount_pct,
    extract_installments,
    extract_original_price,
    extract_pix_price,
    extract_prices,
)
from src.extractors.product_extractor import extract_product
from src.extractors.store_extractor import extract_store
from src.models.offer import ExtractedOffer
from src.normalizers.text_normalizer import normalize_text

# URL regex para extrair links do texto
URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)


class OfferExtractionPipeline:
    """
    Pipeline de 4 estágios para extração de ofertas:

    1. Pré-processamento (normalização de texto)
    2. Extração de entidades (preço, produto, loja, etc.)
    3. Cálculo de confiança
    4. Validação e output

    Opcionalmente, estágio 5: LLM fallback para baixa confiança.
    """

    CONFIDENCE_THRESHOLD = 0.4  # mínimo para considerar válido
    LLM_THRESHOLD = 0.6         # abaixo disso, usa LLM fallback

    def __init__(self, llm_enabled: bool = False) -> None:
        self._llm_enabled = llm_enabled

    def extract(
        self,
        text: str,
        links: list[str] | None = None,
        raw_message_id: int | None = None,
        group_id: int | None = None,
        message_date: datetime | None = None,
    ) -> ExtractedOffer | None:
        """
        Extrai uma oferta estruturada de uma mensagem de texto.

        Args:
            text: texto da mensagem
            links: URLs já extraídas (opcional, senão extrai do texto)
            raw_message_id: ID da mensagem no banco
            group_id: ID do grupo
            message_date: data da mensagem

        Returns:
            ExtractedOffer ou None se não for uma oferta válida
        """
        if not text or not text.strip():
            return None

        # ── Estágio 1: Pré-processamento ──
        cleaned_text = normalize_text(text)
        if links is None:
            links = URL_PATTERN.findall(text)

        # ── Estágio 2: Extração de entidades ──
        offer = ExtractedOffer(
            raw_message_id=raw_message_id,
            group_id=group_id,
            offer_date=message_date,
        )

        # Produto
        product_result = extract_product(cleaned_text)
        if product_result:
            offer.product_name = product_result.name
            offer.brand = product_result.brand
            offer.model = product_result.model

        # Preços
        prices = extract_prices(text)  # usa texto original para preservar R$
        if prices:
            # O menor preço geralmente é o preço atual
            sorted_prices = sorted(prices, key=lambda p: p.value)
            offer.price_current = sorted_prices[0].value
            # Se houver mais de um preço, o maior pode ser o original
            if len(sorted_prices) > 1:
                offer.price_original = sorted_prices[-1].value

        # Tenta preço original explícito
        original = extract_original_price(text)
        if original:
            offer.price_original = original.value

        # Preço PIX
        pix = extract_pix_price(text)
        if pix:
            offer.pix_price = pix.value
            # Se preço PIX é menor que current, current vira original
            if offer.price_current and pix.value < offer.price_current:
                if not offer.price_original:
                    offer.price_original = offer.price_current
                offer.price_current = pix.value

        # Parcelas
        installments = extract_installments(text)
        if installments:
            offer.installments_raw = installments.raw
            offer.installment_count = installments.count
            offer.installment_value = installments.value
            # Se não tem preço current, calcula pelo parcelamento
            if not offer.price_current:
                offer.price_current = installments.count * installments.value

        # Desconto
        discount = extract_discount_pct(text)
        if discount:
            offer.discount_pct = discount
        else:
            offer.compute_discount()

        # Loja
        store = extract_store(text, links)
        if store:
            offer.store = store.name

        # Cupom
        offer.coupon = extract_coupon(text)

        # Frete
        offer.shipping = extract_shipping(text)

        # Link (primeiro link encontrado)
        if links:
            offer.link = links[0]

        # Link do Telegram (construído se tiver group_id e msg_id)
        if group_id and raw_message_id:
            offer.telegram_link = f"https://t.me/c/{group_id}/{raw_message_id}"

        # ── Estágio 3: Score de confiança ──
        offer.confidence = self._compute_confidence(offer)
        offer.extraction_method = "regex"

        # ── Estágio 4: Validação ──
        if not offer.is_valid:
            return None

        if offer.confidence < self.CONFIDENCE_THRESHOLD:
            return None

        # TODO: Estágio 5 — LLM fallback
        # if self._llm_enabled and offer.confidence < self.LLM_THRESHOLD:
        #     offer = await self._llm_fallback(text, offer)

        return offer

    def extract_batch(
        self,
        messages: list[dict],
    ) -> list[ExtractedOffer]:
        """
        Processa um lote de mensagens.

        Args:
            messages: lista de dicts com 'id', 'text', 'links', 'group_id', 'date'
        """
        results: list[ExtractedOffer] = []
        for msg in messages:
            offer = self.extract(
                text=msg.get("text", ""),
                links=msg.get("links"),
                raw_message_id=msg.get("id"),
                group_id=msg.get("group_id"),
                message_date=msg.get("date"),
            )
            if offer:
                results.append(offer)
        return results

    def _compute_confidence(self, offer: ExtractedOffer) -> float:
        """
        Calcula score de confiança baseado nos campos extraídos.

        Pesos:
        - has_price: 0.30
        - has_product_name: 0.25
        - has_store: 0.20
        - has_link: 0.15
        - has_discount_or_coupon: 0.10
        """
        score = 0.0

        if offer.price_current:
            score += 0.30
        if offer.product_name:
            score += 0.25
        if offer.store:
            score += 0.20
        if offer.link:
            score += 0.15
        if offer.discount_pct or offer.coupon:
            score += 0.10

        return round(score, 2)
