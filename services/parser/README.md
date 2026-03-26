# Parser Service

Pipeline NLP que transforma mensagens brutas de promoção em ofertas estruturadas.

## Pipeline de Extração (4 estágios)

1. **Pré-processamento**: normalização de texto, remoção de emojis repetidos
2. **Extração de entidades**: regex + dicionário para preço, produto, loja, cupom, frete
3. **Score de confiança**: ponderação dos campos extraídos (0.0 a 1.0)
4. **Validação**: threshold mínimo de confiança + validação de campos obrigatórios

### Entidades Extraídas

| Campo | Método | Exemplo |
|-------|--------|---------|
| Produto | Heurística + dicionário de marcas | "iPhone 15 Pro Max 256GB" |
| Marca | Dicionário de 50+ marcas | "Apple" |
| Preço atual | Regex `R$ X.XXX,XX` | 6499.00 |
| Preço original | Regex `De R$ X` | 9499.00 |
| Desconto | Regex `X% OFF` ou calculado | 31.58 |
| Loja | URL domain + dicionário de texto | "Magazine Luiza" |
| Parcelamento | Regex `Nx R$ X` | 12x R$ 599,92 |
| PIX | Regex contextual | 5999.00 |
| Cupom | Regex `cupom: XXX` | "TECH10" |
| Frete | Regex `frete grátis` | "Grátis" |

## Deduplicação

Usa `SequenceMatcher` (similar a Levenshtein) após normalização de texto para detectar quando duas mensagens falam do mesmo produto. Threshold: 0.82.

## Testes

```bash
pytest tests/ -v
```

Os testes incluem 7 mensagens simuladas que reproduzem o estilo real de grupos brasileiros de promoção, incluindo mensagens "bagunçadas" sem formatação.
