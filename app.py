from datetime import datetime, timezone
import math
import re
from flask import Flask, jsonify, request

app = Flask(__name__)

def clean_text(value, max_length=200):
    """Normaliza texto simple y evita caracteres de control."""
    if value is None:
        return ""
    text = re.sub(r"[\x00-\x1f\x7f]", " ", str(value))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_length]

def as_number(value, default=0.0):
    try:
        number = float(value)
        return number if math.isfinite(number) else default
    except (TypeError, ValueError):
        return default

def classify_event(item):
    magnitude = as_number(item.get("magnitude", 0))
    if magnitude >= 5.0:
        label = "alto"
    elif magnitude >= 3.0:
        label = "moderado"
    else:
        label = "bajo"

    return {
        "id": clean_text(item.get("id", "sin-id"), 100),
        "place": clean_text(item.get("place", "Ubicación desconocida"), 200),
        "magnitude": magnitude,
        "depth_km": as_number(item.get("depth_km", 0)),
        "time_utc": clean_text(item.get("time_utc", ""), 40),
        "label": label,
        "rule": "magnitude >= 5: alto; >= 3: moderado; < 3: bajo"
    }

@app.get("/")
def index():
    return jsonify({
        "service": "earthquake-mining-api",
        "status": "ok",
        "endpoints": {"health": "GET /health", "analyze": "POST /analyze"}
    })

@app.get("/health")
def health():
    return jsonify({"service": "earthquake-mining-api", "status": "ok"})

@app.post("/analyze")
def analyze():
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Se requiere un JSON válido con Content-Type application/json"}), 400

    items = payload if isinstance(payload, list) else payload.get("data") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return jsonify({"error": "El JSON debe ser una lista o un objeto con la propiedad 'data' como lista"}), 400

    if not all(isinstance(item, dict) for item in items):
        return jsonify({"error": "Cada elemento de data debe ser un objeto JSON"}), 400

    results = [classify_event(item) for item in items]
    return jsonify({
        "pipeline": "usgs-earthquake-serverless-mining",
        "processed_at": datetime.now(timezone.utc).isoformat(),
        "input_count": len(items),
        "output_count": len(results),
        "results": results
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
