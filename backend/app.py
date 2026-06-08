"""
app.py
CarPriceLK — Flask REST API (Case Sensitivity, Normalization Fix & Database Auto-Suggestions)
"""

from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from predict import predict_price
import json
import os
import pymysql  # 👈 Database එක සම්බන්ධ කිරීමට අවශ්‍ය පුස්තකාලය

app = Flask(__name__, template_folder=".")

# Fix CORS for all origins
CORS(app, resources={r"/*": {"origins": "*"}})

META_PATH = os.path.join(os.path.dirname(__file__), "model", "model_meta.json")
with open(META_PATH) as f:
    META = json.load(f)


# 🗄️ Database එක සම්බන්ධ කරන ශ්‍රිතය (Helper function)
def get_db_connection():
    # ⚠️ සටහන: ඔයාගේ local database එකේ username/password මෙහි වෙනස් නම් ඒවා නිවැරදිව සකසන්න.
    return pymysql.connect(
        host='localhost',
        user='root',
        password='',
        database='srilanka_vehicles',
        charset='utf8mb4'
    )


def normalize_make(make: str) -> str:
    """Convert make to correct case for API"""
    make_mapping = {
        'ashok leyland': 'Ashok Leyland',
        'bajaj': 'Bajaj',
        'daihatsu': 'Daihatsu',
        'hero': 'Hero',
        'honda': 'Honda',
        'hyundai': 'Hyundai',
        'isuzu': 'Isuzu',
        'mahindra': 'Mahindra',
        'mitsubishi': 'Mitsubishi',
        'nissan': 'Nissan',
        'nissanette': 'Nissanette',
        'nissaniyer': 'Nissaniyer',
        'perodua': 'Perodua',
        'suzuki': 'Suzuki',
        'tvs': 'TVS',
        'tata': 'Tata',
        'toyota': 'Toyota',
        'yamaha': 'Yamaha'
    }
    make_lower = str(make).lower().strip()
    return make_mapping.get(make_lower, make_lower.title())


def normalize_model(model: str, make: str) -> str:
    """Normalize model name"""
    model_lower = str(model).lower().strip()
    model_mapping = {
        'ct 100': 'CT 100', 'ct100': 'CT 100', 'pulsar': 'Pulsar',
        'discover': 'Discover', 'platina': 'Platina', 'alto': 'Alto',
        'wagonr': 'WagonR', 'wagon r': 'WagonR', 'vezel': 'Vezel',
        'prius': 'Prius', 'vitz': 'Vitz', 'corolla': 'Corolla',
        'camry': 'Camry', 'hilux': 'Hilux', 'hiace': 'Hiace',
        'caravan': 'Caravan', 'march': 'March', 'sunny': 'Sunny',
        'xtrail': 'XTrail', 'lancer': 'Lancer', 'pajero': 'Pajero',
        'delica': 'Delica', 'rosa': 'Rosa', 'coaster': 'Coaster',
        'civilian': 'Civilian', 'viking': 'Viking', 'lion': 'Lion',
        'ace': 'Ace', 'super ace': 'Super Ace', 'elf': 'Elf',
        'maxximo': 'Maxximo', 'pleasure': 'Pleasure', 'hf deluxe': 'HF Deluxe'
    }
    if model_lower in model_mapping:
        return model_mapping[model_lower]
    return model_lower.title()


@app.route("/ui")
def ui_dashboard():
    return render_template("index.html")


