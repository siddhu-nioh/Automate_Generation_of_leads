import time
from scraper import scrape_crunchbase
from enrichment import enrich_data
from database import save_to_db

def continuous_scraping():
    while True:
        scraped_data = scrape_crunchbase()
        if scraped_data:
            enriched_data = enrich_data(scraped_data)
            save_to_db(enriched_data)
            print(f"Scraped and saved {len(enriched_data)} leads.")
        else:
            print("No new data found.")
        time.sleep(3600)  

if __name__ == "__main__":
    continuous_scraping()
