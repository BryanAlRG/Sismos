import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

USGS_URL = (
    "https://earthquake.usgs.gov/fdsnws/event/1/query"
    "?format=geojson&orderby=time&limit=10&minmagnitude=1"
)

def request_json(url, data=None, headers=None, timeout=30):
    req = urllib.request.Request(url, data=data, headers=headers or {}, method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} al consultar {url}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"No se pudo conectar con {url}: {exc}") from exc

def normalize_usgs(feature):
    props = feature.get("properties") or {}
    geometry = feature.get("geometry") or {}
    coords = geometry.get("coordinates") or [0, 0, 0]
    timestamp_ms = props.get("time")
    time_utc = ""
    if timestamp_ms is not None:
        time_utc = datetime.fromtimestamp(timestamp_ms / 1000, tz=timezone.utc).isoformat()
    return {
        "id": feature.get("id", ""),
        "place": props.get("place", "Ubicación desconocida"),
        "magnitude": props.get("mag", 0),
        "depth_km": coords[2] if len(coords) > 2 else 0,
        "time_utc": time_utc
    }

def main():
    parser = argparse.ArgumentParser(description="Extrae sismos de USGS y los envía al microservicio de clasificación.")
    parser.add_argument("--input-json", help="Usa datos locales de prueba en vez de consultar USGS.")
    parser.add_argument("--service-url", default="", help="URL base del microservicio, por ejemplo https://mi-api.onrender.com")
    parser.add_argument("--limit", type=int, default=10, help="Número máximo de eventos recientes para solicitar a USGS (1-50).")
    args = parser.parse_args()

    if args.input_json:
        with open(args.input_json, "r", encoding="utf-8") as file:
            payload = json.load(file)
        items = payload.get("data") if isinstance(payload, dict) else payload
        if not isinstance(items, list):
            raise SystemExit("El archivo de entrada debe ser una lista o un objeto con 'data' como lista.")
    else:
        limit = max(1, min(args.limit, 50))
        url = USGS_URL.replace("limit=10", f"limit={limit}")
        source = request_json(url)
        features = source.get("features", [])
        items = [normalize_usgs(feature) for feature in features]

    payload = {"data": items}
    if not args.service_url:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        print("\nNo se indicó --service-url; se muestra la extracción sin enviar al microservicio.")
        return

    endpoint = args.service_url.rstrip("/") + "/analyze"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    result = request_json(endpoint, data=body, headers={
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "EarthquakeMiningPractice/1.0"
    })
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
