# Invoice Processor
🧾 Enkel PDF-fakturahantering för småföretag

## 🎯 Vad det gör
- Läser PDF-fakturor och textfiler
- Extraherar automatiskt:
  - 💰 Belopp (inkl. moms)
  - 📅 Fakturadatum
  - 📆 Förfallodatum
  - 🔢 Fakturanummer
  - 🏢 Leverantör
- Exporterar till JSON
- Genererar rapporter

## 🚀 Snabbstart

### Installation
```bash
pip install -r requirements.txt
```

### Användning

**En fil:**
```bash
python invoice_processor.py faktura.pdf
```

**Hela mappen:**
```bash
python invoice_processor.py ./fakturor/ -o resultat.json -r
```

**Med rapport:**
```bash
python invoice_processor.py ./fakturor/ -r
```

## 💡 Affärsmöjlighet

Detta är ett **enkelt verktyg** som kan:
- Säljas som SaaS (månadsavgift)
- Erbjudas som tjänst (per faktura)
- Användas internt för Citedo-kunder
- Byggas ut till fullständig bokföringsintegration

## 🔧 Nästa steg

1. Lägg till fler fakturaformat
2. Integrera med bokföringsprogram (Fortnox, Visma)
3. Bygg webbgränssnitt
4. Automatisk betalningspåminnelse

---
**Status:** MVP klar för test!
**Skapad:** 2026-02-04 med AI-hjälp
