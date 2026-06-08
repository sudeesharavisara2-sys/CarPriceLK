"""
train_model.py
CarPriceLK — ML Model Trainer (Updated with Make & Model from Title)

Loads scraped riyasewana JSON files, cleans data,
trains a RandomForest price prediction model, and saves it.

Usage:
    python train_model.py
"""

import json
import glob
import os
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_absolute_error, r2_score
import joblib


# ─────────────────────────────────────────────
# 1. LOAD ALL JSON DATA
# ─────────────────────────────────────────────

def load_all_data(data_dir="."):
    all_records = []
    skip = {"riyasewana_vehicles.json", "scraping_progress.json"}

    for filepath in glob.glob(os.path.join(data_dir, "riyasewana_*.json")):
        filename = os.path.basename(filepath)
        if filename in skip:
            continue
        with open(filepath, encoding="utf-8") as f:
            records = json.load(f)
        if isinstance(records, list):
            all_records.extend(records)

    print(f"Loaded {len(all_records)} total records from JSON files.")
    return all_records


# ─────────────────────────────────────────────
# 2. CLEAN & ENGINEER FEATURES
# ─────────────────────────────────────────────

def clean_data(records):
    df = pd.DataFrame(records)

    # Drop rows with no valid price
    df = df[df["cleaned_price"] > 500_000].copy()

    # Remove extreme outliers
    df = df[(df["cleaned_price"] >= 500_000) & (df["cleaned_price"] <= 40_000_000)]

    # Year → numeric, drop N/A
    df = df[df["year"] != "N/A"]
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)

    # Keep only reasonable years
    df = df[(df["year"] >= 1990) & (df["year"] <= 2026)]

    # Mileage: 0 means unknown — replace with median
    df["mileage"] = df["mileage"].replace(0, np.nan)
    df["mileage"] = df.groupby("category")["mileage"].transform(
        lambda x: x.fillna(x.median())
    )
    df["mileage"] = df["mileage"].fillna(df["mileage"].median())

    # Car age feature
    df["car_age"] = 2026 - df["year"]

    # Fuel type
    df["fuel_type"] = df["fuel_type"].fillna("unknown")
    df["fuel_type"] = df["fuel_type"].replace(["unknown", ""], "petrol")
    
    # Transmission
    df["transmission"] = df["transmission"].fillna("unknown")
    df["transmission"] = df["transmission"].replace(["unknown", ""], "automatic")

    # Make and Model from title (new fields)
    if "make" in df.columns:
        df["make"] = df["make"].fillna("unknown")
        df["make"] = df["make"].replace(["unknown", ""], "other")
    else:
        # Fallback: extract from category
        df["make"] = df["category"].str.split("_").str[0].str.lower()
    
    if "model" in df.columns:
        df["model"] = df["model"].fillna("unknown")
        df["model"] = df["model"].replace(["unknown", ""], "other")
    else:
        df["model"] = df["category"].str.split("_").str[1].str.lower()

    # Vehicle type
    if "vehicle_type" in df.columns:
        df["vehicle_type"] = df["vehicle_type"].fillna("Car")
    else:
        df["vehicle_type"] = "Car"

    print(f"After cleaning: {len(df)} usable records")
    print(f"  Price range: Rs.{df['cleaned_price'].min():,.0f} – Rs.{df['cleaned_price'].max():,.0f}")
    print(f"  Year range:  {df['year'].min()} – {df['year'].max()}")
    print(f"  Makes: {sorted(df['make'].unique())[:20]}...")
    print(f"  Fuel types: {sorted(df['fuel_type'].unique())}")
    print(f"  Transmissions: {sorted(df['transmission'].unique())}")
    print(f"  Vehicle types: {sorted(df['vehicle_type'].unique())}")

    return df


# ─────────────────────────────────────────────
# 3. ENCODE CATEGORICAL FEATURES
# ─────────────────────────────────────────────

def encode_features(df):
    le_make       = LabelEncoder()
    le_model      = LabelEncoder()
    le_fuel       = LabelEncoder()
    le_trans      = LabelEncoder()
    le_vehicle_type = LabelEncoder()

    df = df.copy()
    df["make_enc"]        = le_make.fit_transform(df["make"])
    df["model_enc"]       = le_model.fit_transform(df["model"])
    df["fuel_enc"]        = le_fuel.fit_transform(df["fuel_type"])
    df["trans_enc"]       = le_trans.fit_transform(df["transmission"])
    df["vehicle_type_enc"] = le_vehicle_type.fit_transform(df["vehicle_type"])

    # Features
    features = [
        "make_enc", "model_enc", "vehicle_type_enc",
        "fuel_enc", "trans_enc", "year", "car_age", "mileage"
    ]
    X = df[features]
    y = df["cleaned_price"]

    return X, y, le_make, le_model, le_fuel, le_trans, le_vehicle_type, features


# ─────────────────────────────────────────────
# 4. TRAIN MODEL
# ─────────────────────────────────────────────

def train(X, y):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Evaluate
    preds = model.predict(X_test)
    mae = mean_absolute_error(y_test, preds)
    r2  = r2_score(y_test, preds)

    print(f"\nModel trained on {len(X_train)} records, tested on {len(X_test)}.")
    print(f"  MAE  (Mean Absolute Error): Rs.{mae:,.0f}")
    print(f"  R²   (Accuracy score):      {r2:.3f}  (1.0 = perfect)")

    # Feature importance
    print("\nFeature importance:")
    for feat, imp in sorted(zip(X.columns, model.feature_importances_), key=lambda x: -x[1]):
        bar = "█" * int(imp * 40)
        print(f"  {feat:<18} {bar} {imp:.3f}")

    return model, mae, r2


