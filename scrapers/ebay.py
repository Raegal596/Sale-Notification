import requests
from bs4 import BeautifulSoup

def scrape_ebay(query: str, region: str) -> list[dict]:
    """
    Scrapes eBay for a given query.
    Note: Region is generally not as directly implemented in generic eBay search URLs 
    without postal codes, so it performs a national/international query by default depending 
    on the ebay domain used (.ca or .com).
    """
    results = []
    
    # Generic search URL for eBay Canada as base
    url = "https://www.ebay.ca/sch/i.html"
    params = {
        "_nkw": query,
    }
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching eBay: {e}")
        return results

    soup = BeautifulSoup(response.content, 'html.parser')
    
    items = soup.select('.s-item')
    for item in items:
        title_elem = item.select_one('.s-item__title')
        price_elem = item.select_one('.s-item__price')
        link_elem = item.select_one('.s-item__link')
        
        if not title_elem or not link_elem:
            continue
            
        title = title_elem.text.strip()
        # eBay often has a dummy first item, we ignore it
        if title == "Shop on eBay" or "Shop on eBay" in title:
            continue
            
        price = price_elem.text.strip() if price_elem else "N/A"
        link = link_elem.get('href')
        
        # eBay URLs are long and have tracking info. We can use the item number from the URL or the whole URL as ID.
        # usually eBay item URLs contain the ID like /itm/1234567890
        item_id = link.split('?')[0].split('/')[-1] if link else str(hash(title))
        
        results.append({
            'title': title,
            'price': price,
            'url': link,
            'id': item_id,
            'source': 'ebay'
        })
    
    return results

if __name__ == "__main__":
    # Test the eBay scraper
    test_results = scrape_ebay("macbook", "toronto")
    print(f"Found {len(test_results)} results:")
    for res in test_results[:3]:
        print(f" - {res['title']} ({res['price']}): {res['url']}")
