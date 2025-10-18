#!/usr/bin/env python3
"""
Script per testare se l'accesso a PVP è ancora bloccato.
Esegui questo script per verificare lo stato del ban.
"""
import requests
import time
import random

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
]

def test_pvp_access():
    """Test se il sito PVP è accessibile."""
    base_url = "https://pvp.giustizia.it"
    api_url = f"{base_url}/ric-496b258c-986a1b71/ric-ms/ricerca/vendite"
    
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
        "Content-Type": "application/json",
        "Origin": base_url,
        "Referer": f"{base_url}/pvp/it/lista_annunci.page",
        "DNT": "1",
    }
    
    payload = {
        "tipoLotto": "IMMOBILI",
        "categoriaBene": [],
        "flagRicerca": 0,
        "coordIndirizzo": "",
        "raggioIndirizzo": "25"
    }
    
    url = f"{api_url}?language=it&page=0&size=1&sort=dataOraVendita,asc&sort=citta,asc"
    
    print("🔍 Testing access to pvp.giustizia.it...")
    print(f"📍 URL: {url}")
    print(f"🎭 User-Agent: {headers['User-Agent'][:60]}...")
    print()
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        print(f"✅ Status Code: {response.status_code}")
        print(f"📦 Response Size: {len(response.content)} bytes")
        
        if response.status_code == 200:
            try:
                data = response.json()
                total = data.get('body', {}).get('totalElements', 0)
                print(f"🎯 SUCCESS! Found {total} total auctions")
                print("✨ Il sito è accessibile. Il ban potrebbe essere stato rimosso.")
                return True
            except Exception as e:
                print(f"⚠️  Response is 200 but can't parse JSON: {e}")
                return False
        
        elif response.status_code == 403:
            print("❌ 403 FORBIDDEN - Sei ancora bannato!")
            print("⏰ Aspetta almeno 1-2 ore prima di riprovare")
            print("💡 Suggerimenti:")
            print("   - Usa una VPN per cambiare IP")
            print("   - Aspetta 24 ore per far scadere il ban")
            print("   - Considera di usare proxy rotativi")
            return False
        
        elif response.status_code == 429:
            print("❌ 429 TOO MANY REQUESTS - Rate limit attivo")
            print("⏰ Aspetta almeno 30-60 minuti")
            return False
        
        elif response.status_code >= 500:
            print(f"⚠️  {response.status_code} SERVER ERROR - Il sito ha problemi")
            print("🔄 Riprova tra qualche minuto")
            return False
        
        else:
            print(f"⚠️  Unexpected status code: {response.status_code}")
            print(f"📄 Response: {response.text[:200]}")
            return False
    
    except requests.exceptions.Timeout:
        print("⏱️  TIMEOUT - Il server non risponde")
        print("🔄 Riprova tra qualche minuto")
        return False
    
    except requests.exceptions.ConnectionError:
        print("🔌 CONNECTION ERROR - Impossibile connettersi")
        print("🌐 Verifica la tua connessione internet")
        return False
    
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("=" * 70)
    print("🔍 PVP Access Test Script")
    print("=" * 70)
    print()
    
    success = test_pvp_access()
    
    print()
    print("=" * 70)
    
    if success:
        print("✅ Puoi riavviare lo scraper con: docker-compose start scraper")
    else:
        print("⏸️  Mantieni lo scraper fermo per ora")
        print("🔄 Riesegui questo script tra 1-2 ore per verificare")
        print()
        print("Comando: python3 scripts/test_pvp_access.py")
    
    print("=" * 70)
