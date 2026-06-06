# interactive_scraper.py
# Interactive category selector for Riyasewana scraper

import json
from typing import Dict, List
from config_categories import CATEGORIES_CONFIG


class InteractiveCategorySelector:
    def __init__(self):
        self.categories = CATEGORIES_CONFIG
    
    def show_menu(self):
        """Display interactive menu"""
        print("\n" + "=" * 70)
        print("🚗 VEHICLE CATEGORY SELECTOR")
        print("=" * 70)
        
        # Group by brand
        brands = {}
        for cat_name, config in self.categories.items():
            brand = cat_name.split('_')[0]
            if brand not in brands:
                brands[brand] = []
            brands[brand].append((cat_name, config))
        
        # Display brands
        brand_list = list(brands.keys())
        for idx, brand in enumerate(brand_list, 1):
            enabled_count = sum(1 for _, cfg in brands[brand] if cfg.get('enabled', True))
            total_count = len(brands[brand])
            print(f"{idx}. {brand} ({enabled_count}/{total_count} enabled)")
        
        print(f"{len(brand_list) + 1}. Custom Category")
        print(f"{len(brand_list) + 2}. Run ALL enabled categories")
        print(f"{len(brand_list) + 3}. Exit")
        
        return brands, brand_list
    
    def show_brand_categories(self, brand, categories):
        """Show categories for selected brand"""
        print(f"\n{'=' * 60}")
        print(f"📋 {brand} CATEGORIES")
        print(f"{'=' * 60}")
        
        for idx, (cat_name, config) in enumerate(categories, 1):
            status = "✅ ENABLED" if config.get('enabled', True) else "❌ DISABLED"
            pages = config.get('pages', 3)
            print(f"{idx:2}. {cat_name:25} [{status}] - {pages} pages")
        
        print(f"{len(categories) + 1}. Back to main menu")
        print(f"{len(categories) + 2}. Select all in {brand}")
        
        return len(categories)
    
    def get_custom_category(self):
        """Get custom category from user"""
        print("\n🔧 CUSTOM CATEGORY")
        print("-" * 40)
        
        make = input("Enter make (e.g., toyota, suzuki, nissan): ").strip().lower()
        model = input("Enter model (e.g., vit, corolla, alto): ").strip().lower()
        pages = int(input("Number of pages to scrape (1-10): "))
        
        # Optional parameters
        print("\nOptional parameters (press Enter to skip):")
        year_from = input("Year from (e.g., 2010): ").strip() or "2010"
        year_to = input("Year to (e.g., 2020): ").strip() or "2020"
        fuel = input("Fuel (petrol/diesel/electric): ").strip().lower() or "petrol"
        transmission = input("Transmission (automatic/manual): ").strip().lower() or "automatic"
        condition = input("Condition (registered/unregistered): ").strip().lower() or "registered"
        
        category_name = f"{make.capitalize()}_{model.capitalize()}"
        
        return {
            category_name: {
                "params": {
                    "make": make,
                    "model": model,
                    "year_from": year_from,
                    "year_to": year_to,
                    "fuel": fuel,
                    "transmission": transmission,
                    "condition": condition
                },
                "pages": pages,
                "enabled": True
            }
        }
    
    def get_selected_categories(self):
        """Get user selected categories"""
        brands, brand_list = self.show_menu()
        
        selected_categories = {}
        
        while True:
            try:
                choice = int(input("\n👉 Enter your choice: "))
                
                if 1 <= choice <= len(brand_list):
                    # Selected a brand
                    brand = brand_list[choice - 1]
                    brand_cats = brands[brand]
                    total = self.show_brand_categories(brand, brand_cats)
                    
                    cat_choice = int(input("\n👉 Select category: "))
                    
                    if 1 <= cat_choice <= len(brand_cats):
                        # Select specific category
                        cat_name, config = brand_cats[cat_choice - 1]
                        if config.get('enabled', True):
                            selected_categories[cat_name] = config
                            print(f"✅ Added: {cat_name}")
                        else:
                            print(f"⚠️ {cat_name} is disabled. Enable in config first.")
                    
                    elif cat_choice == len(brand_cats) + 1:
                        # Back to main menu
                        continue
                    
                    elif cat_choice == len(brand_cats) + 2:
                        # Select all in brand
                        for cat_name, config in brand_cats:
                            if config.get('enabled', True):
                                selected_categories[cat_name] = config
                                print(f"✅ Added: {cat_name}")
                        print(f"\n📊 Added all enabled categories from {brand}")
                    
                    else:
                        print("❌ Invalid choice")
                
                elif choice == len(brand_list) + 1:
                    # Custom category
                    custom = self.get_custom_category()
                    selected_categories.update(custom)
                    print(f"✅ Added custom category")
                
                elif choice == len(brand_list) + 2:
                    # Run all enabled
                    for cat_name, config in self.categories.items():
                        if config.get('enabled', True):
                            selected_categories[cat_name] = config
                    print(f"✅ Added all enabled categories ({len(selected_categories)} total)")
                    break
                
                elif choice == len(brand_list) + 3:
                    # Exit
                    break
                
                # Ask if want to add more
                if selected_categories:
                    more = input("\nAdd more categories? (y/n): ").strip().lower()
                    if more != 'y':
                        break
                    
            except ValueError:
                print("❌ Please enter a valid number")
                continue
        
        return selected_categories
    
    def save_selection(self, selected_categories, filename="selected_categories.json"):
        """Save selected categories to file for later use"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(selected_categories, f, indent=2, ensure_ascii=False)
        print(f"\n💾 Selection saved to {filename}")
    
    def load_selection(self, filename="selected_categories.json"):
        """Load previously saved selection"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return None


# For direct testing
if __name__ == "__main__":
    selector = InteractiveCategorySelector()
    selected = selector.get_selected_categories()
    
    print("\n" + "=" * 60)
    print("📋 SELECTED CATEGORIES:")
    print("=" * 60)
    for cat_name, config in selected.items():
        print(f"  - {cat_name} ({config.get('pages', 3)} pages)")
    
    if selected:
        selector.save_selection(selected)