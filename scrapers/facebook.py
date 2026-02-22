from playwright.sync_api import sync_playwright
import time
import re

def scrape_facebook(query: str, region: str) -> list[dict]:
    """
    Scrapes Facebook Marketplace using Playwright.
    Facebook heavily relies on JS and uses dynamic obfuscated class names.
    We look for Marketplace item links and extract nearby text.
    """
    results = []
    
    # Simple formatting of region for Facebook (e.g., 'toronto', 'sanfrancisco')
    region_formatted = region.lower().replace(" ", "")
    
    url = f"https://www.facebook.com/marketplace/{region_formatted}/search/?query={query}"
    
    with sync_playwright() as p:
        # Launching with args to make it look less like a bot
        browser = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800}
        )
        page = context.new_page()
        
        try:
            page.goto(url, timeout=30000)
            # Wait for some listings to load. 
            # We look for links containing '/marketplace/item/'
            page.wait_for_selector('a[href*="/marketplace/item/"]', timeout=10000)
            
            # Scroll down slightly to trigger lazy loading of images/prices if needed
            page.mouse.wheel(0, 1000)
            time.sleep(2)
            
            # Grab all listing elements
            listing_elements = page.locator('a[href*="/marketplace/item/"]').all()
            
            seen_urls = set()
            
            for elem in listing_elements:
                try:
                    href = elem.get_attribute('href')
                    if not href or href in seen_urls:
                        continue
                        
                    # Build full URL
                    full_url = href if href.startswith('http') else f"https://www.facebook.com{href}"
                    # Strip tracking parameters from URL to get clean ID
                    clean_url = full_url.split('?')[0]
                    
                    seen_urls.add(href)
                    
                    # The text inside the anchor usually contains the price, title, and location sequentially.
                    # e.g., "C$1,200\nMacbook Pro 2021\nToronto, ON"
                    inner_text = elem.inner_text().strip()
                    lines = [line.strip() for line in inner_text.split('\n') if line.strip()]
                    
                    if not lines:
                        continue
                        
                    # Attempt to parse lines. Facebook changes this often.
                    # Typically: [Price, Title, Location] or [Title, Price, Location]
                    price = "N/A"
                    title = "Unknown Title"
                    
                    for line in lines:
                        if '$' in line or 'Free' in line or re.match(r'^\d', line):
                            # Very rough heuristic for price
                            if price == "N/A": 
                                price = line
                        elif title == "Unknown Title" and len(line) > 3:
                            title = line
                    
                    # Unique item ID from URL 
                    # url is typically /marketplace/item/1234567890/
                    item_id_match = re.search(r'/item/(\d+)', clean_url)
                    item_id = item_id_match.group(1) if item_id_match else clean_url
                    
                    results.append({
                        'title': title,
                        'price': price,
                        'url': clean_url,
                        'id': item_id,
                        'source': 'facebook'
                    })
                except Exception as e:
                    print(f"Error parsing Facebook element: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error scraping Facebook: {e}")
        finally:
            browser.close()
            
    return results

if __name__ == "__main__":
    # Test
    test_results = scrape_facebook("macbook", "toronto")
    print(f"Found {len(test_results)} results:")
    for res in test_results[:3]:
        print(f" - {res['title']} ({res['price']}): {res['url']}")
