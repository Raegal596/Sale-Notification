import os
import json
import time
import schedule
from scrapers.craigslist import scrape_craigslist
from scrapers.kijiji import scrape_kijiji
from scrapers.facebook import scrape_facebook
from scrapers.ebay import scrape_ebay
from notifier import send_notifications

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
    search_queries = config.get('SEARCH_QUERIES', [])
    # Fallback to single SEARCH_QUERY if it exists for backwards compatibility
    if 'SEARCH_QUERY' in config and config['SEARCH_QUERY'] not in search_queries:
        search_queries.append({
            "query": config['SEARCH_QUERY'],
            "region": config.get('REGION', ''),
            "to_phone_number": config.get('TO_PHONE_NUMBER', '')
        })
        
    seen_listings = load_seen_listings()
    listings_by_phone = {}
    
    for query_item in search_queries:
        if isinstance(query_item, str):
            search_query = query_item
            region = config.get('REGION', '')
            to_phone_number = config.get('TO_PHONE_NUMBER', '')
        else:
            search_query = query_item.get("query", "")
            region = query_item.get("region", config.get('REGION', ''))
            to_phone_number = query_item.get("to_phone_number", config.get('TO_PHONE_NUMBER'))
            
        if not search_query:
            continue
            
        print(f"Starting job. Query: {search_query}, Region: {region}")
        query_new_listings = []
        
        # 1. Craigslist
        try:
            print(f"Scraping Craigslist for '{search_query}'...")
            cl_results = scrape_craigslist(search_query, region)
            query_new_listings.extend(process_results(cl_results, seen_listings))
        except Exception as e:
            print(f"Error executing Craigslist scraper: {e}")
            
        # 2. Kijiji
        try:
            print(f"Scraping Kijiji for '{search_query}'...")
            kj_results = scrape_kijiji(search_query, region)
            query_new_listings.extend(process_results(kj_results, seen_listings))
        except Exception as e:
            print(f"Error executing Kijiji scraper: {e}")
            
        # 3. Facebook
        try:
            print(f"Scraping Facebook Marketplace for '{search_query}'...")
            fb_results = scrape_facebook(search_query, region)
            query_new_listings.extend(process_results(fb_results, seen_listings))
        except Exception as e:
            print(f"Error executing Facebook scraper: {e}")
            
        # 4. eBay
        try:
            print(f"Scraping eBay for '{search_query}'...")
            ebay_results = scrape_ebay(search_query, region)
            query_new_listings.extend(process_results(ebay_results, seen_listings))
        except Exception as e:
            print(f"Error executing eBay scraper: {e}")
            
        if query_new_listings:
            if to_phone_number not in listings_by_phone:
                listings_by_phone[to_phone_number] = []
            listings_by_phone[to_phone_number].extend(query_new_listings)
            
    for phone_number, listings in listings_by_phone.items():
        if listings:
            print(f"Found {len(listings)} new listings for phone {phone_number}. Sending notifications...")
            send_notifications(listings, to_phone_number=phone_number)
            
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