# ─────────────────────────────────────────────
# 5. SAVE MODEL ARTIFACTS
# ─────────────────────────────────────────────

def save_model(model, le_make, le_model, le_fuel, le_trans, le_vehicle_type, 
               features, mae, r2, output_dir="model"):
    os.makedirs(output_dir, exist_ok=True)

    joblib.dump(model,           os.path.join(output_dir, "price_model.pkl"))
    joblib.dump(le_make,         os.path.join(output_dir, "encoder_make.pkl"))
    joblib.dump(le_model,        os.path.join(output_dir, "encoder_model.pkl"))
    joblib.dump(le_fuel,         os.path.join(output_dir, "encoder_fuel.pkl"))
    joblib.dump(le_trans,        os.path.join(output_dir, "encoder_transmission.pkl"))
    joblib.dump(le_vehicle_type, os.path.join(output_dir, "encoder_vehicle_type.pkl"))

    meta = {
        "features": features,
        "mae_lkr":  round(mae),
        "r2_score": round(r2, 4),
        "makes":    list(le_make.classes_),
        "models":   list(le_model.classes_),
        "fuel_types": list(le_fuel.classes_),
        "transmissions": list(le_trans.classes_),
        "vehicle_types": list(le_vehicle_type.classes_),
        "trained_on": "2026-06-07",
    }
    with open(os.path.join(output_dir, "model_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\nSaved to '{output_dir}/':")
    print("  price_model.pkl           — trained RandomForest")
    print("  encoder_make.pkl          — make label encoder")
    print("  encoder_model.pkl         — model label encoder")
    print("  encoder_fuel.pkl          — fuel type encoder")
    print("  encoder_transmission.pkl  — transmission encoder")
    print("  encoder_vehicle_type.pkl  — vehicle type encoder")
    print("  model_meta.json           — metadata + accuracy info")


# ─────────────────────────────────────────────
# 6. QUICK TEST PREDICTION
# ─────────────────────────────────────────────

def test_prediction(model, le_make, le_model, le_fuel, le_trans, le_vehicle_type, features):
    print("\n--- Quick prediction tests ---")

    test_cases = [
        {"make": "toyota", "model": "prius",  "year": 2014, "mileage": 150000, 
         "fuel": "petrol", "transmission": "automatic", "vehicle_type": "Car"},
        {"make": "suzuki", "model": "alto",   "year": 2019, "mileage": 40000,  
         "fuel": "petrol", "transmission": "manual", "vehicle_type": "Car"},
        {"make": "honda",  "model": "vezel",  "year": 2016, "mileage": 80000,  
         "fuel": "petrol", "transmission": "automatic", "vehicle_type": "Car"},
        {"make": "ashok leyland", "model": "viking", "year": 2015, "mileage": 120000, 
         "fuel": "diesel", "transmission": "manual", "vehicle_type": "Bus"},
        {"make": "toyota", "model": "hiace",  "year": 2018, "mileage": 100000,
         "fuel": "diesel", "transmission": "manual", "vehicle_type": "Van"},
        {"make": "bajaj",  "model": "pulsar", "year": 2019, "mileage": 30000,
         "fuel": "petrol", "transmission": "manual", "vehicle_type": "Motorcycle"},
    ]

    for tc in test_cases:
        try:
            # Check if make exists in encoder
            if tc["make"] not in le_make.classes_:
                print(f"  ⚠️ Make '{tc['make']}' not in training data, skipping...")
                continue
            
            if tc["model"] not in le_model.classes_:
                print(f"  ⚠️ Model '{tc['model']}' not in training data, skipping...")
                continue
            
            make_enc        = le_make.transform([tc["make"]])[0]
            model_enc       = le_model.transform([tc["model"]])[0]
            fuel_enc        = le_fuel.transform([tc["fuel"]])[0]
            trans_enc       = le_trans.transform([tc["transmission"]])[0]
            vehicle_type_enc = le_vehicle_type.transform([tc["vehicle_type"]])[0]
            car_age         = 2026 - tc["year"]

            row = pd.DataFrame([{
                "make_enc":        make_enc,
                "model_enc":       model_enc,
                "vehicle_type_enc": vehicle_type_enc,
                "fuel_enc":        fuel_enc,
                "trans_enc":       trans_enc,
                "year":            tc["year"],
                "car_age":         car_age,
                "mileage":         tc["mileage"],
            }])[features]

            predicted = model.predict(row)[0]
            print(f"  ✅ {tc['vehicle_type']}: {tc['make'].title()} {tc['model'].title()} {tc['year']} "
                  f"({tc['mileage']:,} km) → Rs. {predicted:,.0f}")
        except Exception as e:
            print(f"  ❌ Skipped {tc}: {e}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  CarPriceLK — ML Model Trainer")
    print("  (Updated: Make & Model from Title Parser)")
    print("=" * 55)

    records          = load_all_data(data_dir=".")
    df               = clean_data(records)
    X, y, le_make, le_model, le_fuel, le_trans, le_vehicle_type, features = encode_features(df)
    model, mae, r2   = train(X, y)

    save_model(model, le_make, le_model, le_fuel, le_trans, le_vehicle_type, 
               features, mae, r2, output_dir="model")
    test_prediction(model, le_make, le_model, le_fuel, le_trans, le_vehicle_type, features)

    print("\nDone. Next step: python app.py")