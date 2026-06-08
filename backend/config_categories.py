# config_categories.py
# Vehicle categories configuration for Riyasewana scraper - CORRECTED

CATEGORIES_CONFIG = {
    # =========================================================
    # 1. BUSES (Using /search/buses)
    # =========================================================
    "Ashok_Leyland_Bus": {
        "params": {
            "make": "ashok-leyland",
        },
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Bus"
    },
    "Toyota_Coaster_Bus": {
        "params": {
            "make": "toyota",
            "model": "coaster",
        },
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Bus"
    },
    "Nissan_Civilian_Bus": {
        "params": {
            "make": "nissan",
            "model": "civilian",
        },
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Bus"
    },
    "Mitsubishi_Rosa_Bus": {
        "params": {
            "make": "mitsubishi",
            "model": "rosa",
        },
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Bus"
    },
    "Tata_Bus": {
        "params": {
            "make": "tata",
        },
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Bus"
    },
    
    # =========================================================
    # 2. LORRIES (Using /search/lorries)
    # =========================================================
    "Tata_Lorry": {
        "params": {
            "make": "tata",
        },
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Lorry"
    },
    "Isuzu_Lorry": {
        "params": {
            "make": "isuzu",
        },
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Lorry"
    },
    "Daihatsu_Lorry": {
        "params": {
            "make": "daihatsu",
        },
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Lorry"
    },
    "Nissan_Lorry": {
        "params": {
            "make": "nissan",
        },
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Lorry"
    },
    "Mahindra_Lorry": {
        "params": {
            "make": "mahindra",
        },
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Lorry"
    },
    
    # =========================================================
    # 3. VANS (Using /search/vans)
    # =========================================================
    "Toyota_Hiace_Van": {
        "params": {
            "make": "toyota",
            "model": "hiace",
        },
        "pages": 3,
        "enabled": True,
        "vehicle_type": "Van"
    },
    "Nissan_Caravan_Van": {
        "params": {
            "make": "nissan",
            "model": "caravan",
        },
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Van"
    },
    "Suzuki_Every_Van": {
        "params": {
            "make": "suzuki",
            "model": "every",
        },
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Van"
    },
    "Mitsubishi_Delica_Van": {
        "params": {
            "make": "mitsubishi",
            "model": "delica",
        },
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Van"
    },
    
    # =========================================================
    # 4. CARS (Using /search/cars)
    # =========================================================
    "Toyota_Prius": {
        "params": {"make": "toyota", "model": "prius"},
        "pages": 3,
        "enabled": True,
        "vehicle_type": "Car"
    },
    "Toyota_Camry": {
        "params": {"make": "toyota", "model": "camry"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Car"
    },
    "Toyota_Vitz": {
        "params": {"make": "toyota", "model": "vitz"},
        "pages": 3,
        "enabled": True,
        "vehicle_type": "Car"
    },
    "Toyota_Corolla": {
        "params": {"make": "toyota", "model": "corolla"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Car"
    },
    "Suzuki_Alto": {
        "params": {"make": "suzuki", "model": "alto"},
        "pages": 3,
        "enabled": True,
        "vehicle_type": "Car"
    },
    "Suzuki_WagonR": {
        "params": {"make": "suzuki", "model": "wagonr"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Car"
    },
    "Suzuki_Swift": {
        "params": {"make": "suzuki", "model": "swift"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Car"
    },
    "Honda_Vezel": {
        "params": {"make": "honda", "model": "vezel"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Car"
    },
    "Honda_Fit": {
        "params": {"make": "honda", "model": "fit"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Car"
    },
    "Nissan_March": {
        "params": {"make": "nissan", "model": "march"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Car"
    },
    "Nissan_Sunny": {
        "params": {"make": "nissan", "model": "sunny"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Car"
    },
    "Hyundai_Santro": {
        "params": {"make": "hyundai", "model": "santro"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Car"
    },
    "Perodua_Axia": {
        "params": {"make": "perodua", "model": "axia"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Car"
    },
    
    # =========================================================
    # 5. MOTORCYCLES (Using /search/motorcycles)
    # =========================================================
    "Honda_Motorcycle": {
        "params": {"make": "honda"},
        "pages": 3,
        "enabled": True,
        "vehicle_type": "Motorcycle"
    },
    "Yamaha_Motorcycle": {
        "params": {"make": "yamaha"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Motorcycle"
    },
    "Suzuki_Motorcycle": {
        "params": {"make": "suzuki"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Motorcycle"
    },
    "Bajaj_Motorcycle": {
        "params": {"make": "bajaj"},
        "pages": 3,
        "enabled": True,
        "vehicle_type": "Motorcycle"
    },
    "TVS_Motorcycle": {
        "params": {"make": "tvs"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Motorcycle"
    },
    "Hero_Motorcycle": {
        "params": {"make": "hero"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Motorcycle"
    },
    
    # =========================================================
    # 6. SUVs (Using /search/cars with SUV makes)
    # =========================================================
    "Toyota_Rav4": {
        "params": {"make": "toyota", "model": "rav4"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "SUV"
    },
    "Toyota_LandCruiser": {
        "params": {"make": "toyota", "model": "landcruiser"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "SUV"
    },
    "Honda_CRV": {
        "params": {"make": "honda", "model": "crv"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "SUV"
    },
    "Mitsubishi_Pajero": {
        "params": {"make": "mitsubishi", "model": "pajero"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "SUV"
    },
    "Suzuki_Jimny": {
        "params": {"make": "suzuki", "model": "jimny"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "SUV"
    },
    
    # =========================================================
    # 7. PICKUP (Using /search/pickup)
    # =========================================================
    "Toyota_Hilux": {
        "params": {"make": "toyota", "model": "hilux"},
        "pages": 3,
        "enabled": True,
        "vehicle_type": "Pickup"
    },
    "Nissan_Navara": {
        "params": {"make": "nissan", "model": "navara"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Pickup"
    },
    "Mitsubishi_L200": {
        "params": {"make": "mitsubishi", "model": "l200"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Pickup"
    },
    
    # =========================================================
    # 8. THREE WHEEL (Using /search/three-wheelers)
    # =========================================================
    "Bajaj_ThreeWheel": {
        "params": {"make": "bajaj"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "ThreeWheel"
    },
    "TVS_ThreeWheel": {
        "params": {"make": "tvs"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "ThreeWheel"
    },
    
    # =========================================================
    # 9. CREW CAB (Using /search/crew-cab)
    # =========================================================
    "Toyota_CrewCab": {
        "params": {"make": "toyota"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "CrewCab"
    },
    
    # =========================================================
    # 10. TRACTOR (Using /search/tractors)
    # =========================================================
    "Mahindra_Tractor": {
        "params": {"make": "mahindra"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Tractor"
    },
    "JohnDeere_Tractor": {
        "params": {"make": "john deere"},
        "pages": 2,
        "enabled": True,
        "vehicle_type": "Tractor"
    },
}