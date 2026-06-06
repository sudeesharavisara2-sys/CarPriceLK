# config_categories.py
# Vehicle categories configuration for Riyasewana scraper

CATEGORIES_CONFIG = {
    # ============= TOYOTA =============
    "Toyota_Camry": {
        "params": {
            "make": "toyota",
            "model": "camry",
            "year_from": "2010",
            "year_to": "2020",
            "fuel": "petrol",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 3,
        "enabled": True
    },
    
    "Toyota_Rav4": {
        "params": {
            "make": "toyota",
            "model": "rav4",
            "year_from": "2010",
            "year_to": "2020",
            "fuel": "petrol",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 3,
        "enabled": True
    },
    
    "Toyota_Hilux": {
        "params": {
            "make": "toyota",
            "model": "hilux",
            "year_from": "2010",
            "year_to": "2020",
            "fuel": "diesel",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 3,
        "enabled": True
    },
    
    "Toyota_LandCruiser": {
        "params": {
            "make": "toyota",
            "model": "landcruiser",
            "year_from": "2010",
            "year_to": "2020",
            "fuel": "diesel",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 2,
        "enabled": False
    },
    
    # ============= SUZUKI =============
    "Suzuki_Alto": {
        "params": {
            "make": "suzuki",
            "model": "alto",
            "year_from": "2015",
            "year_to": "2023",
            "fuel": "petrol",
            "transmission": "manual",
            "condition": "registered"
        },
        "pages": 4,
        "enabled": True
    },
    
    "Suzuki_WagonR": {
        "params": {
            "make": "suzuki",
            "model": "wagonr",
            "year_from": "2015",
            "year_to": "2023",
            "fuel": "petrol",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 4,
        "enabled": True
    },
    
    "Suzuki_Swift": {
        "params": {
            "make": "suzuki",
            "model": "swift",
            "year_from": "2010",
            "year_to": "2020",
            "fuel": "petrol",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 3,
        "enabled": True
    },
    
    "Suzuki_Every": {
        "params": {
            "make": "suzuki",
            "model": "every",
            "year_from": "2015",
            "year_to": "2023",
            "fuel": "petrol",
            "transmission": "manual",
            "condition": "registered"
        },
        "pages": 2,
        "enabled": False
    },
    
    # ============= NISSAN =============
    "Nissan_March": {
        "params": {
            "make": "nissan",
            "model": "march",
            "year_from": "2010",
            "year_to": "2020",
            "fuel": "petrol",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 3,
        "enabled": True
    },
    
    "Nissan_Sunny": {
        "params": {
            "make": "nissan",
            "model": "sunny",
            "year_from": "2010",
            "year_to": "2018",
            "fuel": "petrol",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 3,
        "enabled": True
    },
    
    "Nissan_XTrail": {
        "params": {
            "make": "nissan",
            "model": "xtrail",
            "year_from": "2010",
            "year_to": "2020",
            "fuel": "petrol",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 2,
        "enabled": True
    },
    
    "Nissan_Leaf": {
        "params": {
            "make": "nissan",
            "model": "leaf",
            "year_from": "2015",
            "year_to": "2023",
            "fuel": "electric",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 2,
        "enabled": False
    },
    
    # ============= HONDA =============
    "Honda_Vezel": {
        "params": {
            "make": "honda",
            "model": "vezel",
            "year_from": "2013",
            "year_to": "2020",
            "fuel": "petrol",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 4,
        "enabled": True
    },
    
    "Honda_Fit": {
        "params": {
            "make": "honda",
            "model": "fit",
            "year_from": "2010",
            "year_to": "2020",
            "fuel": "petrol",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 3,
        "enabled": True
    },
    
    "Honda_Grace": {
        "params": {
            "make": "honda",
            "model": "grace",
            "year_from": "2014",
            "year_to": "2020",
            "fuel": "petrol",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 3,
        "enabled": True
    },
    
    "Honda_CRV": {
        "params": {
            "make": "honda",
            "model": "crv",
            "year_from": "2010",
            "year_to": "2020",
            "fuel": "petrol",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 2,
        "enabled": True
    },
    
    # ============= MITSUBISHI =============
    "Mitsubishi_Lancer": {
        "params": {
            "make": "mitsubishi",
            "model": "lancer",
            "year_from": "2010",
            "year_to": "2018",
            "fuel": "petrol",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 2,
        "enabled": True
    },
    
    "Mitsubishi_Pajero": {
        "params": {
            "make": "mitsubishi",
            "model": "pajero",
            "year_from": "2010",
            "year_to": "2020",
            "fuel": "diesel",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 2,
        "enabled": False
    },
    
    # ============= HYUNDAI =============
    "Hyundai_Santro": {
        "params": {
            "make": "hyundai",
            "model": "santro",
            "year_from": "2015",
            "year_to": "2023",
            "fuel": "petrol",
            "transmission": "manual",
            "condition": "registered"
        },
        "pages": 3,
        "enabled": True
    },
    
    "Hyundai_Elantra": {
        "params": {
            "make": "hyundai",
            "model": "elantra",
            "year_from": "2010",
            "year_to": "2020",
            "fuel": "petrol",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 2,
        "enabled": True
    },
    
    "Hyundai_Grand_i10": {
        "params": {
            "make": "hyundai",
            "model": "grandi10",
            "year_from": "2014",
            "year_to": "2020",
            "fuel": "petrol",
            "transmission": "manual",
            "condition": "registered"
        },
        "pages": 3,
        "enabled": True
    },
    
    # ============= PERODUA =============
    "Perodua_Axia": {
        "params": {
            "make": "perodua",
            "model": "axia",
            "year_from": "2014",
            "year_to": "2023",
            "fuel": "petrol",
            "transmission": "manual",
            "condition": "registered"
        },
        "pages": 3,
        "enabled": True
    },
    
    "Perodua_Bezza": {
        "params": {
            "make": "perodua",
            "model": "bezza",
            "year_from": "2016",
            "year_to": "2023",
            "fuel": "petrol",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 3,
        "enabled": True
    },
    
    # ============= BMW (Premium - Disabled by default) =============
    "BMW_3Series": {
        "params": {
            "make": "bmw",
            "model": "3series",
            "year_from": "2010",
            "year_to": "2020",
            "fuel": "petrol",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 2,
        "enabled": False
    },
    
    "BMW_5Series": {
        "params": {
            "make": "bmw",
            "model": "5series",
            "year_from": "2010",
            "year_to": "2020",
            "fuel": "petrol",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 2,
        "enabled": False
    },
    
    # ============= MERCEDES (Premium - Disabled by default) =============
    "Mercedes_CEclass": {
        "params": {
            "make": "mercedes",
            "model": "cclass",
            "year_from": "2010",
            "year_to": "2020",
            "fuel": "petrol",
            "transmission": "automatic",
            "condition": "registered"
        },
        "pages": 2,
        "enabled": False
    }
}