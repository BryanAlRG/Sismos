# Pipeline de minería de datos en la nube: sismos

Proyecto académico que consulta el feed GeoJSON público de USGS, normaliza eventos sísmicos y los envía a una API Flask para clasificación por magnitud.

## Arquitectura
1. Fuente externa en tiempo real: USGS Earthquake API (GeoJSON).
2. Extracción: `fetcher.py`.
3. Ingesta HTTP: `POST /analyze` con JSON `{ "data": [...] }`.
4. Preprocesamiento y clasificación: `app.py`.
5. Salida: JSON con etiqueta `bajo`, `moderado` o `alto`.

## Requisitos
Python 3.10 o superior e internet para consultar USGS.

## Ejecutar en Windows (PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```
En otra terminal, desde la carpeta del proyecto:
```powershell
.venv\Scripts\Activate.ps1
python fetcher.py --input-json sample_input.json --service-url http://127.0.0.1:8080
```
Prueba extracción real:
```powershell
python fetcher.py --service-url http://127.0.0.1:8080 --limit 10
```

## Despliegue manual en Render
- Crear un repositorio GitHub y subir los archivos de esta carpeta.
- Render: New + -> Web Service -> conectar el repositorio.
- Runtime: Python 3.
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app --bind 0.0.0.0:$PORT`
- Health Check Path: `/health` (si aparece el campo).
- Environment Variables: no se requieren para esta versión.
- La URL pública y el funcionamiento real solo se confirman después de un despliegue exitoso.

## Probar la URL de Render
```powershell
$body = Get-Content sample_input.json -Raw
Invoke-RestMethod -Uri "https://TU-SERVICIO.onrender.com/analyze" -Method Post -ContentType "application/json" -Body $body
```
Sustituye `TU-SERVICIO` por el dominio real asignado por Render.

## API
- `GET /`: información del servicio.
- `GET /health`: estado del servicio.
- `POST /analyze`: acepta una lista JSON o un objeto con `data` como lista.
Cada objeto admite `id`, `place`, `magnitude`, `depth_km` y `time_utc`.

## Reglas didácticas
- Magnitud >= 5.0: `alto`
- Magnitud >= 3.0 y < 5.0: `moderado`
- Magnitud < 3.0: `bajo`

Las etiquetas son una clasificación simplificada para fines educativos; no representan una evaluación oficial de peligro o riesgo sísmico.
