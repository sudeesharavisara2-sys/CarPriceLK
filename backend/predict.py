"""
predict.py
CarPriceLK — Price Predictor (Updated with Fuel & Transmission)

Loads trained model and predicts market value for a given vehicle.

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
    model            = joblib.load(os.path.join(MODEL_DIR, "price_model.pkl"))
    le_make          = joblib.load(os.path.join(MODEL_DIR, "encoder_make.pkl"))
    le_model         = joblib.load(os.path.join(MODEL_DIR, "encoder_model.pkl"))
    le_fuel          = joblib.load(os.path.join(MODEL_DIR, "encoder_fuel.pkl"))
    le_trans         = joblib.load(os.path.join(MODEL_DIR, "encoder_transmission.pkl"))
    le_vehicle_type = joblib.load(os.path.join(MODEL_DIR, "encoder_vehicle_type.pkl"))
    with open(os.path.join(MODEL_DIR, "model_meta.json")) as f:
        meta = json.load(f)
    return model, le_make, le_model, le_fuel, le_trans, le_vehicle_type, meta


def predict_price(make: str, model_name: str, year: int, mileage: int,
                  fuel_type: str = "petrol", transmission: str = "automatic",
                  vehicle_type: str = "Car") -> dict:
    """
    Predict the market price of a vehicle.
    """
    (rf_model, le_make, le_model, le_fuel, le_trans, le_vehicle_type, meta) = load_artifacts()

    # Clean inputs and strip spaces
    input_make = str(make).strip()
    input_model = str(model_name).strip()
    input_fuel = str(fuel_type).strip()
    input_trans = str(transmission).strip()
    input_vtype = str(vehicle_type).strip()

    # FIX: Match case-insensitively with Encoder Classes
    matched_make = next((c for c in le_make.classes_ if c.lower() == input_make.lower()), None)
    matched_model = next((c for c in le_model.classes_ if c.lower() == input_model.lower()), None)
    matched_fuel = next((c for c in le_fuel.classes_ if c.lower() == input_fuel.lower()), None)
    matched_trans = next((c for c in le_trans.classes_ if c.lower() == input_trans.lower()), None)
    matched_vtype = next((c for c in le_vehicle_type.classes_ if c.lower() == input_vtype.lower()), None)

    # Validate strictly against mapped elements
    if not matched_make:
        return {"error": f"Unknown make '{input_make}'. Supported: {list(le_make.classes_)}"}
    if not matched_model:
        return {"error": f"Unknown model '{input_model}'. Supported: {list(le_model.classes_)}"}
    if not matched_fuel:
        return {"error": f"Unknown fuel type '{input_fuel}'. Supported: {list(le_fuel.classes_)}"}
    if not matched_trans:
        return {"error": f"Unknown transmission '{input_trans}'. Supported: {list(le_trans.classes_)}"}
    if not matched_vtype:
        return {"error": f"Unknown vehicle type '{input_vtype}'. Supported: {list(le_vehicle_type.classes_)}"}

    car_age   = 2026 - year
    make_enc  = le_make.transform([matched_make])[0]
    model_enc = le_model.transform([matched_model])[0]
    fuel_enc  = le_fuel.transform([matched_fuel])[0]
    trans_enc = le_trans.transform([matched_trans])[0]
    vehicle_type_enc = le_vehicle_type.transform([matched_vtype])[0]

    features = meta["features"]
    row = pd.DataFrame([{
        "make_enc":         make_enc,
        "model_enc":        model_enc,
        "vehicle_type_enc": vehicle_type_enc,
        "fuel_enc":         fuel_enc,
        "trans_enc":        trans_enc,
        "year":             year,
        "car_age":          car_age,
        "mileage":          mileage,
    }])[features]

    # Each tree gives a separate prediction
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
        "make":            matched_make,
        "model":           matched_model,
        "year":            year,
        "mileage_km":      mileage,
        "fuel_type":       matched_fuel,
        "transmission":    matched_trans,
        "vehicle_type":    matched_vtype,
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
        f"\n{'─'*50}\n"
        f"  {result['make']} {result['model']} {result['year']}\n"
        f"  {result['mileage_km']:,} km  |  {result['fuel_type']}  |  {result['transmission']}\n"
        f"  {result['vehicle_type']}\n"
        f"{'─'*50}\n"
        f"  Estimated price : Rs. {result['predicted_price']:>12,.0f}\n"
        f"  Market range    : Rs. {result['range_low']:>12,.0f}\n"
        f"                  – Rs. {result['range_high']:>12,.0f}\n"
        f"  Verdict         : {result['verdict']}\n"
        f"{'─'*50}\n"
        f"  Model accuracy  : R² {result['model_r2']}  |  "
        f"±Rs.{result['model_mae']:,} avg error\n"
    )


if __name__ == "__main__":
    print("=" * 50)
    print("  CarPriceLK — Price Predictor")
    print("  (Supports: Cars, Vans, Buses, SUVs, Jeeps, Lorries)")
    print("=" * 50)

    _, le_make, le_model, le_fuel, le_trans, le_vehicle_type, meta = load_artifacts()

    print(f"\nSupported makes  : {', '.join(meta['makes'][:10])}...")
    print(f"Supported fuel types: {', '.join(meta['fuel_types'])}")
    print(f"Supported transmissions: {', '.join(meta['transmissions'])}")
    print(f"Supported vehicle types: {', '.join(meta['vehicle_types'])}")

    print("\nEnter vehicle details:")
    make         = input("  Make    (e.g., toyota): ").strip()
    model_name   = input("  Model   (e.g., prius): ").strip()
    vehicle_type = input("  Type    (Car/Van/Bus/SUV/Jeep/Lorry): ").strip()
    year         = int(input("  Year    (e.g., 2015): ").strip())
    mileage      = int(input("  Mileage km (e.g., 100000): ").strip())
    fuel_type    = input("  Fuel    (petrol/diesel/hybrid/electric): ").strip()
    transmission = input("  Gear    (automatic/manual): ").strip()

    result = predict_price(
        make=make,
        model_name=model_name,
        year=year,
        mileage=mileage,
        fuel_type=fuel_type,
        transmission=transmission,
        vehicle_type=vehicle_type
    )

    print(format_result(result))