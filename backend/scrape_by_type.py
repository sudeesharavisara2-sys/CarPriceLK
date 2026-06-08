# scrape_by_type.py
# Scrape vehicles by type - one type at a time

import time
from advanced_scraper import AdvancedRiyasewanaScraper
from config_categories import CATEGORIES_CONFIG

def scrape_by_vehicle_type(vehicle_type, max_pages_per_category=2):
    """Scrape all categories of a specific vehicle type"""
    
    print(f"\n{'='*60}")
    print(f"🚛 SCRAPING: {vehicle_type}")
    print(f"{'='*60}")
    
    # Get all categories of this type
    categories = {}
    for cat_name, config in CATEGORIES_CONFIG.items():
        if config.get('vehicle_type') == vehicle_type and config.get('enabled', True):
            config_copy = config.copy()
            config_copy['pages'] = min(config_copy.get('pages', 3), max_pages_per_category)
            categories[cat_name] = config_copy
    
    if not categories:
        print(f"❌ No categories found for {vehicle_type}")
        return 0
    
    print(f"📋 Found {len(categories)} categories for {vehicle_type}")
    for cat in categories.keys():
        print(f"   - {cat}")
    
    confirm = input(f"\n🚀 Start scraping {vehicle_type}? (y/n): ").strip().lower()
    if confirm != 'y':
        return 0
    
    scraper = AdvancedRiyasewanaScraper()
    total_vehicles = 0
    successful = 0
    
    for idx, (cat_name, config) in enumerate(categories.items(), 1):
        print(f"\n📌 [{idx}/{len(categories)}] Scraping {cat_name}...")
        
        try:
            count = scraper.scrape_category_safe(cat_name, config)
            total_vehicles += count
            successful += 1
            print(f"✅ {cat_name}: {count} vehicles")
        except Exception as e:
            print(f"❌ Failed {cat_name}: {e}")
        
        if idx < len(categories):
            delay = 10
            print(f"\n⏸️ Waiting {delay} seconds before next category...")
            time.sleep(delay)
    
    scraper.close()
    
    print(f"\n{'='*60}")
    print(f"📊 {vehicle_type} SUMMARY:")
    print(f"   Categories: {successful}/{len(categories)}")
    print(f"   Total vehicles: {total_vehicles}")
    print(f"{'='*60}")
    
    return total_vehicles

def main():
    print("=" * 60)
    print("🚗 VEHICLE SCRAPER - BY TYPE")
    print("=" * 60)
    
    vehicle_types = [
        "Bus", "Lorry", "Van", "Car", "Motorcycle",
        "SUV", "Pickup", "ThreeWheel", "CrewCab", "Tractor"
    ]
    
    print("\nSelect vehicle type to scrape:")
    for idx, vt in enumerate(vehicle_types, 1):
        print(f"   {idx}. {vt}")
    print(f"   {len(vehicle_types) + 1}. ALL (scrape everything)")
    print(f"   {len(vehicle_types) + 2}. Exit")
    
    try:
        choice = int(input("\n👉 Enter choice: ").strip())
        
        if 1 <= choice <= len(vehicle_types):
            vt = vehicle_types[choice - 1]
            pages = int(input("Pages per category (1-2, default 1): ") or "1")
            scrape_by_vehicle_type(vt, pages)
            
        elif choice == len(vehicle_types) + 1:
            pages = int(input("Pages per category (1-2, default 1): ") or "1")
            total = 0
            for vt in vehicle_types:
                total += scrape_by_vehicle_type(vt, pages)
                time.sleep(15)
            print(f"\n🎉 TOTAL VEHICLES COLLECTED: {total}")
            
        elif choice == len(vehicle_types) + 2:
            print("Goodbye!")
            
    except ValueError:
        print("Invalid input")

if __name__ == "__main__":
    main()