# HEARTBEAT.md - TRADING BOT EDITION
## Autonomous Crypto Trading Workflows

---

## 🎯 NYTT MÅL: Trading Bot - "Micro-Scalp"
**Strategi:** Små, frekventa vinster med strikt riskhantering
**Mål:** 0.5-2% vinst per trade, 15-30% månadsavkastning
**Risk:** Minimal (max 2% per trade, max 5% daglig förlust)
**Marknad:** Bitcoin, Ethereum, Solana (spot trading)

---

## ⏰ TRADING BOT WORKFLOWS

### T :00 - Price Monitor & Signal Check
**När:** Varje minut
**Fil:** `projects/trading-bot/micro_scalp_bot.py`

**Att göra:**
1. [ ] Hämta realtidspriser från Binance API
2. [ ] Beräkna tekniska indikatorer (SMA, EMA, volym)
3. [ ] Generera trading-signaler
4. [ ] Kontrollera öppna trades (stop-loss/take-profit)
5. [ ] Öppna nya trades om signal & risk-gränser tillåter
6. [ ] Logga alla aktiviteter

**Output:** 
- Uppdatera `trading_bot.log`
- Spara trades i `paper_trades.db`
- Skriv statistik till `daily_trading_report.json`

---

### Var 5:e minut - Performance Check
**Att göra:**
1. [ ] Beräkna win-rate, P&L, drawdown
2. [ ] Kontrollera om daglig förlustgräns nådd
3. [ ] Om daglig förlust >5% → STOPPA trading för dagen
4. [ ] Uppdatera dashboard/statistik

**Output:**
- Statusrapport i loggen
- Eventuell STOP-alert om gränser nåtts

---

### Varje timme - Codex Optimization (Automatisk)
**Att göra:**
1. [ ] Låt Codex analysera trading_bot.log performance
2. [ ] Förbättra signalgenerering med nya indikatorer
3. [ ] Testa förbättringar i paper mode
4. [ ] Commita ändringar till GitHub

**Output:** Förbättrad bot-varje timme

---

### Dagligen kl 06:00 - Strategy Backtest
**Att göra:**
1. [ ] Ladda historisk data för BTC, ETH, SOL
2. [ ] Kör backtest på senaste 30 dagarna
3. [ ] Beräkna teoretisk avkastning, win-rate, drawdown
4. [ ] Generera backtest-rapport
5. [ ] Föreslå strategi-förbättringar

---
**Att göra:**
1. [ ] Utvärdera riskhantering
2. [ ] Kontrollera position sizes
3. [ ] Säkerställ stop-lossar fungerar
4. [ ] Om problem → ALERT

---

### Dagligen kl 08:00 - Morning Trading Brief
**Att göra:**
1. [ ] Ladda gårdagens tradingdata
2. [ ] Beräkna daglig avkastning
3. [ ] Identifiera mönster/förbättringsområden
4. [ ] Justera strategi-parametrar om nödvändigt
5. [ ] Skapa daglig rapport

**Output:** `reports/daily_trading_summary_YYYY-MM-DD.md`

---

### Dagligen kl 20:00 - Evening Trading Report
**Att göra:**
1. [ ] Sammanställ dagens trades
2. [ ] Beräkna total P&L
3. [ ] Uppdatera monthly stats
4. [ ] Commit all trading data till GitHub
5. [ ] Förbered imorgon-analys

**Output:** Commit till GitHub med dagens tradingdata

---

### Veckovis (Söndagar) - Strategy Review
**Att göra:**
1. [ ] Analysera veckans performance
2. [ ] Jämför med föregående vecka
3. [ ] Identifiera vinnande/förlorande mönster
4. [ ] Justera strategi om nödvändigt
5. [ ] Skapa veckorapport

---

## 🤖 AUTONOMA REGLER FÖR TRADING

### Jag får agera UTAN godkännande:
✅ PAPER TRADING - Simulera trades med fejk-pengar
✅ Övervaka marknader och generera signaler
✅ Hantera stop-loss och take-profit automatiskt
✅ Logga all aktivitet
✅ Riskhantering (stoppa vid gränsöverskridande)
✅ Generera rapporter och analyser

### Jag MÅSTE vänta på godkännande vid:
❌ SWITCH till LIVE TRADING (riktiga pengar)
❌ Ändra risk-parametrar
❌ Lägg till/ta bort trading-symbols
❌ Justera stop-loss/take-procent över 2%
❌ Överföra riktiga pengar till trading-konto

---

## 📊 TRADING BOT STATUS

### Pågående Faser:
**FAZ 1: PAPER TRADING** (Nuvarande - 1-2 veckor)
- Simulerade trades
- Validera strategi
- Mål: Bevisad win-rate >50%

**FAZ 2: MICRO LIVE** (Efter FAZ 1 - 1-2 veckor)
- $50-100 riktiga pengar
- Sma trades, tight risk
- Mål: Konsistent daglig vinst

**FAZ 3: SCALE UP** (Efter FAZ 2)
- Öka kapital gradvis
- Mål: $150-300/månad vinst

---

## 🚨 KRITISKA ALERTS (Informerar omedelbart)

**STOPPA ALLT OM:**
1. Daglig förlust >5%
2. 3 förlorande trades i rad
3. Tekniskt fel i bot
4. Misstänkt marknadsbeteende (pump & dump)

---

## 📈 SUCCESS METRICS

| Mått | Mål | Nuvarande |
|------|-----|-----------|
| Win-rate | >55% | TBD |
| Avg. profit/trade | 0.5-2% | TBD |
| Max. drawdown | <10% | TBD |
| Daily trades | 5-10 | TBD |
| Monthly return | 15-30% | TBD |

---

## 🔄 INTEGRATION MED ANDRA SYSTEM

### Git Sync:
- Auto-commit trading logs varje timme
- Backup av trade-databas dagligen

### Notifications (Framtida):
- Discord alert vid viktiga händelser
- Daily summary till Christian

### Memory:
- Logga trading-insikter i MEMORY.md
- Uppdatera strategi baserat på resultat

---

*Trading Bot Autonomous Mode: ENABLED*
*Paper Trading: ACTIVE*
*Risk Management: STRICT*

**BOT ÄR LIVE OCH HANDLAR (PAPER MODE)** 🚀
