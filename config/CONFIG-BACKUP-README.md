# 🔧 OpenClaw Config Backup

## 📍 Var finns backup?

**Fullständig backup (med API-nycklar):**
```
C:\Users\Hejhej\.openclaw\backups\openclaw-backup-2026-02-04.json
```

**Denna mall (utan API-nycklar):**
```
config/openclaw-config-TEMPLATE.json
```

---

## 🚨 VIKTIGT: Säkerhet

**API-nycklar ska ALDRIG commitas till Git!**

| Fil | Innehåller API-nycklar? | Var? |
|-----|------------------------|------|
| `openclaw-backup-*.json` | ✅ Ja | Lokal backup (~/.openclaw/backups/) |
| `openclaw-config-TEMPLATE.json` | ❌ Nej | Git-repo (mall) |

---

## 🔄 Återställa från backup

**Om config går förlorad:**

1. Kopiera från backup:
   ```powershell
   copy C:\Users\Hejhej\.openclaw\backups\openclaw-backup-2026-02-04.json C:\Users\Hejhej\.openclaw\openclaw.json
   ```

2. Starta om gateway:
   ```powershell
   openclaw gateway restart
   ```

---

## 📝 API-nycklar som behövs

| Tjänst | Nyckeltyp | Kostnad |
|--------|-----------|---------|
| **NVIDIA** | Gratis | $0 |
| **OpenAI** | Betald | Per användning |
| **Brave Search** | Gratis (till 2000/år) | $0 |
| **Telegram** | Gratis | $0 |

---

## 🆘 Om allt försvinner

1. **Återställ config** från backup
2. **Verifiera att nycklar fungerar:**
   ```powershell
   openclaw doctor
   ```
3. **Testa varje modell:**
   ```powershell
   openclaw status
   ```

---

Senast uppdaterad: 2026-02-04
