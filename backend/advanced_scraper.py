# advanced_scraper.py
# Main advanced scraper for Riyasewana

import time
import json
import random
import re
from datetime import datetime
from typing import Dict, List
from urllib.parse import urljoin

import cloudscraper
from bs4 import BeautifulSoup
import mysql.connector

from config_categories import CATEGORIES_CONFIG
from interactive_scraper import InteractiveCategorySelector


class AdvancedRiyasewanaScraper:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            },
            delay=random.uniform(2, 4)
        )
        self.conn = None
        self.cursor = None
        self.progress_file = "scraping_progress.json"
        
    def get_db_connection(self):
        """Create database connection"""
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Change this to your MySQL password
            database="srilanka_vehicles"
        )
    
    def save_progress(self, completed_categories: List[str]):
        """Save progress to resume later"""
        progress = {
            "last_updated": datetime.now().isoformat(),
            "completed_categories": completed_categories
        }
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def load_progress(self):
        """Load previous progress"""
        try:
            with open(self.progress_file, 'r') as f:
                progress = json.load(f)
                return progress.get("completed_categories", [])
        except FileNotFoundError:
            return []
    
    def build_search_url(self, params: Dict) -> str:
        """Build search URL from parameters"""
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
    
    def clean_price(self, price_str):
        """Extract numeric price from string"""
        if not price_str or "Negotiable" in price_str or "Price on phone" in price_str:
            return 0
        numbers_only = re.sub(r'[^\d]', '', price_str)
        return int(numbers_only) if numbers_only else 0
    
    def clean_mileage(self, mileage_str):
        """Extract numeric mileage from string"""
        if not mileage_str:
            return 0
        numbers_only = re.sub(r'[^\d]', '', mileage_str)
        return int(numbers_only) if numbers_only else 0
    
    def extract_vehicle_data(self, card, category):
        """Extract vehicle data from HTML card"""
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
            return None
    
    def save_to_database(self, vehicle):
        """Save vehicle data to database"""
        try:
            self.conn.ping(reconnect=True)
            sql = """INSERT INTO vehicle_prices 
                     (source, title, cleaned_price, original_price, location, year, mileage, post_date, vehicle_url, category) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            
            self.cursor.execute(sql, (
                vehicle['source'], vehicle['title'], vehicle['cleaned_price'],
                vehicle['original_price'], vehicle['location'], vehicle['year'],
                vehicle['mileage'], vehicle['post_date'], vehicle['url'], vehicle['category']
            ))
            return True
        except Exception as e:
            print(f"    ⚠️ DB Error: {e}")
            return False
    
    def save_to_json(self, vehicles, category):
        """Save vehicles to JSON backup file"""
        filename = f"riyasewana_{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(vehicles, f, indent=2, ensure_ascii=False)
        print(f"    💾 Saved {len(vehicles)} vehicles to {filename}")
    
    def scrape_category_safe(self, category_name: str, config: Dict):
        """Scrape a single category with error handling"""
        
        # Create new connection for each category
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
        
        self.conn = self.get_db_connection()
        self.cursor = self.conn.cursor()
        
        params = config['params']
        max_pages = config['pages']
        
        # Build URL
        base_url = self.build_search_url(params)
        
        print(f"\n{'🔥' * 40}")
        print(f"📌 SCRAPING: {category_name}")
        print(f"🔗 URL: {base_url}")
        print(f"📄 Pages: {max_pages}")
        print(f"{'🔥' * 40}\n")
        
        all_vehicles = []
        successful_pages = 0
        
        for page in range(1, max_pages + 1):
            url = f"{base_url}?page={page}" if page > 1 else base_url
            
            print(f"📄 Page {page}/{max_pages}", end=" ")
            
            try:
                response = self.scraper.get(url, timeout=20)
                if response.status_code != 200:
                    print(f"❌ Failed (Status: {response.status_code})")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                vehicle_cards = soup.find_all('li', class_='v-card')
                
                if not vehicle_cards:
                    print(f"⚠️ No vehicles found")
                    break
                
                print(f"✅ Found {len(vehicle_cards)} vehicles")
                
                page_vehicles = []
                for idx, card in enumerate(vehicle_cards, 1):
                    vehicle_data = self.extract_vehicle_data(card, category_name)
                    if vehicle_data and vehicle_data['cleaned_price'] > 0:
                        page_vehicles.append(vehicle_data)
                        all_vehicles.append(vehicle_data)
                        
                        # Insert into database
                        self.save_to_database(vehicle_data)
                        
                        # Print progress every 10 vehicles
                        if idx % 10 == 0:
                            print(f"    Processed {idx}/{len(vehicle_cards)}...")
                
                # Commit page
                self.conn.commit()
                successful_pages += 1
                print(f"    ✅ Page {page} complete - {len(page_vehicles)} vehicles saved (${len(all_vehicles)} total)")
                
                # Delay between pages
                if page < max_pages:
                    delay = random.uniform(3, 6)
                    print(f"    ⏳ Waiting {delay:.1f}s...")
                    time.sleep(delay)
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
        
        # Save category to JSON
        if all_vehicles:
            self.save_to_json(all_vehicles, category_name)
        
        # Summary
        print(f"\n📊 {category_name} SUMMARY:")
        print(f"   Pages scraped: {successful_pages}/{max_pages}")
        print(f"   Vehicles collected: {len(all_vehicles)}")
        
        if self.conn:
            try:
                self.cursor.execute("SELECT COUNT(*) FROM vehicle_prices WHERE category = %s", (category_name,))
                db_count = self.cursor.fetchone()[0]
                print(f"   Records in database: {db_count}")
            except:
                pass
        
        return len(all_vehicles)
    
    def close(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def main():
    print("=" * 70)
    print("🚗 RIYASEWANA ADVANCED VEHICLE SCRAPER")
    print("=" * 70)
    print("\n⚠️  Important Notes:")
    print("   - Make sure MySQL is running")
    print("   - Check database password in code")
    print("   - Start with 1-2 categories for testing")
    print("=" * 70)
    
    # Initialize scraper
    scraper = AdvancedRiyasewanaScraper()
    
    # Choose mode
    print("\n📋 Select Mode:")
    print("1. Interactive - Select categories manually")
    print("2. Run all enabled categories")
    print("3. Resume from last progress")
    print("4. Run specific brand only")
    print("5. Test mode (Single category, 1 page)")
    
    mode = input("\n👉 Enter choice (1-5): ").strip()
    
    selected_categories = {}
    
    if mode == '1':
        # Interactive mode
        selector = InteractiveCategorySelector()
        selected_categories = selector.get_selected_categories()
        
    elif mode == '2':
        # All enabled
        for cat_name, config in CATEGORIES_CONFIG.items():
            if config.get('enabled', True):
                selected_categories[cat_name] = config
        print(f"✅ Selected {len(selected_categories)} categories")
        
    elif mode == '3':
        # Resume
        completed = scraper.load_progress()
        for cat_name, config in CATEGORIES_CONFIG.items():
            if config.get('enabled', True) and cat_name not in completed:
                selected_categories[cat_name] = config
        print(f"✅ Resuming with {len(selected_categories)} remaining categories")
        if completed:
            print(f"   Already completed: {', '.join(completed)}")
        
    elif mode == '4':
        # Specific brand
        brand = input("Enter brand name (e.g., Suzuki, Nissan, Honda, Toyota): ").strip().capitalize()
        for cat_name, config in CATEGORIES_CONFIG.items():
            if cat_name.startswith(brand) and config.get('enabled', True):
                selected_categories[cat_name] = config
        print(f"✅ Selected {len(selected_categories)} {brand} categories")
        
    elif mode == '5':
        # Test mode - pick one category with 1 page
        print("\n🧪 TEST MODE - Available categories:")
        test_options = list(CATEGORIES_CONFIG.keys())[:10]
        for idx, cat in enumerate(test_options, 1):
            print(f"   {idx}. {cat}")
        
        try:
            test_choice = int(input("\nSelect category number: ")) - 1
            if 0 <= test_choice < len(test_options):
                cat_name = test_options[test_choice]
                config = CATEGORIES_CONFIG[cat_name].copy()
                config['pages'] = 1  # Override to 1 page only
                selected_categories[cat_name] = config
                print(f"✅ Test mode: {cat_name} (1 page only)")
        except:
            print("Invalid selection")
    
    if not selected_categories:
        print("❌ No categories selected. Exiting.")
        return
    
    print(f"\n📋 Categories to scrape: {len(selected_categories)}")
    for cat in selected_categories.keys():
        pages = selected_categories[cat].get('pages', 3)
        print(f"   - {cat} ({pages} pages)")
    
    confirm = input("\n🚀 Start scraping? (y/n): ").strip().lower()
    if confirm != 'y':
        print("Cancelled.")
        return
    
    # Start scraping
    completed_categories = scraper.load_progress() if mode != '1' else []
    total_vehicles = 0
    success_count = 0
    
    for idx, (cat_name, config) in enumerate(selected_categories.items(), 1):
        print(f"\n{'📌' * 35}")
        print(f"Progress: {idx}/{len(selected_categories)}")
        
        try:
            vehicles_count = scraper.scrape_category_safe(cat_name, config)
            total_vehicles += vehicles_count
            success_count += 1
            
            # Save progress
            if cat_name not in completed_categories:
                completed_categories.append(cat_name)
            scraper.save_progress(completed_categories)
            
        except Exception as e:
            print(f"❌ Failed to scrape {cat_name}: {e}")
        
        # Longer delay between different categories
        if idx < len(selected_categories):
            delay = random.uniform(10, 20)
            print(f"\n⏸️  Break for {delay:.0f} seconds before next category...")
            time.sleep(delay)
    
    # Final summary
    print(f"\n{'🎉' * 35}")
    print(f"SCRAPING COMPLETED!")
    print(f"{'🎉' * 35}")
    print(f"Categories scraped successfully: {success_count}/{len(selected_categories)}")
    print(f"Total vehicles collected: {total_vehicles}")
    
    scraper.close()
    
    # Ask if user wants to see database summary
    view_summary = input("\n📊 View database summary? (y/n): ").strip().lower()
    if view_summary == 'y':
        try:
            conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="",
                database="srilanka_vehicles"
            )
            cursor = conn.cursor()
            cursor.execute("""
                SELECT category, COUNT(*) as count, AVG(cleaned_price) as avg_price
                FROM vehicle_prices 
                WHERE cleaned_price > 0
                GROUP BY category
                ORDER BY count DESC
            """)
            results = cursor.fetchall()
            print("\n📊 DATABASE SUMMARY:")
            print("-" * 60)
            for category, count, avg_price in results:
                print(f"   {category}: {count} vehicles, Avg: Rs. {int(avg_price):,}")
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Could not fetch summary: {e}")


if __name__ == "__main__":
    main()