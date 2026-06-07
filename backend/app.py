"""
app.py
CarPriceLK — Flask REST API

Run:
    python app.py

Endpoints:
    GET  /               → status check
    POST /predict        → price prediction
    GET  /models         → supported makes + models
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from predict import predict_price
import json, os

app = Flask(__name__)
CORS(app)

META_PATH = os.path.join(os.path.dirname(__file__), "model", "model_meta.json")
with open(META_PATH) as f:
    META = json.load(f)


@app.route("/")
def index():
    return jsonify({
        "app":      "CarPriceLK API",
        "status":   "running",
        "accuracy": f"R² {META['r2_score']}",
        "mae_lkr":  META["mae_lkr"],
    })


@app.route("/models")
def get_models():
    return jsonify({
        "makes":  META["makes"],
        "models": META["models"],
    })


@app.route("/predict", methods=["POST"])
def predict():
    body = request.get_json()

    required = ["make", "model", "year", "mileage"]
    for field in required:
        if field not in body:
            return jsonify({"error": f"Missing field: {field}"}), 400

    result = predict_price(
        make        = str(body["make"]).lower().strip(),
        model_name  = str(body["model"]).lower().strip(),
        year        = int(body["year"]),
        mileage     = int(body["mileage"]),
        is_colombo  = bool(body.get("is_colombo", False)),
    )

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result)


if __name__ == "__main__":
    print("=" * 45)
    print("  CarPriceLK API — http://localhost:5000")
    print("=" * 45)
    app.run(debug=True, port=5000)