# 🔍 🚀 අලුතින්ම එකතු කරන ලද Real-time Auto-Suggestions Endpoint එක
@app.route("/get_suggestions", methods=["GET"])
def get_suggestions():
    raw_make = request.args.get("make", "").strip()
    query_text = request.args.get("query", "").strip()

    if not raw_make or not query_text:
        return jsonify([])

    # ML Pipeline එකට ගැළපෙන ආකාරයට Make එක සාමාන්‍යකරණය කිරීම (e.g. toyota -> Toyota)
    normalized_make = normalize_make(raw_make)
    
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            # Database එකෙන් අදාළ Make එකට අයිති, User ටයිප් කරන අකුරු වලින් ආරම්භ වන සුවිශේෂී (Distinct) Models 10ක් ලබා ගැනීම
            sql = "SELECT DISTINCT model FROM vehicle_prices WHERE make = %s AND model LIKE %s LIMIT 10"
            cursor.execute(sql, (normalized_make, f"{query_text}%"))
            results = cursor.fetchall()
            
            # Tuple ලැයිස්තුව සාමාන්‍ය string list එකක් බවට පත් කිරීම
            suggestions = [row[0] for row in results]
            
            response = jsonify(suggestions)
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response
            
    except Exception as e:
        print(f"❌ Database error in suggestions: {e}")
        return jsonify([])
    finally:
        if 'connection' in locals() and connection.open:
            connection.close()


@app.route("/")
def index():
    return jsonify({
        "app":      "CarPriceLK API",
        "status":   "running",
        "ui_url":   "http://localhost:5000/ui",
        "accuracy": f"R² {META['r2_score']}",
        "mae_lkr":  META["mae_lkr"],
        "vehicle_types": META.get("vehicle_types", ["Car", "Van", "Bus", "SUV", "Lorry", "Motorcycle", "ThreeWheel"]),
    })


@app.route("/models")
def get_models():
    return jsonify({
        "makes":          META.get("makes", []),
        "models":         META.get("models", []),
        "fuel_types":     META.get("fuel_types", ["petrol", "diesel", "hybrid", "electric"]),
        "transmissions":  META.get("transmissions", ["automatic", "manual"]),
        "vehicle_types":  META.get("vehicle_types", ["Car", "Van", "Bus", "SUV", "Lorry", "Motorcycle", "ThreeWheel"]),
        "r2_score":       META.get("r2_score", 0),
        "mae_lkr":        META.get("mae_lkr", 0),
    })


@app.route("/predict", methods=["POST", "OPTIONS"])
def predict():
    if request.method == "OPTIONS":
        response = jsonify({"message": "OK"})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        return response
    
    body = request.get_json() or {}

    # Map frontend 'model_name' safely to backend expected 'model' parameter
    if "model_name" in body and "model" not in body:
        body["model"] = body["model_name"]

    required = ["make", "model", "year", "mileage"]
    for field in required:
        if field not in body:
            return jsonify({"error": f"Missing field: {field}"}), 400

    fuel_type    = body.get("fuel_type", "petrol")
    transmission = body.get("transmission", "automatic")
    
    # FIX: Default to proper Title Case "Car" instead of lowercase "car"
    raw_vehicle_type = str(body.get("vehicle_type", "Car")).strip().lower()
    
    # Direct normalization mapping for special classes like Three-Wheelers
    if raw_vehicle_type in ["threewheel", "three-wheeler", "threewheeler"]:
        vehicle_type = "ThreeWheel"
    else:
        vehicle_type = raw_vehicle_type.title()

    raw_make = str(body["make"]).strip()
    raw_model = str(body["model"]).strip()
    
    normalized_make = normalize_make(raw_make)
    normalized_model = normalize_model(raw_model, normalized_make)
    
    print(f"🔍 Original Input: make='{raw_make}', model='{raw_model}', type='{body.get('vehicle_type')}'")
    print(f"🔍 Pipeline Fed:   make='{normalized_make}', model='{normalized_model}', type='{vehicle_type}'")

    result = predict_price(
        make         = normalized_make,
        model_name   = normalized_model,
        year         = int(body["year"]),
        mileage      = int(body["mileage"]),
        fuel_type    = str(fuel_type).lower().strip(),
        transmission = str(transmission).lower().strip(),
        vehicle_type = vehicle_type, # Fed to engine with standard Title Case strings
    )

    if "error" in result:
        return jsonify(result), 400

    response = jsonify(result)
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


if __name__ == "__main__":
    print("=" * 50)
    print("  CarPriceLK API — UI Available at: http://localhost:5000/ui")
    print("=" * 50)
    app.run(debug=True, port=5000)