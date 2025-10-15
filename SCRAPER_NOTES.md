# Scraper Implementation Notes

## Current Status

✅ **Scraper service is running successfully**
✅ **URL format updated to correct endpoint**
⚠️ **Website uses JavaScript rendering - requires headless browser**

## Website Structure

The Italian auction portal (pvp.giustizia.it) uses a **React-based Single Page Application (SPA)** that loads data dynamically via JavaScript. This means:

- HTML returned is just a shell with JavaScript bundles
- Actual auction data is loaded asynchronously via API calls
- Traditional HTML scraping (BeautifulSoup) won't work

## Current URL

```
https://pvp.giustizia.it/pvp/it/lista_annunci.page?searchType=searchForm&page=0&size=12&sortProperty=dataOraVendita,asc&sortAlpha=citta,asc&searchWith=Raggio%20d%27azione&codTipoLotto=IMMOBILI&raggioAzione=25
```

## Solution Options

### Option 1: Headless Browser (Recommended)
Use Playwright or Selenium to render JavaScript and extract data.

**Pros:**
- Can scrape any modern website
- Handles JavaScript rendering
- Can interact with dynamic content

**Cons:**
- Higher resource usage
- Slower scraping
- More complex setup

**Implementation:**
```python
# Add to requirements.txt
playwright==1.40.0

# Update scraper to use Playwright
from playwright.async_api import async_playwright

async def scrape_with_browser(url: str):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url)
        await page.wait_for_selector('.auction-card')  # Wait for content
        content = await page.content()
        await browser.close()
        return content
```

### Option 2: Reverse Engineer API
Find the actual JSON API endpoint the React app uses.

**Pros:**
- Fast and efficient
- Low resource usage
- Clean JSON data

**Cons:**
- Requires browser DevTools investigation
- API might be protected
- May change without notice

**Steps:**
1. Open https://pvp.giustizia.it in browser
2. Open DevTools → Network tab
3. Filter by XHR/Fetch
4. Search for auctions
5. Find API endpoint in network requests

### Option 3: Sample Data Generator (Current Temporary Solution)
Use the existing sample data generator for development/testing.

```bash
docker-compose exec backend python scripts/sample_data.py 50
```

This creates realistic test data without scraping.

## Next Steps

1. **For Development/Testing**: Use sample data generator
2. **For Production**: 
   - Option A: Add Playwright to scraper service
   - Option B: Investigate browser DevTools to find JSON API
   - Option C: Contact website administrators for API access

## Scraper Service Status

The scraper is currently running and will attempt to scrape every cycle, but returns 0 auctions due to JavaScript rendering. The service is healthy and ready for implementation of one of the above solutions.

**Logs show:**
```
scraped_auction_list count=0 page=0
scraped_auction_list count=0 page=1
...
scraping_completed total_auctions=0
```

This is expected behavior - the HTML is being fetched successfully, but contains no auction data (loaded by JS).
