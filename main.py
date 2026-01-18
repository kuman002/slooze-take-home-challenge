import asyncio
from scraper.config import CATEGORIES
from scraper.indiamart_scraper import scrape_category
from etl.clean_data import run_etl
from eda.eda_report import run_eda

async def main():
    raw_files = []
    for category, url in CATEGORIES.items():
        out = await scrape_category(category, url)
        raw_files.append(out)

    cleaned_csv = run_etl(raw_files)
    run_eda(cleaned_csv)

if __name__ == "__main__":
    asyncio.run(main())
