# Minnesstruktur - Saga & Christian
*Strukturerad och portabel minneshantering för vårt team.*

## 📂 Struktur

```
memory/
├── README.md              # Denna fil - översikt
├── daily/                 # Dagliga loggar
│   ├── 2025-01-17.md     # Konversationer, vad som hände
│   └── 2025-01-18.md
├── projects/              # Projektspecifikt minne
│   └── YouTube-comeback/ # YouTube-kanalens återupplivande
├── decisions/             # Viktiga beslut vi tar
│   └── 2025-01-decisions.md
├── ideas/                 # Idéer vi vill utforska
│   └── business-ideas.md
└── TOOLS.md              # Miljö-specifik info (flyttas separat)
```

## 🔄 Portabilitet

Allt i denna mapp (förutom TOOLS.md) är **portabelt** - kan kopieras/laddas upp till GitHub och flyttas mellan miljöer.

**TOOLS.md** innehåller:
- API-nycklar (dolda i .env)
- Lokala sökvägar
- Datorspecifika inställningar
- Denna fil ska INTE pushas till GitHub!

## 📝 Mall för Daily Log

```markdown
# YYYY-MM-DD - Kort titel

## Vad hände idag
- Punkt 1
- Punkt 2

## Beslut tagna
- Beslut X: Motivation

## Nästa steg
1. Gör detta
2. Gör sedan detta

## Kod/Snippet (om relevant)
```

## 🔍 Snabb åtkomst

- **Senaste:** Se `daily/` mappen
- **Viktiga beslut:** `decisions/`
- **Pågående projekt:** `projects/`
- **Idéer:** `ideas/`

---
*Skapad: 2025-01-17 av Saga*
