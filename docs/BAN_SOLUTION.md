# 🚫 Ban da PVP.giustizia.it - Soluzioni

## ⚠️ Stato Attuale

Sei stato bannato dal sito **pvp.giustizia.it** per eccesso di richieste.

**Evidenze:**
- Il sito non risponde alle richieste (timeout/connessione bloccata)
- Logs mostrano errori ripetuti: `api_fetch_failed`
- Troppe richieste consecutive hanno attivato protezioni anti-bot

## ✅ Ho Già Implementato

### 1. **Strategie Anti-Ban nello Scraper**
- ✅ Delay aumentato da 1s a **8-15 secondi** (randomizzato)
- ✅ Rate limit ridotto a **6 richieste/minuto** (max 1 ogni 10 sec)
- ✅ Rotazione User-Agent (12 diversi browser)
- ✅ Headers realistici (Accept-Language, DNT, Sec-Fetch-*)
- ✅ Exponential backoff dopo errori (60s → 120s → 240s)
- ✅ Limite di 3 pagine per sessione (invece di 100)
- ✅ Stop immediato su 403/429 HTTP status
- ✅ Logging dettagliato per monitoring

### 2. **Scraper Fermato**
```bash
docker-compose stop scraper  # ✅ Già eseguito
```

## 🔧 Soluzioni Immediate

### Opzione A: **Aspettare (CONSIGLIATO)**
Il ban potrebbe essere temporaneo (24-48 ore).

**Cosa fare:**
1. ⏰ **Aspetta 24 ore** senza fare richieste
2. 🧪 **Testa l'accesso** con lo script:
   ```bash
   python3 scripts/test_pvp_access.py
   ```
3. ✅ **Se torna accessibile**, riavvia lo scraper:
   ```bash
   docker-compose start scraper
   ```

**Pro:**
- Gratis
- Nessuna configurazione aggiuntiva
- Il nuovo scraper ha già protezioni anti-ban

**Contro:**
- Devi aspettare 1-2 giorni

---

### Opzione B: **Usare una VPN**
Cambia il tuo indirizzo IP pubblico.

