import cloudscraper
from bs4 import BeautifulSoup
import mysql.connector
import time
import re
import random
from urllib.parse import urljoin

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="srilanka_vehicles"
    )

def clean_price_string(price_str):
    if not price_str or "Negotiable" in price_str or "Price on phone" in price_str:
        return 0
    # Remove Rs. and commas, keep only digits
    numbers_only = re.sub(r'[^\d]', '', price_str)
    return int(numbers_only) if numbers_only else 0

def clean_mileage(mileage_str):
    """Extract numeric mileage from string like '99,000 km'"""
    if not mileage_str:
        return 0
    numbers_only = re.sub(r'[^\d]', '', mileage_str)
    return int(numbers_only) if numbers_only else 0

def scrape_vehicle_listings(max_pages=8):
    """
    Scrape vehicle listings from Riyasewana search results
    Based on the actual HTML structure from the page
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print(f"--> Starting Riyasewana Scraper. Target: {max_pages} pages...")
    print("=" * 60)
    
    # Create scraper with browser emulation
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        },
        delay=random.uniform(2, 4)
    )
    
    # Base URL from the actual page (Toyota Vitz 2011-2020, Petrol, Automatic, Registered)
    base_url = "https://riyasewana.com/search/cars/toyota/vit/2011-2020/petrol/automatic/registered"
    
    all_vehicles = []
    
    for page in range(1, max_pages + 1):
        # Construct URL for each page
        if page == 1:
            url = base_url
        else:
            url = f"{base_url}?page={page}"
        
        print(f"\n📄 Fetching page {page}: {url}")
        
        try:
            response = scraper.get(url, timeout=20)
            if response.status_code != 200:
                print(f"⚠️ Failed to load page {page}. Status: {response.status_code}")
                continue
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all vehicle cards (li with class 'v-card')
            vehicle_cards = soup.find_all('li', class_='v-card')
            
            if not vehicle_cards:
                print(f"⚠️ No vehicle cards found on page {page}")
                continue
            
            print(f"Found {len(vehicle_cards)} vehicles on page {page}")
            
            page_vehicles = []
            for idx, card in enumerate(vehicle_cards, 1):
                try:
                    # Extract title
                    title_elem = card.find('div', class_='v-card-title')
                    if title_elem:
                        title_link = title_elem.find('a')
                        title = title_link.text.strip() if title_link else title_elem.text.strip()
                    else:
                        title = "Unknown"
                    
                    # Extract URL
                    url_elem = card.find('div', class_='v-card-img')
                    if url_elem:
                        link = url_elem.find('a')
                        vehicle_url = link.get('href') if link else None
                        if vehicle_url:
                            vehicle_url = urljoin("https://riyasewana.com", vehicle_url)
                    else:
                        vehicle_url = None
                    
                    # Extract price
                    price_elem = card.find('div', class_='v-card-price')
                    original_price = price_elem.text.strip() if price_elem else "Price not specified"
                    cleaned_price = clean_price_string(original_price)
                    
                    # Extract year
                    year_elem = card.find('div', class_='v-card-year')
                    year = year_elem.text.strip() if year_elem else "N/A"
                    
                    # Extract location and mileage from meta div
                    meta_elem = card.find('div', class_='v-card-meta')
                    location = "N/A"
                    mileage = 0
                    
                    if meta_elem:
                        # Get all text parts
                        meta_parts = meta_elem.get_text(separator='|').split('|')
                        for part in meta_parts:
                            part = part.strip()
                            if 'km' in part.lower():
                                mileage = clean_mileage(part)
                            elif part and part not in ['·', ''] and not any(c.isdigit() for c in part):
                                # Location doesn't have numbers typically
                                if len(part) > 2:
                                    location = part
                    
                    # Extract date
                    date_elem = card.find('div', class_='v-card-date')
                    post_date = date_elem.text.strip() if date_elem else "Unknown"
                    
                    vehicle_data = {
                        'title': title,
                        'url': vehicle_url,
                        'original_price': original_price,
                        'cleaned_price': cleaned_price,
                        'year': year,
                        'location': location,
                        'mileage': mileage,
                        'post_date': post_date,
                        'page': page
                    }
                    
                    page_vehicles.append(vehicle_data)
                    all_vehicles.append(vehicle_data)
                    
                    # Insert into database
                    sql = """INSERT INTO vehicle_prices 
                             (source, title, cleaned_price, original_price, location, year, mileage, post_date, vehicle_url) 
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"""
                    
                    cursor.execute(sql, (
                        "Riyasewana",
                        title,
                        cleaned_price,
                        original_price,
                        location,
                        year,
                        mileage,
                        post_date,
                        vehicle_url
                    ))
                    
                    print(f"  ✓ [{idx:2d}] {title[:35]:35} | {original_price:15} | {year} | {location}")
                    
                except Exception as e:
                    print(f"  ✗ Error processing vehicle {idx}: {e}")
                    continue
            
            # Commit batch for this page
            conn.commit()
            print(f"\n✅ Page {page} complete. Saved {len(page_vehicles)} vehicles.")
            
            # Random delay between pages to avoid detection
            if page < max_pages:
                delay = random.uniform(3, 6)
                print(f"⏳ Waiting {delay:.1f} seconds before next page...")
                time.sleep(delay)
            
        except Exception as e:
            print(f"❌ Error on page {page}: {e}")
            continue
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 SCRAPING SUMMARY:")
    print(f"   Total pages processed: {max_pages}")
    print(f"   Total vehicles scraped: {len(all_vehicles)}")
    
    if all_vehicles:
        # Price statistics
        prices = [v['cleaned_price'] for v in all_vehicles if v['cleaned_price'] > 0]
        if prices:
            print(f"   Average price: Rs. {sum(prices)//len(prices):,}")
            print(f"   Min price: Rs. {min(prices):,}")
            print(f"   Max price: Rs. {max(prices):,}")
        
        # Year distribution
        years = [v['year'] for v in all_vehicles if v['year'] != 'N/A']
        from collections import Counter
        year_counts = Counter(years)
        print(f"\n   Year distribution:")
        for year in sorted(year_counts.keys(), reverse=True)[:5]:
            print(f"     {year}: {year_counts[year]} vehicles")
    
    cursor.close()
    conn.close()
    print("\n✨ Scraping completed successfully!")
    
    return all_vehicles

def scrape_with_progress_tracking(max_pages=8):
    """Scrape with progress tracking and resume capability"""
    
    # You can add logic to track last successful page and resume
    last_page = 0
    
    print(f"Starting from page {last_page + 1}")
    vehicles = scrape_vehicle_listings(max_pages)
    
    return vehicles

if __name__ == "__main__":
    print("🚗 Riyasewana Vehicle Scraper")
    print("Target: Toyota Vitz (Registered, Petrol, Automatic, 2011-2020)")
    print("-" * 60)
    
    # Start with 2-3 pages for testing, then increase
    vehicles = scrape_vehicle_listings(max_pages=3)
    
    # Optional: Save to JSON file as backup
    import json
    with open('riyasewana_vehicles.json', 'w', encoding='utf-8') as f:
        json.dump(vehicles, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Data also saved to riyasewana_vehicles.json")