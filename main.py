import os
import json
import time
import schedule
from scrapers.craigslist import scrape_craigslist
from scrapers.kijiji import scrape_kijiji
from scrapers.facebook import scrape_facebook
from notifier import send_bulk_sms_notification

def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config.json: {e}")
        return {}

config = load_config()

SEEN_LISTINGS_FILE = "seen_listings.json"

def load_seen_listings() -> set:
    if os.path.exists(SEEN_LISTINGS_FILE):
        try:
            with open(SEEN_LISTINGS_FILE, "r") as f:
                return set(json.load(f))
        except (json.JSONDecodeError, ValueError):
            return set()
    return set()

def save_seen_listings(seen_listings: set):
    with open(SEEN_LISTINGS_FILE, "w") as f:
        json.dump(list(seen_listings), f)

def run_scrapers():
    search_query = config.get('SEARCH_QUERY', '')
    region = config.get('REGION', '')
    print(f"Starting job. Query: {search_query}, Region: {region}")
    seen_listings = load_seen_listings()
    new_listings = []
    
    # 1. Craigslist
    try:
        print("Scraping Craigslist...")
        cl_results = scrape_craigslist(search_query, region)
        new_listings.extend(process_results(cl_results, seen_listings))
    except Exception as e:
        print(f"Error executing Craigslist scraper: {e}")
        
    # 2. Kijiji
    try:
        print("Scraping Kijiji...")
        kj_results = scrape_kijiji(search_query, region)
        new_listings.extend(process_results(kj_results, seen_listings))
    except Exception as e:
        print(f"Error executing Kijiji scraper: {e}")
        
    # 3. Facebook
    try:
        print("Scraping Facebook Marketplace...")
        fb_results = scrape_facebook(search_query, region)
        new_listings.extend(process_results(fb_results, seen_listings))
    except Exception as e:
        print(f"Error executing Facebook scraper: {e}")
        
    if new_listings:
        print(f"Found {len(new_listings)} new listings in total. Sending bulk SMS...")
        send_bulk_sms_notification(new_listings)
        
    save_seen_listings(seen_listings)
    print("Job completed. Waiting for next interval...")

def process_results(results: list[dict], seen_listings: set) -> list[dict]:
    new_items = []
    for result in results:
        # Use item ID as unique identifier, fallback to URL
        item_id = str(result.get('id', result['url']))
        if item_id not in seen_listings:
            print(f"Found new listing: {result['title']}")
            new_items.append(result)
            seen_listings.add(item_id)
    return new_items

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-once", action="store_true", help="Run scrapers once and exit")
    args = parser.parse_args()

    if args.run_once:
        run_scrapers()
    else:
        # Initial run
        run_scrapers()
        
        # Schedule the job to run every 30 minutes
        schedule.every(30).minutes.do(run_scrapers)
        
        print("Scheduler started. Running every 30 minutes.")
        while True:
            schedule.run_pending()
            time.sleep(60)
