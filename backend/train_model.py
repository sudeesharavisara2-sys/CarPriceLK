"""
train_model.py
CarPriceLK — ML Model Trainer

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

COLOMBO_AREA = {
    "colombo", "nugegoda", "dehiwala", "maharagama", "kotte",
    "rajagiriya", "battaramulla", "kelaniya", "malabe", "kaduwela",
    "athurugiriya", "hokandara", "boralesgamuwa", "moratuwa",
    "dehiwala-mt", "mount lavinia", "ratmalana", "wellampitiya",
}

def clean_data(records):
    df = pd.DataFrame(records)

    # Drop rows with no valid price
    df = df[df["cleaned_price"] > 500_000].copy()

    # Remove extreme outliers (price > 30M or < 1M likely junk)
    df = df[(df["cleaned_price"] >= 1_000_000) & (df["cleaned_price"] <= 30_000_000)]

    # Year → numeric, drop N/A
    df = df[df["year"] != "N/A"]
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)

    # Keep only reasonable years (1990–2026)
    df = df[(df["year"] >= 1990) & (df["year"] <= 2026)]

    # Mileage: 0 means unknown — replace with median per category
    df["mileage"] = df["mileage"].replace(0, np.nan)
    df["mileage"] = df.groupby("category")["mileage"].transform(
        lambda x: x.fillna(x.median())
    )
    df["mileage"] = df["mileage"].fillna(df["mileage"].median())

    # Car age feature
    df["car_age"] = 2026 - df["year"]

    # Location: is it Colombo area?
    df["is_colombo"] = df["location"].str.lower().apply(
        lambda loc: 1 if any(area in loc for area in COLOMBO_AREA) else 0
    )

    # Extract make and model from category  (e.g. "Toyota_Prius" → "toyota", "prius")
    df["make"] = df["category"].str.split("_").str[0].str.lower()
    df["model"] = df["category"].str.split("_").str[1].str.lower()

    print(f"After cleaning: {len(df)} usable records")
    print(f"  Price range: Rs.{df['cleaned_price'].min():,.0f} – Rs.{df['cleaned_price'].max():,.0f}")
    print(f"  Year range:  {df['year'].min()} – {df['year'].max()}")
    print(f"  Makes: {sorted(df['make'].unique())}")

    return df


# ─────────────────────────────────────────────
# 3. ENCODE CATEGORICAL FEATURES
# ─────────────────────────────────────────────

def encode_features(df):
    le_make  = LabelEncoder()
    le_model = LabelEncoder()

    df = df.copy()
    df["make_enc"]  = le_make.fit_transform(df["make"])
    df["model_enc"] = le_model.fit_transform(df["model"])

    features = ["make_enc", "model_enc", "year", "car_age", "mileage", "is_colombo"]
    X = df[features]
    y = df["cleaned_price"]

    return X, y, le_make, le_model, features


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
        print(f"  {feat:<15} {bar} {imp:.3f}")

    return model, mae, r2


# ─────────────────────────────────────────────
# 5. SAVE MODEL ARTIFACTS
# ─────────────────────────────────────────────

def save_model(model, le_make, le_model, features, mae, r2, output_dir="."):
    os.makedirs(output_dir, exist_ok=True)

    joblib.dump(model,    os.path.join(output_dir, "price_model.pkl"))
    joblib.dump(le_make,  os.path.join(output_dir, "encoder_make.pkl"))
    joblib.dump(le_model, os.path.join(output_dir, "encoder_model.pkl"))

    meta = {
        "features": features,
        "mae_lkr":  round(mae),
        "r2_score": round(r2, 4),
        "makes":    list(le_make.classes_),
        "models":   list(le_model.classes_),
        "trained_on": "2026-06-06",
    }
    with open(os.path.join(output_dir, "model_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\nSaved to '{output_dir}/':")
    print("  price_model.pkl   — trained RandomForest")
    print("  encoder_make.pkl  — make label encoder")
    print("  encoder_model.pkl — model label encoder")
    print("  model_meta.json   — metadata + accuracy info")


# ─────────────────────────────────────────────
# 6. QUICK TEST PREDICTION
# ─────────────────────────────────────────────

def test_prediction(model, le_make, le_model, features):
    print("\n--- Quick prediction tests ---")

    test_cases = [
        {"make": "toyota", "model": "prius",  "year": 2014, "mileage": 150000, "is_colombo": 1},
        {"make": "suzuki", "model": "alto",   "year": 2019, "mileage": 40000,  "is_colombo": 0},
        {"make": "honda",  "model": "vezel",  "year": 2016, "mileage": 80000,  "is_colombo": 1},
        {"make": "toyota", "model": "vit",    "year": 2013, "mileage": 100000, "is_colombo": 0},
    ]

    for tc in test_cases:
        try:
            make_enc  = le_make.transform([tc["make"]])[0]
            model_enc = le_model.transform([tc["model"]])[0]
            car_age   = 2026 - tc["year"]

            row = pd.DataFrame([{
                "make_enc":   make_enc,
                "model_enc":  model_enc,
                "year":       tc["year"],
                "car_age":    car_age,
                "mileage":    tc["mileage"],
                "is_colombo": tc["is_colombo"],
            }])[features]

            predicted = model.predict(row)[0]
            print(f"  {tc['make'].capitalize()} {tc['model'].capitalize()} {tc['year']} "
                  f"({tc['mileage']:,} km) → Rs. {predicted:,.0f}")
        except Exception as e:
            print(f"  Skipped {tc}: {e}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 55)
    print("  CarPriceLK — ML Model Trainer")
    print("=" * 55)

    records          = load_all_data(data_dir=".")
    df               = clean_data(records)
    X, y, le_make, le_model, features = encode_features(df)
    model, mae, r2   = train(X, y)

    save_model(model, le_make, le_model, features, mae, r2, output_dir="model")
    test_prediction(model, le_make, le_model, features)

    print("\nDone. Next step: predict.py or FastAPI endpoint.")