**Servizi VPN consigliati:**
- [NordVPN](https://nordvpn.com) (~€3/mese)
- [ProtonVPN](https://protonvpn.com) (piano gratuito disponibile)
- [Mullvad](https://mullvad.net) (€5/mese)

**Procedura:**
1. 🌐 Installa e attiva VPN
2. 🔄 Cambia server (preferibilmente Italia)
3. 🧪 Testa accesso:
   ```bash
   python3 scripts/test_pvp_access.py
   ```
4. ✅ Se accessibile, riavvia scraper

**Pro:**
- Soluzione rapida (funziona subito)
- Utile anche per privacy

**Contro:**
- Costa €3-5/mese
- Potrebbe rallentare connessione

---

### Opzione C: **Proxy Rotativi** (per uso professionale)
Usa servizi con pool di IP che ruotano automaticamente.

**Servizi consigliati:**
- [ScraperAPI](https://www.scraperapi.com) (~$49/mese)
- [Bright Data](https://brightdata.com) (da $500/mese)
- [Smartproxy](https://smartproxy.com) (~$75/mese)

**Pro:**
- IP sempre diversi
- Gestione automatica CAPTCHA
- Alta affidabilità

**Contro:**
- Costoso ($50-500/mese)
- Richiede integrazione nel codice

---

### Opzione D: **Ridurre Frequenza Scraping**
Invece di scraping continuo, fai run manuali poco frequenti.

**Configurazione:**
1. 📝 Modifica `docker-compose.yml`:
   ```yaml
   scraper:
     # Rimuovi "restart: unless-stopped"
     # Aggiungi:
     profiles: ["manual"]
   ```

2. 🕐 **Run manuale** una volta al giorno:
   ```bash
   # Ogni 24 ore
   docker-compose run --rm scraper
   ```

**Pro:**
- Evita ban futuri
- Controllo totale

**Contro:**
- Dati meno aggiornati
- Richiede scheduling manuale

---

### Opzione E: **Usare Solo Dati Mock**
Lavora con i 94 dati mock già importati.

**Vantaggi:**
- ✅ Hai già 94 aste con dati realistici
- ✅ Backend funzionante
- ✅ Frontend testabile
- ✅ Zero rischio ban

**Quando è sufficiente:**
- Sviluppo e test
- Demo per clienti
- Prototipo MVP

---

## 🔮 Soluzione Futura: API Ufficiale

Verifica se **pvp.giustizia.it** offre:
- API pubblica ufficiale
- Dataset open data
- Feed RSS

**Come verificare:**
```bash
# Cerca robots.txt
curl https://pvp.giustizia.it/robots.txt

# Cerca sitemap
curl https://pvp.giustizia.it/sitemap.xml
```

## 📊 Configurazione Attuale

Ho già modificato questi file:

### `scraper/src/config.py`
```python
SCRAPER_DELAY_MS: int = 8000          # 8 secondi base
SCRAPER_MIN_DELAY_MS: int = 5000      # Min 5 secondi
SCRAPER_MAX_DELAY_MS: int = 15000     # Max 15 secondi
SCRAPER_MAX_PAGES_PER_RUN: int = 5    # Solo 5 pagine per run
SCRAPER_PAUSE_AFTER_ERROR: int = 60   # 60s di pausa dopo errore
```

### `scraper/src/user_agents.py`
- 12 User-Agent diversi (Chrome, Firefox, Safari, Edge)
- Headers realistici con DNT, Sec-Fetch-*, Accept-Language

### `scraper/src/pvp_scraper.py`
- Delay randomizzato (5-15 sec)
- Stop immediato su 403/429
- Logging ban detection
- Max 3 pagine per sessione

## 🧪 Test Script

Usa questo script per verificare lo stato del ban:

```bash
python3 scripts/test_pvp_access.py
```

**Output possibili:**
- ✅ `SUCCESS! Found X auctions` → Ban rimosso
- ❌ `403 FORBIDDEN` → Ancora bannato
- ❌ `429 TOO MANY REQUESTS` → Rate limit attivo
- ⏱️ `TIMEOUT` → IP bloccato

## 📝 Raccomandazioni

### Per Sviluppo (ORA)
1. ⏸️ **Mantieni scraper fermo** (già fatto)
2. 💾 **Usa i 94 dati mock** per sviluppo
3. 🎨 **Completa frontend** (MapView, AuctionDetail)
4. 🧪 **Testa con dati esistenti**

### Per Produzione (FUTURO)
1. ⏰ **Aspetta 24h** per far scadere ban
2. 🧪 **Testa accesso** con script
3. 🌐 **Se ancora bannato**, considera VPN
4. 🚀 **Riavvia scraper** con nuove protezioni
5. 📊 **Monitora logs**: `docker-compose logs -f scraper`

### Se Ban Persiste (>48h)
- Considera VPN professionale
- Valuta proxy rotativi
- Cerca fonti dati alternative
- Contatta pvp.giustizia.it per accesso API ufficiale

## 🆘 Comandi Utili

```bash
# Test accesso PVP
python3 scripts/test_pvp_access.py

# Verifica stato scraper
docker-compose ps scraper

# Avvia scraper (solo se test positivo)
docker-compose start scraper

# Logs in tempo reale
docker-compose logs -f scraper

# Ferma scraper
docker-compose stop scraper

# Verifica IP pubblico
curl ifconfig.me
```

## 📞 Supporto

Se hai domande o hai bisogno di implementare una delle soluzioni, fammi sapere!

**Prossimi passi consigliati:**
1. Aspettare 24h
2. Testare accesso
3. Se necessario, configurare VPN
4. Riavviare scraper con nuove protezioni
