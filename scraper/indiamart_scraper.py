import asyncio
import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

from scraper.config import OUTPUT_DIR, MAX_PAGES, REQUEST_DELAY, TIMEOUT
from scraper.utils import save_json, timestamp


# ---------------------------
# Helpers
# ---------------------------
def clean_text(x):
    if not x:
        return None
    return re.sub(r"\s+", " ", x).strip()


def extract_detail_fast(url: str):
    """
    FAST enrichment using Requests + BeautifulSoup.
    Much faster than Playwright for product detail pages.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
    }

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code != 200:
            return {"price": None, "supplier": None, "location": None}

        soup = BeautifulSoup(r.text, "lxml")
        text = soup.get_text(" ", strip=True)

        # ✅ Price extraction (₹)
        price = None
        m = re.search(r"(₹\s?\d[\d,]*)", text)
        if m:
            price = m.group(1)

        # ✅ Supplier extraction (fallback using meta tags / title)
        supplier = None
        og_title = soup.find("meta", {"property": "og:title"})
        if og_title and og_title.get("content"):
            supplier = og_title["content"]

        # ✅ Location extraction (state match)
        location = None
        m = re.search(
            r"(Tamil Nadu|Kerala|Karnataka|Maharashtra|Delhi|Gujarat|Telangana|Andhra Pradesh|West Bengal|Uttar Pradesh|Rajasthan|Punjab|Haryana)",
            text
        )
        if m:
            location = m.group(1)

        return {"price": price, "supplier": supplier, "location": location}

    except Exception:
        return {"price": None, "supplier": None, "location": None}


# ---------------------------
# Main scraper
# ---------------------------
async def scrape_category(category_name: str, url: str):
    results = []
    all_items = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        await page.set_extra_http_headers({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        })

        # ✅ Step 1: Listing scrape (FAST)
        for page_no in range(1, MAX_PAGES + 1):
            target_url = url + f"?page={page_no}"
            print(f"\n[{category_name}] Listing page {page_no}: {target_url}")

            try:
                await page.goto(target_url, timeout=TIMEOUT, wait_until="domcontentloaded")
                await page.wait_for_timeout(1500)

                # scroll to load more listings
                for _ in range(3):
                    await page.mouse.wheel(0, 1500)
                    await page.wait_for_timeout(400)

                links = page.locator("a.titles, a[href*='/proddetail/']")
                count = await links.count()
                print(f"✅ Links found: {count}")

                N = min(20, count)  # take 20 per page
                for i in range(N):
                    link = links.nth(i)
                    name = clean_text(await link.inner_text())
                    href = await link.get_attribute("href")

                    if not name or not href:
                        continue

                    full_url = href if href.startswith("http") else urljoin("https://www.indiamart.com", href)

                    all_items.append({
                        "category": category_name,
                        "product_name": name,
                        "product_url": full_url,
                        "price": None,
                        "supplier": None,
                        "location": None
                    })

                await asyncio.sleep(REQUEST_DELAY)

            except Exception as e:
                print(f"[WARN] Listing page failed: {e}")
                continue

        await browser.close()

    print(f"✅ Total listing items collected for {category_name}: {len(all_items)}")

    # ✅ Step 2: Enrich all collected items
    enrich_limit = len(all_items)

    for idx in range(enrich_limit):
        item = all_items[idx]
        print(f"⚡ Fast enriching {idx+1}/{enrich_limit}: {item['product_name']}")

        detail_data = extract_detail_fast(item["product_url"])
        item.update(detail_data)

        results.append(item)

    out_file = f"{OUTPUT_DIR}/{category_name}_{timestamp()}.json"
    save_json(results, out_file)
    print(f"\n[DONE] Saved {len(results)} records → {out_file}")
    return out_file
