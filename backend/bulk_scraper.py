import cloudscraper
from bs4 import BeautifulSoup
import mysql.connector
import time
import re
import random
from urllib.parse import urljoin
from typing import List, Dict
import json

class RiyasewanaScraper:
    def __init__(self):
        self.conn = self.get_db_connection()
        self.cursor = self.conn.cursor()
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            },
            delay=random.uniform(2, 4)
        )
        
    def get_db_connection(self):
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # ඔයාගේ password එක දාන්න
            database="srilanka_vehicles"
        )
    
    def scrape_category(self, search_params: Dict, max_pages: int = 5, category_name: str = None):
        """
        Generic scraper for any vehicle category
        
        search_params example:
        {
            'make': 'toyota',
            'model': 'corolla',
            'year_from': '2010',
            'year_to': '2020',
            'fuel': 'petrol',
            'transmission': 'automatic',
            'condition': 'registered'
        }
        """
        # Build URL based on search parameters
        base_url = self.build_search_url(search_params)
        
        print(f"\n{'='*60}")
        print(f"🎯 Scraping: {category_name or search_params.get('model', 'Unknown')}")
        print(f"🔗 URL: {base_url}")
        print(f"{'='*60}\n")
        
        all_vehicles = []
        
        for page in range(1, max_pages + 1):
            url = f"{base_url}?page={page}" if page > 1 else base_url
            
            print(f"📄 Page {page}: {url}")
            
            try:
                response = self.scraper.get(url, timeout=20)
                if response.status_code != 200:
                    print(f"⚠️ Failed. Status: {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                vehicle_cards = soup.find_all('li', class_='v-card')
                
                if not vehicle_cards:
                    print(f"⚠️ No vehicles found on page {page}")
                    break
                
                print(f"Found {len(vehicle_cards)} vehicles on page {page}")
                
                for idx, card in enumerate(vehicle_cards, 1):
                    vehicle_data = self.extract_vehicle_data(card, category_name or search_params.get('model'))
                    if vehicle_data:
                        all_vehicles.append(vehicle_data)
                        self.save_to_database(vehicle_data)
                        print(f"  ✓ [{idx:2d}] {vehicle_data['title'][:40]:40} | {vehicle_data['cleaned_price']:,} LKR")
                
                self.conn.commit()
                print(f"\n✅ Page {page} complete. Total so far: {len(all_vehicles)}")
                
                if page < max_pages:
                    delay = random.uniform(3, 6)
                    print(f"⏳ Waiting {delay:.1f}s...")
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"❌ Error on page {page}: {e}")
                continue
        
        # Save category data to JSON
        self.save_to_json(all_vehicles, category_name or search_params.get('model'))
        
        return all_vehicles
    
    def build_search_url(self, params: Dict) -> str:
        """Build Riyasewana search URL from parameters"""
        base = "https://riyasewana.com/search/cars"
        
        parts = []
        if params.get('make'):
            parts.append(params['make'].lower())
        if params.get('model'):
            parts.append(params['model'].lower())
        if params.get('year_from') and params.get('year_to'):
            parts.append(f"{params['year_from']}-{params['year_to']}")
        if params.get('fuel'):
            parts.append(params['fuel'].lower())
        if params.get('transmission'):
            parts.append(params['transmission'].lower())
        if params.get('condition'):
            parts.append(params['condition'].lower())
        
        return "/".join([base] + parts) if parts else base
    
    def extract_vehicle_data(self, card, category):
        """Extract data from a vehicle card"""
        try:
            # Title
            title_elem = card.find('div', class_='v-card-title')
            if title_elem:
                title_link = title_elem.find('a')
                title = title_link.text.strip() if title_link else title_elem.text.strip()
            else:
                title = "Unknown"
            
            # URL
            url_elem = card.find('div', class_='v-card-img')
            vehicle_url = None
            if url_elem:
                link = url_elem.find('a')
                if link:
                    vehicle_url = urljoin("https://riyasewana.com", link.get('href'))
            
            # Price
            price_elem = card.find('div', class_='v-card-price')
            original_price = price_elem.text.strip() if price_elem else "Price not specified"
            cleaned_price = self.clean_price(original_price)
            
            # Year
            year_elem = card.find('div', class_='v-card-year')
            year = year_elem.text.strip() if year_elem else "N/A"
            
            # Location & Mileage
            meta_elem = card.find('div', class_='v-card-meta')
            location = "N/A"
            mileage = 0
            
            if meta_elem:
                meta_parts = meta_elem.get_text(separator='|').split('|')
                for part in meta_parts:
                    part = part.strip()
                    if 'km' in part.lower():
                        mileage = self.clean_mileage(part)
                    elif part and not any(c.isdigit() for c in part) and len(part) > 2:
                        location = part
            
            # Date
            date_elem = card.find('div', class_='v-card-date')
            post_date = date_elem.text.strip() if date_elem else "Unknown"
            
            return {
                'source': 'Riyasewana',
                'category': category,
                'title': title,
                'url': vehicle_url,
                'original_price': original_price,
                'cleaned_price': cleaned_price,
                'year': year,
                'location': location,
                'mileage': mileage,
                'post_date': post_date
            }
        except Exception as e:
            print(f"Error extracting data: {e}")
            return None
    
    def clean_price(self, price_str):
        if not price_str or "Negotiable" in price_str or "Price on phone" in price_str:
            return 0
        numbers_only = re.sub(r'[^\d]', '', price_str)
        return int(numbers_only) if numbers_only else 0
    
    def clean_mileage(self, mileage_str):
        if not mileage_str:
            return 0
        numbers_only = re.sub(r'[^\d]', '', mileage_str)
        return int(numbers_only) if numbers_only else 0
    
    def save_to_database(self, vehicle):
        sql = """INSERT INTO vehicle_prices 
                 (source, title, cleaned_price, original_price, location, year, mileage, post_date, vehicle_url, category) 
                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        
        self.cursor.execute(sql, (
            vehicle['source'], vehicle['title'], vehicle['cleaned_price'],
            vehicle['original_price'], vehicle['location'], vehicle['year'],
            vehicle['mileage'], vehicle['post_date'], vehicle['url'], vehicle['category']
        ))
    
    def save_to_json(self, vehicles, category):
        filename = f"riyasewana_{category}_{time.strftime('%Y%m%d')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(vehicles, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Saved {len(vehicles)} vehicles to {filename}")
    
    def close(self):
        self.cursor.close()
        self.conn.close()

# ============= MAIN SCRAPING STRATEGY =============

def scrape_multiple_categories():
    """Scrape different vehicle categories step by step"""
    
    scraper = RiyasewanaScraper()
    
    # Define categories to scrape (start small, then expand)
    categories = [
        # Phase 1: Toyota (starting with what we have)
        {
            'name': 'Toyota_Vitz',
            'params': {
                'make': 'toyota',
                'model': 'vit',
                'year_from': '2011',
                'year_to': '2020',
                'fuel': 'petrol',
                'transmission': 'automatic',
                'condition': 'registered'
            },
            'pages': 3  # Start small
        },
        
        # Phase 2: Add more Toyota models
        {
            'name': 'Toyota_Corolla',
            'params': {
                'make': 'toyota',
                'model': 'corolla',
                'year_from': '2010',
                'year_to': '2020',
                'fuel': 'petrol',
                'transmission': 'automatic',
                'condition': 'registered'
            },
            'pages': 3
        },
        {
            'name': 'Toyota_Axio',
            'params': {
                'make': 'toyota',
                'model': 'axio',
                'year_from': '2010',
                'year_to': '2020',
                'fuel': 'petrol',
                'transmission': 'automatic',
                'condition': 'registered'
            },
            'pages': 3
        },
        
        # Phase 3: Suzuki
        {
            'name': 'Suzuki_Alto',
            'params': {
                'make': 'suzuki',
                'model': 'alto',
                'year_from': '2015',
                'year_to': '2023',
                'fuel': 'petrol',
                'transmission': 'manual',
                'condition': 'registered'
            },
            'pages': 2
        },
        
        # Phase 4: Nissan
        {
            'name': 'Nissan_March',
            'params': {
                'make': 'nissan',
                'model': 'march',
                'year_from': '2010',
                'year_to': '2020',
                'fuel': 'petrol',
                'transmission': 'automatic',
                'condition': 'registered'
            },
            'pages': 2
        },
        
        # Phase 5: Honda
        {
            'name': 'Honda_Vezel',
            'params': {
                'make': 'honda',
                'model': 'vezel',
                'year_from': '2013',
                'year_to': '2020',
                'fuel': 'petrol',
                'transmission': 'automatic',
                'condition': 'registered'
            },
            'pages': 2
        }
    ]
    
    total_vehicles = []
    
    for idx, category in enumerate(categories, 1):
        print(f"\n{'🔥'*30}")
        print(f"Category {idx}/{len(categories)}: {category['name']}")
        print(f"{'🔥'*30}")
        
        try:
            vehicles = scraper.scrape_category(
                search_params=category['params'],
                max_pages=category['pages'],
                category_name=category['name']
            )
            total_vehicles.extend(vehicles)
            
            print(f"\n✅ Completed {category['name']}: {len(vehicles)} vehicles")
            
            # Longer delay between different categories
            if idx < len(categories):
                delay = random.uniform(10, 15)
                print(f"\n⏸️  Taking a {delay:.0f} second break before next category...")
                time.sleep(delay)
                
        except Exception as e:
            print(f"❌ Failed to scrape {category['name']}: {e}")
            continue
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"📊 GRAND SUMMARY")
    print(f"{'='*60}")
    print(f"Total categories scraped: {len([c for c in categories if c])}")
    print(f"Total vehicles collected: {len(total_vehicles)}")
    
    # Save master JSON
    with open('riyasewana_all_vehicles_master.json', 'w', encoding='utf-8') as f:
        json.dump(total_vehicles, f, indent=2, ensure_ascii=False)
    
    scraper.close()
    return total_vehicles

# Progressive scraping function (resume capability)
def progressive_scrape():
    """
    Scrape one category at a time with ability to resume
    """
    print("🚗 Progressive Vehicle Scraper")
    print("=================================")
    print("Options:")
    print("1. Scrape Toyota Vitz only (test)")
    print("2. Scrape all Toyota models")
    print("3. Scrape all categories (full)")
    print("4. Custom category")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    scraper = RiyasewanaScraper()
    
    if choice == '1':
        # Test mode
        vehicles = scraper.scrape_category(
            search_params={
                'make': 'toyota',
                'model': 'vit',
                'year_from': '2011',
                'year_to': '2020',
                'fuel': 'petrol',
                'transmission': 'automatic',
                'condition': 'registered'
            },
            max_pages=2,
            category_name='Toyota_Vitz_Test'
        )
        
    elif choice == '2':
        # Toyota only
        toyota_models = ['vit', 'corolla', 'axio', 'premio', 'allion', 'prius']
        all_vehicles = []
        
        for model in toyota_models:
            print(f"\n--- Scraping Toyota {model.upper()} ---")
            vehicles = scraper.scrape_category(
                search_params={
                    'make': 'toyota',
                    'model': model,
                    'year_from': '2010',
                    'year_to': '2020',
                    'fuel': 'petrol',
                    'transmission': 'automatic',
                    'condition': 'registered'
                },
                max_pages=3,
                category_name=f'Toyota_{model.capitalize()}'
            )
            all_vehicles.extend(vehicles)
            
            if model != toyota_models[-1]:
                time.sleep(random.uniform(8, 12))
        
        print(f"\n✅ Total Toyota vehicles: {len(all_vehicles)}")
        
    elif choice == '3':
        # Full scrape
        vehicles = scrape_multiple_categories()
        
    else:
        # Custom
        make = input("Enter make (e.g., toyota, suzuki, nissan): ")
        model = input("Enter model (e.g., vit, corolla, alto): ")
        pages = int(input("Number of pages: "))
        
        vehicles = scraper.scrape_category(
            search_params={'make': make, 'model': model},
            max_pages=pages,
            category_name=f"{make}_{model}"
        )
    
    scraper.close()
    return vehicles

if __name__ == "__main__":
    print("🚗 Riyasewana Complete Vehicle Scraper")
    print("="*60)
    
    # Run progressive scraping
    # Start with option 1 for testing, then move to 2, then 3
    progressive_scrape()