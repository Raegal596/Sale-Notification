import requests
from bs4 import BeautifulSoup
import re

def scrape_craigslist(query: str, region: str) -> list[dict]:
    """
    Scrapes Craigslist for a given query and region.
    Craigslist uses subdomains for regions, e.g., toronto.craigslist.org
    """
    results = []
    
    # Simple formatting of region for craigslist subdomain (this might need to be refined based on user inputs)
    region_subdomain = region.lower().replace(" ", "")
    
    # Craigslist JSON search API URL
    url = "https://sapi.craigslist.org/web/v8/postings/search/full"
    
    params = {
        "batch": "25-0-360-6-0",
        "query": query,
        "searchPath": "sss",
        "sort": "rel",
        "lang": "en",
        "cc": "us"
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Origin': f'https://{region_subdomain}.craigslist.org',
        'Referer': f'https://{region_subdomain}.craigslist.org/'
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Craigslist: {e}")
        return results
    except ValueError:
        print("Error parsing Craigslist JSON response")
        return results

    decode = data.get('data', {}).get('decode', {})
    min_posting_id = decode.get('minPostingId', 0)
    items = data.get('data', {}).get('items', [])
    
    for item in items:
        # Some items might be cluster markers or other non-listing data
        if not isinstance(item, list) or len(item) < 3:
             continue
             
        try:
            # The structure is an array with various items.
            # Usually:
            # item[0]: ID offset, such that absolute ID = minPostingId + item[0]
            # item[-1]: Title (string)
            # Find the price which is typically a string starting with '$' located in a nested list
            
            title = item[-1]
            if not isinstance(title, str):
                continue

            item_id = str(min_posting_id + item[0])
            price = "N/A"
            for x in item:
                if isinstance(x, list) and len(x) > 1 and isinstance(x[1], str) and x[1].startswith('$'):
                    price = x[1]
                    break

            link = f"https://{region_subdomain}.craigslist.org/search/sss?query={query}#search=1~gallery~0~{item[0]}" 

            results.append({
                'title': title,
                'price': price,
                'url': link,
                'id': item_id,
                'source': 'craigslist'
            })
        except Exception as e:
            print(f"Skipping an item due to parsing error: {e}")
            continue
        
    return results

if __name__ == "__main__":
    # Test the scraper
    test_results = scrape_craigslist("macbook", "toronto")
    print(f"Found {len(test_results)} results:")
    for res in test_results[:3]:
        print(f" - {res['title']} ({res['price']}): {res['url']}")
