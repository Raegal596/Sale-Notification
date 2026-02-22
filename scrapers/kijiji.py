import requests
from bs4 import BeautifulSoup

def scrape_kijiji(query: str, region: str) -> list[dict]:
    """
    Scrapes Kijiji for a given query.
    Note: Kijiji handles regions with specific location IDs or path segments.
    For simplicity, we'll use the generic search endpoint with query params, 
    but this may need a location ID mapped from the region string in a production app.
    """
    results = []
    
    # Generic search URL for Kijiji Canada
    url = "https://www.kijiji.ca/b-search.html"
    params = {
        "categoryId": "0",  # 0 means all categories
        "formSubmit": "true",
        "keywords": query,
    }
    
    # Normally locationId is needed, e.g., locationId=1700272 (GTA)
    if "toronto" in region.lower() or "gta" in region.lower():
        params["locationId"] = "1700272"
    elif "vancouver" in region.lower():
         params["locationId"] = "1700287"
         
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching Kijiji: {e}")
        return results

    soup = BeautifulSoup(response.content, 'html.parser')
    
    cards = soup.find_all(attrs={'data-testid': 'listing-card'})
    for card in cards:
        title_elem = card.find(attrs={'data-testid': 'listing-title'})
        price_elem = card.find(attrs={'data-testid': 'listing-price'})
        link_elem = card.find(attrs={'data-testid': 'listing-link'})
        
        if not title_elem or not link_elem:
            continue
            
        title = title_elem.text.strip()
        price = price_elem.text.strip() if price_elem else "N/A"
        link = link_elem.get('href')
        
        if link and link.startswith('/'):
            link = f"https://www.kijiji.ca{link}"
            
        item_id = card.get('data-listingid', link)
        
        results.append({
            'title': title,
            'price': price,
            'url': link,
            'id': item_id,
            'source': 'kijiji'
        })
    
    return results

if __name__ == "__main__":
    # Test the Kijiji scraper
    test_results = scrape_kijiji("macbook", "toronto")
    print(f"Found {len(test_results)} results:")
    for res in test_results[:3]:
        print(f" - {res['title']} ({res['price']}): {res['url']}")
