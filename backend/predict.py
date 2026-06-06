"""
predict.py
CarPriceLK — Price Predictor

Loads trained model and predicts market value for a given vehicle.
Later this becomes the FastAPI endpoint.

Usage:
    python predict.py
    or import predict_price() into your API.
"""

import json
import os
import numpy as np
import pandas as pd
import joblib


MODEL_DIR = os.path.join(os.path.dirname(__file__), "model")


def load_artifacts():
    model    = joblib.load(os.path.join(MODEL_DIR, "price_model.pkl"))
    le_make  = joblib.load(os.path.join(MODEL_DIR, "encoder_make.pkl"))
    le_model = joblib.load(os.path.join(MODEL_DIR, "encoder_model.pkl"))
    with open(os.path.join(MODEL_DIR, "model_meta.json")) as f:
        meta = json.load(f)
    return model, le_make, le_model, meta


def predict_price(make: str, model_name: str, year: int,
                  mileage: int, is_colombo: bool = False) -> dict:
    """
    Predict the market price of a vehicle.

    Args:
        make        : e.g. "toyota", "suzuki", "honda"
        model_name  : e.g. "prius", "alto", "vezel"
        year        : manufacture year e.g. 2015
        mileage     : km reading e.g. 100000
        is_colombo  : True if location is Colombo district

    Returns:
        dict with predicted price, range, and confidence band
    """
    rf_model, le_make, le_model, meta = load_artifacts()

    make       = make.lower().strip()
    model_name = model_name.lower().strip()

    # Validate
    if make not in le_make.classes_:
        return {"error": f"Unknown make '{make}'. Supported: {list(le_make.classes_)}"}
    if model_name not in le_model.classes_:
        return {"error": f"Unknown model '{model_name}'. Supported: {list(le_model.classes_)}"}

    car_age   = 2026 - year
    make_enc  = le_make.transform([make])[0]
    model_enc = le_model.transform([model_name])[0]

    features = meta["features"]
    row = pd.DataFrame([{
        "make_enc":   make_enc,
        "model_enc":  model_enc,
        "year":       year,
        "car_age":    car_age,
        "mileage":    mileage,
        "is_colombo": int(is_colombo),
    }])[features]

    # Each tree gives a separate prediction (use numpy array to avoid feature-name warnings)
    row_np = row.to_numpy()
    tree_preds = np.array([tree.predict(row_np)[0] for tree in rf_model.estimators_])
    predicted  = float(np.mean(tree_preds))
    low        = float(np.percentile(tree_preds, 15))
    high       = float(np.percentile(tree_preds, 85))

    mae = meta["mae_lkr"]

    # Verdict
    if predicted < low + (high - low) * 0.3:
        verdict = "Low end of market"
    elif predicted > high - (high - low) * 0.3:
        verdict = "High end of market"
    else:
        verdict = "Mid market"

    return {
        "make":           make.capitalize(),
        "model":          model_name.capitalize(),
        "year":           year,
        "mileage_km":     mileage,
        "location":       "Colombo area" if is_colombo else "Outside Colombo",
        "predicted_price": round(predicted / 1000) * 1000,
        "range_low":       round(low / 1000) * 1000,
        "range_high":      round(high / 1000) * 1000,
        "model_mae":       mae,
        "verdict":         verdict,
        "model_r2":        meta["r2_score"],
    }


def format_result(result: dict) -> str:
    if "error" in result:
        return f"Error: {result['error']}"

    return (
        f"\n{'─'*45}\n"
        f"  {result['make']} {result['model']} {result['year']}\n"
        f"  {result['mileage_km']:,} km  |  {result['location']}\n"
        f"{'─'*45}\n"
        f"  Estimated price : Rs. {result['predicted_price']:>12,.0f}\n"
        f"  Market range    : Rs. {result['range_low']:>12,.0f}\n"
        f"                  – Rs. {result['range_high']:>12,.0f}\n"
        f"  Verdict         : {result['verdict']}\n"
        f"{'─'*45}\n"
        f"  Model accuracy  : R² {result['model_r2']}  |  "
        f"±Rs.{result['model_mae']:,} avg error\n"
    )


if __name__ == "__main__":
    print("=" * 45)
    print("  CarPriceLK — Price Predictor")
    print("=" * 45)

    # Interactive mode
    _, le_make, le_model, meta = load_artifacts()

    print(f"\nSupported makes  : {', '.join(meta['makes'])}")
    print(f"Supported models : {', '.join(meta['models'])}")

    print("\nEnter vehicle details:")
    make       = input("  Make   (e.g. toyota): ").strip().lower()
    model_name = input("  Model  (e.g. prius):  ").strip().lower()
    year       = int(input("  Year   (e.g. 2015):   ").strip())
    mileage    = int(input("  Mileage km (e.g. 100000): ").strip())
    location   = input("  Colombo area? (y/n): ").strip().lower()

    result = predict_price(
        make=make,
        model_name=model_name,
        year=year,
        mileage=mileage,
        is_colombo=(location == "y")
    )

    print(format_result(result))