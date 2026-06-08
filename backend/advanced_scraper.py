# advanced_scraper.py
# Main advanced scraper for Riyasewana - WITH IMPROVED FUEL/TRANSMISSION DETECTION

import time
import json
import random
import re
from datetime import datetime, timedelta
from typing import Dict, List
from urllib.parse import urljoin

import cloudscraper
from bs4 import BeautifulSoup
import mysql.connector
import urllib3
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from config_categories import CATEGORIES_CONFIG

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class AdvancedRiyasewanaScraper:
    def __init__(self):
        # Create cloudscraper first
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            },
            delay=random.uniform(3, 5)
        )
        
        # Fix SSL - create a new session with SSL verification disabled
        session = requests.Session()
        session.verify = False
        
        # Add retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Replace the session
        self.scraper.session = session
        
        self.conn = None
        self.cursor = None
        self.progress_file = "scraping_progress.json"
        
        # Calculate cutoff date (2 months ago from today)
        self.cutoff_date = datetime.now() - timedelta(days=60)
        print(f"📅 Only scraping vehicles posted after: {self.cutoff_date.strftime('%Y-%m-%d')}")
        
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
        """Build correct Riyasewana search URL based on vehicle type"""
        
        # Get vehicle type for URL
        vehicle_type_param = params.get('vehicle_type_param', params.get('vehicle_type', 'cars')).lower()
        
        # Map vehicle types to Riyasewana search categories
        type_mapping = {
            'bus': 'buses',
            'buses': 'buses',
            'lorry': 'lorries',
            'lorries': 'lorries',
            'van': 'vans',
            'vans': 'vans',
            'car': 'cars',
            'cars': 'cars',
            'motorcycle': 'motorcycles',
            'motorcycles': 'motorcycles',
            'threewheel': 'three-wheelers',
            'three-wheelers': 'three-wheelers',
            'suv': 'cars',
            'jeep': 'cars',
            'pickup': 'pickup',
            'pickups': 'pickup',
            'crew cab': 'crew-cab',
            'crewcab': 'crew-cab',
            'tractor': 'tractors',
            'tractors': 'tractors',
            'heavy-duty': 'heavy-duty',
            'heavyduty': 'heavy-duty',
            'bicycle': 'bicycles',
            'bicycles': 'bicycles',
        }
        
        base_type = type_mapping.get(vehicle_type_param, 'cars')
        base = f"https://riyasewana.com/search/{base_type}"
        
        # Add make and model if provided
        parts = []
        if params.get('make'):
            make = params['make'].lower().replace(' ', '-')
            parts.append(make)
        if params.get('model') and params.get('model') != '':
            model = params['model'].lower().replace(' ', '-')
            parts.append(model)
        
        if parts:
            return "/".join([base] + parts)
        return base
    
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
    
    def parse_post_date(self, date_str: str) -> datetime:
        """Parse Riyasewana date string to datetime object"""
        if not date_str or date_str == "Unknown":
            return None
            
        date_str_lower = date_str.lower().strip()
        now = datetime.now()
        
        try:
            if 'today' in date_str_lower:
                return now
            elif 'yesterday' in date_str_lower:
                return now - timedelta(days=1)
            elif 'minute' in date_str_lower or 'min ago' in date_str_lower or 'm ago' in date_str_lower:
                match = re.search(r'(\d+)', date_str_lower)
                if match:
                    minutes = int(match.group(1))
                    return now - timedelta(minutes=minutes)
            elif 'hour' in date_str_lower or 'h ago' in date_str_lower:
                match = re.search(r'(\d+)', date_str_lower)
                if match:
                    hours = int(match.group(1))
                    return now - timedelta(hours=hours)
            elif 'day' in date_str_lower or 'd ago' in date_str_lower:
                match = re.search(r'(\d+)', date_str_lower)
                if match:
                    days = int(match.group(1))
                    return now - timedelta(days=days)
            else:
                current_year = now.year
                try:
                    date_with_year = f"{date_str} {current_year}"
                    parsed = datetime.strptime(date_with_year, "%b %d %Y")
                    if parsed > now:
                        parsed = datetime.strptime(f"{date_str} {current_year - 1}", "%b %d %Y")
                    return parsed
                except:
                    pass
        except Exception:
            pass
        return None
    
    def is_within_cutoff(self, post_date_str: str) -> bool:
        if not post_date_str or post_date_str == "Unknown":
            return True
        post_date = self.parse_post_date(post_date_str)
        if post_date is None:
            return True
        return post_date >= self.cutoff_date
    
    def parse_title(self, title: str) -> dict:
        """
        Parse vehicle title to extract make, model, and vehicle type
        
        Examples:
        "Ashok-Leyland Leyland Bus" -> {"make": "Ashok Leyland", "model": "Leyland", "type": "Bus"}
        "Toyota Prius Car" -> {"make": "Toyota", "model": "Prius", "type": "Car"}
        "Bajaj CT 100 Motorcycle" -> {"make": "Bajaj", "model": "CT 100", "type": "Motorcycle"}
        """
        result = {
            "make": None,
            "model": None,
            "type": None
        }
        
        if not title:
            return result
        
        # Vehicle type keywords (last word usually)
        type_keywords = {
            "Bus": ["bus"], 
            "Van": ["van"], 
            "Car": ["car"], 
            "Lorry": ["lorry", "truck"], 
            "SUV": ["suv"], 
            "Motorcycle": ["motorcycle", "motorbike", "bike"],
            "ThreeWheel": ["three wheel", "three-wheeler", "threewheel"]
        }
        
        title_lower = title.lower().strip()
        
        # 1. Find vehicle type 
        for vtype, keywords in type_keywords.items():
            for kw in keywords:
                if title_lower.endswith(kw) or f" {kw}" in title_lower:
                    result["type"] = vtype
                    # Remove type from title for further parsing
                    title_lower = title_lower.replace(f" {kw}", "").replace(kw, "").strip()
                    break
            if result["type"]:
                break
        
        # 2. Split remaining parts
        parts = title_lower.split()
        
        if len(parts) >= 2:
            # Check for hyphenated make at start
            if '-' in parts[0]:
                result["make"] = parts[0].replace('-', ' ').title()
                if len(parts) > 1:
                    result["model"] = " ".join(parts[1:]).title()
            else:
                result["make"] = parts[0].title()
                if len(parts) > 1:
                    result["model"] = " ".join(parts[1:]).title()
        elif len(parts) == 1:
            result["make"] = parts[0].title()
            result["model"] = parts[0].title()
        
        # Fix common make names
        make_fixes = {
            "Ashok-Leyland": "Ashok Leyland",
            "Mahindra": "Mahindra",
            "Tata": "Tata",
            "Bajaj": "Bajaj",
            "Hero": "Hero",
            "Tvs": "TVS",
            "Honda": "Honda",
            "Toyota": "Toyota",
            "Suzuki": "Suzuki",
            "Nissan": "Nissan",
            "Mitsubishi": "Mitsubishi",
            "Perodua": "Perodua",
            "Hyundai": "Hyundai",
            "Kia": "Kia",
            "Bmw": "BMW",
            "Mercedes": "Mercedes"
        }
        
        if result["make"]:
            for old, new in make_fixes.items():
                if old.lower() == result["make"].lower():
                    result["make"] = new
                    break
        
        return result
    
    def get_details_from_detail_page(self, vehicle_url, max_retries=2):
        """Fetch fuel type and transmission from detail page with improved parsing"""
        fuel_type = "unknown"
        transmission = "unknown"
        
        if not vehicle_url:
            return fuel_type, transmission
        
        for attempt in range(max_retries):
            try:
                time.sleep(random.uniform(1.5, 2.5))
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                }
                
                response = self.scraper.get(vehicle_url, timeout=30, headers=headers)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    page_text = soup.get_text().lower()
                    
                    # =============================================
                    # IMPROVED FUEL TYPE DETECTION
                    # =============================================
                    
                    # Pattern 1: "Fuel Type: Petrol" or similar
                    fuel_patterns = [
                        r'fuel\s*type\s*:\s*(\w+)',
                        r'fuel\s*:\s*(\w+)',
                        r'fuel\s*type\s*</strong>\s*:\s*(\w+)',
                        r'<strong>fuel\s*type<\/strong>\s*(\w+)',
                        r'fuel\s*type\s*-\s*(\w+)',
                    ]
                    
                    for pattern in fuel_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            found = match.group(1).lower()
                            if found in ['diesel', 'petrol', 'hybrid', 'electric']:
                                fuel_type = found
                                break
                    
                    # If not found, check for keywords in context
                    if fuel_type == "unknown":
                        fuel_sentences = re.findall(r'[^.]*fuel[^.]*\.', page_text, re.IGNORECASE)
                        for sentence in fuel_sentences:
                            if 'diesel' in sentence:
                                fuel_type = 'diesel'
                                break
                            elif 'petrol' in sentence:
                                fuel_type = 'petrol'
                                break
                            elif 'hybrid' in sentence:
                                fuel_type = 'hybrid'
                                break
                            elif 'electric' in sentence:
                                fuel_type = 'electric'
                                break
                    
                    # Check title element
                    if fuel_type == "unknown":
                        title_tag = soup.find('title')
                        if title_tag:
                            title_text = title_tag.get_text().lower()
                            if 'diesel' in title_text:
                                fuel_type = 'diesel'
                            elif 'petrol' in title_text:
                                fuel_type = 'petrol'
                            elif 'hybrid' in title_text:
                                fuel_type = 'hybrid'
                            elif 'electric' in title_text:
                                fuel_type = 'electric'
                    
                    # =============================================
                    # IMPROVED TRANSMISSION DETECTION
                    # =============================================
                    
                    gear_patterns = [
                        r'gear\s*:\s*(\w+)',
                        r'transmission\s*:\s*(\w+)',
                        r'gear\s*type\s*:\s*(\w+)',
                        r'<strong>gear<\/strong>\s*(\w+)',
                    ]
                    
                    for pattern in gear_patterns:
                        match = re.search(pattern, page_text, re.IGNORECASE)
                        if match:
                            found = match.group(1).lower()
                            if found in ['manual', 'automatic', 'auto']:
                                transmission = 'manual' if found == 'manual' else 'automatic'
                                break
                    
                    if transmission == "unknown":
                        gear_sentences = re.findall(r'[^.]*(?:gear|transmission)[^.]*\.', page_text, re.IGNORECASE)
                        for sentence in gear_sentences:
                            if 'manual' in sentence:
                                transmission = 'manual'
                                break
                            elif 'automatic' in sentence or 'auto' in sentence:
                                transmission = 'automatic'
                                break
                    
                    # Check main content area
                    main_content = soup.find('div', class_='col-md-8')
                    if main_content:
                        content_text = main_content.get_text().lower()
                        if transmission == "unknown":
                            if 'manual' in content_text:
                                transmission = 'manual'
                            elif 'automatic' in content_text or 'auto' in content_text:
                                transmission = 'automatic'
                        
                        if fuel_type == "unknown":
                            if 'diesel' in content_text:
                                fuel_type = 'diesel'
                            elif 'petrol' in content_text:
                                fuel_type = 'petrol'
                            elif 'hybrid' in content_text:
                                fuel_type = 'hybrid'
                            elif 'electric' in content_text:
                                fuel_type = 'electric'
                    
                    # If we got valid data, break
                    if fuel_type != 'unknown' or transmission != 'unknown':
                        break
                        
            except Exception as e:
                if attempt == 0:
                    print(f"⚠️ Error, retrying...", end=" ")
                
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(2, 3))
        
        return fuel_type, transmission
    
    def get_defaults_by_vehicle_type(self, vehicle_type: str, title: str = "") -> tuple:
        """Get default fuel type and transmission based on vehicle type"""
        vehicle_type_lower = vehicle_type.lower()
        title_lower = title.lower()
        
        fuel_type = "unknown"
        transmission = "unknown"
        
        # Check title for specific indicators first
        if 'electric' in title_lower or 'ev' in title_lower:
            fuel_type = 'electric'
        elif 'hybrid' in title_lower:
            fuel_type = 'hybrid'
        elif 'diesel' in title_lower:
            fuel_type = 'diesel'
        elif 'petrol' in title_lower:
            fuel_type = 'petrol'
        
        # Set defaults by vehicle type
        if vehicle_type_lower in ['motorcycle', 'bike', 'motorbike']:
            if fuel_type == "unknown":
                fuel_type = 'petrol'
            if transmission == "unknown":
                transmission = 'manual'
                
        elif vehicle_type_lower in ['threewheel', 'three wheel', 'three-wheeler']:
            if fuel_type == "unknown":
                fuel_type = 'petrol'
            if transmission == "unknown":
                transmission = 'manual'
                
        elif vehicle_type_lower in ['bus']:
            if fuel_type == "unknown":
                fuel_type = 'diesel'
            if transmission == "unknown":
                transmission = 'manual'
                
        elif vehicle_type_lower in ['lorry', 'truck']:
            if fuel_type == "unknown":
                fuel_type = 'diesel'
            if transmission == "unknown":
                transmission = 'manual'
                
        elif vehicle_type_lower in ['van']:
            if fuel_type == "unknown":
                fuel_type = 'diesel'
            if transmission == "unknown":
                transmission = 'manual'
                
        elif vehicle_type_lower in ['car', 'suv', 'jeep']:
            if fuel_type == "unknown":
                fuel_type = 'petrol'
            if transmission == "unknown":
                transmission = 'automatic'
        
        return fuel_type, transmission
    
    def extract_vehicle_data(self, card, category, vehicle_type):
        try:
            # Title
            title_elem = card.find('div', class_='v-card-title')
            if title_elem:
                title_link = title_elem.find('a')
                title = title_link.text.strip() if title_link else title_elem.text.strip()
            else:
                title = "Unknown"
            
            # Parse title to extract make, model, and type
            parsed = self.parse_title(title)
            
            # Use parsed values or fallback to category
            if parsed["make"]:
                actual_make = parsed["make"]
                actual_model = parsed["model"] if parsed["model"] else "Unknown"
                actual_vehicle_type = parsed["type"] if parsed["type"] else vehicle_type
            else:
                # Fallback to category parsing
                parts = category.split('_')
                actual_make = parts[0] if len(parts) > 0 else "Unknown"
                actual_model = parts[1] if len(parts) > 1 else "Unknown"
                actual_vehicle_type = vehicle_type
            
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
            
            if cleaned_price == 0:
                return None
            
            # Year
            year_elem = card.find('div', class_='v-card-year')
            year = year_elem.text.strip() if year_elem else "N/A"
            
            # Mileage
            meta_elem = card.find('div', class_='v-card-meta')
            mileage = 0
            
            if meta_elem:
                meta_parts = meta_elem.get_text(separator='|').split('|')
                for part in meta_parts:
                    part = part.strip()
                    if 'km' in part.lower():
                        mileage = self.clean_mileage(part)
            
            # Date
            date_elem = card.find('div', class_='v-card-date')
            post_date = date_elem.text.strip() if date_elem else "Unknown"
            
            # Check date filter
            if not self.is_within_cutoff(post_date):
                return None
            
            # Get fuel and transmission from detail page
            fuel_type, transmission = self.get_details_from_detail_page(vehicle_url)
            
            # If still unknown, set defaults based on vehicle type
            if fuel_type == "unknown" or transmission == "unknown":
                default_fuel, default_trans = self.get_defaults_by_vehicle_type(actual_vehicle_type, title)
                if fuel_type == "unknown":
                    fuel_type = default_fuel
                if transmission == "unknown":
                    transmission = default_trans
            
            return {
                'source': 'Riyasewana',
                'category': category,
                'make': actual_make,
                'model': actual_model,
                'vehicle_type': actual_vehicle_type,
                'title': title,
                'url': vehicle_url,
                'original_price': original_price,
                'cleaned_price': cleaned_price,
                'year': year,
                'mileage': mileage,
                'fuel_type': fuel_type,
                'transmission': transmission,
                'post_date': post_date
            }
        except Exception as e:
            return None
    
    def save_to_database(self, vehicle):
        try:
            self.conn.ping(reconnect=True)
            sql = """INSERT INTO vehicle_prices 
                     (source, title, cleaned_price, original_price, year, mileage, 
                      post_date, vehicle_url, category, vehicle_type, fuel_type, transmission,
                      make, model) 
                     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
            
            self.cursor.execute(sql, (
                vehicle['source'], vehicle['title'], vehicle['cleaned_price'],
                vehicle['original_price'], vehicle['year'], vehicle['mileage'],
                vehicle['post_date'], vehicle['url'], vehicle['category'],
                vehicle['vehicle_type'], vehicle['fuel_type'], vehicle['transmission'],
                vehicle.get('make', 'Unknown'), vehicle.get('model', 'Unknown')
            ))
            return True
        except Exception as e:
            return False
    
    def save_to_json(self, vehicles, category):
        filename = f"riyasewana_{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(vehicles, f, indent=2, ensure_ascii=False)
        print(f"    💾 Saved {len(vehicles)} vehicles to {filename}")
    
    def scrape_category_safe(self, category_name: str, config: Dict):
        if self.conn:
            try:
                self.conn.close()
            except:
                pass
        
        self.conn = self.get_db_connection()
        self.cursor = self.conn.cursor()
        
        params = config['params'].copy()
        max_pages = config['pages']
        vehicle_type = config.get('vehicle_type', 'Car')
        
        params['vehicle_type_param'] = vehicle_type.lower()
        base_url = self.build_search_url(params)
        
        print(f"\n{'🔥' * 40}")
        print(f"📌 SCRAPING: {category_name} ({vehicle_type})")
        print(f"🔗 URL: {base_url}")
        print(f"📄 Pages: {max_pages}")
        print(f"{'🔥' * 40}\n")
        
        all_vehicles = []
        successful_pages = 0
        
        for page in range(1, max_pages + 1):
            url = f"{base_url}?page={page}" if page > 1 else base_url
            
            print(f"📄 Page {page}/{max_pages}", end=" ")
            
            try:
                response = self.scraper.get(url, timeout=25)
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
                    if idx % 10 == 0:
                        print(f"    Processing {idx}/{len(vehicle_cards)}...")
                    
                    vehicle_data = self.extract_vehicle_data(card, category_name, vehicle_type)
                    if vehicle_data:
                        page_vehicles.append(vehicle_data)
                        all_vehicles.append(vehicle_data)
                        self.save_to_database(vehicle_data)
                
                self.conn.commit()
                successful_pages += 1
                print(f"\n    ✅ Page {page} complete - {len(page_vehicles)} vehicles saved ({len(all_vehicles)} total)")
                
                if page < max_pages and len(page_vehicles) > 0:
                    delay = random.uniform(4, 7)
                    print(f"    ⏳ Waiting {delay:.1f}s...")
                    time.sleep(delay)
                elif page < max_pages and len(page_vehicles) == 0:
                    print(f"    🛑 No vehicles on this page, stopping")
                    break
                    
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
        
        if all_vehicles:
            self.save_to_json(all_vehicles, category_name)
        
        print(f"\n📊 {category_name} SUMMARY:")
        print(f"   Pages scraped: {successful_pages}/{max_pages}")
        print(f"   Vehicles collected: {len(all_vehicles)}")
        
        return len(all_vehicles)
    
    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()


def main():
    print("=" * 70)
    print("🚗 RIYASEWANA ADVANCED VEHICLE SCRAPER")
    print("   (With Title Parser & Smart Fuel/Transmission Detection)")
    print("=" * 70)
    
    scraper = AdvancedRiyasewanaScraper()
    
    print("\n📋 Select Mode:")
    print("1. Scrape by Vehicle Type")
    print("2. Test mode (1 category, 1 page)")
    print("3. Exit")
    
    mode = input("\n👉 Enter choice: ").strip()
    
    if mode == '1':
        types = ["Bus", "Lorry", "Van", "Car", "Motorcycle", "SUV", "Pickup", "ThreeWheel"]
        for idx, vt in enumerate(types, 1):
            print(f"   {idx}. {vt}")
        
        try:
            choice = int(input("\nSelect vehicle type: ")) - 1
            if 0 <= choice < len(types):
                vt = types[choice]
                pages = int(input("Pages (1-2, default 1): ") or "1")
                
                categories = {}
                for cat_name, config in CATEGORIES_CONFIG.items():
                    if config.get('vehicle_type') == vt and config.get('enabled', True):
                        config_copy = config.copy()
                        config_copy['pages'] = pages
                        categories[cat_name] = config_copy
                
                if categories:
                    print(f"\n✅ Found {len(categories)} categories for {vt}")
                    confirm = input(f"\nStart scraping {vt}? (y/n): ").strip().lower()
                    
                    if confirm == 'y':
                        total = 0
                        for idx, (cat_name, config) in enumerate(categories.items(), 1):
                            print(f"\n📌 [{idx}/{len(categories)}] {cat_name}")
                            count = scraper.scrape_category_safe(cat_name, config)
                            total += count
                            if idx < len(categories):
                                time.sleep(10)
                        print(f"\n🎉 Total: {total} vehicles")
        except ValueError:
            print("Invalid input")
            
    elif mode == '2':
        test_options = list(CATEGORIES_CONFIG.keys())[:10]
        for idx, cat in enumerate(test_options, 1):
            vt = CATEGORIES_CONFIG[cat].get('vehicle_type', 'Car')
            print(f"   {idx}. {cat} ({vt})")
        
        try:
            choice = int(input("\nSelect category: ")) - 1
            if 0 <= choice < len(test_options):
                cat_name = test_options[choice]
                config = CATEGORIES_CONFIG[cat_name].copy()
                config['pages'] = 1
                count = scraper.scrape_category_safe(cat_name, config)
                print(f"\n✅ Test complete: {count} vehicles")
        except:
            print("Invalid selection")
    
    scraper.close()


if __name__ == "__main__":
    main()