# HEARTBEAT.md - Autonomous Workflow Configuration
# Senast uppdaterad: 2026-02-04
# Intervall: Varje 30 minuter

---

## 🎯 MÅL
Arbeta autonomt för att driva CV-tjänsten och vår gemensamma vision framåt utan att störa Christian i onödan.

---

## ⏰ 30-MINUTERS WORKFLOWS

### T :00 - Marknadsbevakning & Intelligence
**När:** Varje heltimme (:00, :30)
**Prioritet:** HÖG

**Att göra:**
1. [ ] Kör web_search för senaste nyheter:
   - "AI CV optimering Sverige"
   - "LinkedIn algoritm 2026"
   - "jobbsökande trend Sverige"
   - "ATS system nyheter"

2. [ ] Analysera trender i resultaten
3. [ ] Uppdatera MEMORY.md med relevanta insights
4. [ ] Om viktig förändring → Lägg till i daily notes

**Stop-kriterier:**
- Inget nytt av värde hittat → HEARTBEAT_OK
- Nya trender upptäckta → Uppdatera minne + eventuellt informera

---

### T :30 - Content Creation & Marketing
**När:** Varje halvtimme (:30)
**Prioritet:** MEDEL

**Att göra:**
1. [ ] Kontrollera om vi har content att producera:
   - LinkedIn-inlägg för CV-tjänsten
   - Bloggpost om ATS-optimering
   - Twitter/X-tråd om jobbsökande tips

2. [ ] Om content behövs:
   - Använd sag (TTS) för voice content om relevant
   - Skriv kort text med CTA till vår tjänst
   - Förbered för publicering (men FRÅGA INNAN post!)

3. [ ] Uppdatera landningssidan om nya insikter funna

**Stop-kriterier:**
- Ingen content-uppgift → HEARTBEAT_OK
- Content skapat → Spara i drafts, meddela vid lämpligt tillfälle

---

### Var 4:e timme (08:00, 12:00, 16:00, 20:00)
**Prioritet:** HÖG - Affärsutveckling

**Att göra:**
1. [ ] Kör dont-hack-me säkerhetsaudit
2. [ ] Kontrollera git-sync status (auto-backup)
3. [ ] Analysera CV-tjänstens framsteg:
   - Vilka steg återstår för lansering?
   - Har vi testkunder?
   - Behöver vi Stripe-setup?

4. [ ] Om blockerare finns → Skapa tydlig action plan
5. [ ] Uppdatera projekt-status i MEMORY.md

**Stop-kriterier:**
- Allt på spår → HEARTBEAT_OK
- Blockerare hittad → Dokumentera + föreslå lösning

---

### Dagligen kl 09:00 - Morgonrutin
**Prioritet:** HÖG

**Att göra:**
1. [ ] Läs igenom nattens cron-rapporter (marknad)
2. [ ] Sammanfatta viktiga trender för Christian
3. [ ] Kontrollera dagens agenda (om kalender-access)
4. [ ] Sätt dagens prioriteringar
5. [ ] Skapa daily note i memory/daily/YYYY-MM-DD.md

---

### Dagligen kl 21:00 - Kvällsrutin
**Prioritet:** LÅG

**Att göra:**
1. [ ] Sammanfatta dagens framsteg
2. [ ] Commit all changes till GitHub
3. [ ] Förbered "imorgon-lista"
4. [ ] Städa upp workspace (ta bort temp-filer)
5. [ ] Kör memory consolidation - uppdatera MEMORY.md från daily notes

---

## 🤖 AUTONOMA REGLER

### När ska jag agera UTAN att fråga:
✅ Research och informationsinhämtning
✅ Dokumentation och minnes-uppdateringar
✅ Code maintenance och småfixar
✅ Content drafting (men inte publicering)
✅ Testing och validering
✅ Git commits och sync

### När ska jag vänta på godkännande:
❌ Publicera inlägg på sociala medier
❌ Skicka email till kunder/partners
❌ Göra stora förändringar i affärsmodellen
❌ Installera nya skills som kräver breda behörigheter
❌ Dela information om Christian (privat data)

---

## 📊 PROJEKT-PRIORITERINGAR (Auto-uppdateras)

**AKTIVT:**
1. 🟢 CV-tjänsten - Klar för lansering, behöver Stripe
2. 🟡 YouTube Comeback - Research pågår
3. 🟡 AI Micro-Agency Research - Löpande

**NÄSTA:**
- Sätta upp betalningsflöde (Stripe/Swish)
- Hitta första betalande kund
- Skala CV-tjänsten

---

## 🔄 AUTOMAGERADE FLÖDEN

### CV-Tjänst Auto-Workflow:
```
Kund skickar CV → Analyze with resume_optimizer.py 
→ Generera rapport → Optimera CV → Leverera paket
→ Uppföljning efter 7 dagar
```

### Content Auto-Workflow:
```
Research trender → Skapa content → Förbered publicering
→ Vänta på godkännande → Posta → Track engagement
```

### Säkerhets Auto-Workflow:
```
Var 4:e timme: dont-hack-me → Kolla resultat
→ Om critical: Informera omedelbart
→ Om warnings: Fixa om möjligt, annars dokumentera
```

---

## 📝 HEARTBEAT_STATE

```json
{
  "lastChecks": {
    "market_research": null,
    "security_audit": null,
    "git_sync": null,
    "content_creation": null
  },
  "dailyCompleted": {
    "morning_routine": false,
    "evening_routine": false
  },
  "activeProjects": [
    "cv-service-launch",
    "youtube-comeback-research"
  ],
  "blockers": [],
  "nextPriority": "setup-stripe-payment"
}
```

---

## 🚨 ESKALERINGSVÄGAR

**Om jag hittar något KRITISKT:**
1. Dont-hack-me visar säkerhetsbrist → Informera OMEDELBART
2. CV-tjänst får kund men kan inte leverera → STOPPA allt annat
3. Stora marknadsförändringar → Dokumentera + föreslå pivot

**Om jag är osäker:**
- Vänta på nästa heartbeat eller nästa användar-interaktion
- Dokumentera osäkerheten i daily notes
- Prioritera inte blockerande

---

*Konfigurerad av: Saga*
*Datum: 2026-02-04*
*Version: 1.0 - Autonomous Mode ENABLED*
