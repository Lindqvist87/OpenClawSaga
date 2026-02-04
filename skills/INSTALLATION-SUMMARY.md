# Skills Installation Summary
## 2026-02-04

---

## ✅ Installerade Skills

### Från GitHub:
1. **qmd-skill** (levineam/qmd-skill)
   - Plats: `C:\Users\Hejhej\AppData\Roaming\npm\node_modules\openclaw\skills\qmd-skill`
   - Status: ✅ Installerad
   - Beskrivning: Local hybrid search for markdown notes and docs

2. **clawdbot-supermemory** (supermemoryai/clawdbot-supermemory)
   - Plats: `C:\Users\Hejhej\AppData\Roaming\npm\node_modules\openclaw\skills\clawdbot-supermemory`
   - Status: ✅ Installerad
   - Beskrivning: Supermemory integration för Clawdbot

### Från ClawHub:
3. **prompt-guard** (seojoonkim/prompt-guard) v2.6.1
   - Plats: `C:\Users\Hejhej\.openclaw\workspace\skills\prompt-guard`
   - Status: ✅ Klar att använda
   - Beskrivning: Advanced prompt injection defense system med HiveFence network integration
   - Funktioner:
     - Skydd mot direct/indirect injection attacks
     - Multi-language detection (EN/KO/JA/ZH)
     - Severity scoring
     - Automatic logging
     - Configurable security policies

4. **find-skills** (JimLiuxinghai/find-skills)
   - Plats: `C:\Users\Hejhej\.openclaw\workspace\skills\find-skills`
   - Status: ✅ Klar att använda
   - Beskrivning: Hjälper användare att upptäcka och installera agent skills
   - Användning: När användaren frågar "how do I do X", "find a skill for X", etc.

5. **dont-hack-me** (peterokase42/dont-hack-me)
   - Plats: `C:\Users\Hejhej\.openclaw\workspace\skills\dont-hack-me`
   - Status: ✅ Klar att använda
   - Beskrivning: Security self-check för Clawdbot/Moltbot
   - Funktioner:
     - Audit av clawdbot.json
     - Upptäcker dangerous misconfigurations
     - Exposed gateway, missing auth, open DM policy, weak tokens, loose file permissions
     - Auto-fix included
   - Kommandon: "run a security check" eller "幫我做安全檢查"

---

## 🔧 Verifiering

Kör följande för att verifiera installationerna:
```bash
openclaw skills list
openclaw skills check
```

Alla 5 skills visas nu i listan över tillgängliga skills.

---

## 📝 Noteringar

- ClawHub-skills installerades via `npx clawhub install [skill-name]`
- GitHub-skills klonades direkt till skills-katalogen
- OpenClaw upptäcker automatiskt skills från båda platserna
- Skills är redo att användas omedelbart
