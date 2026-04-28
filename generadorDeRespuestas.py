from fastapi import FastAPI, HTTPException
import pandas as pd
import numpy as np
import math
import os

app = FastAPI()

# 1. Zonas
ZONAS = {
    "Z1": {"lat_min": -33.445, "lat_max": -33.420, "lon_min": -70.640, "lon_max": -70.600},
    "Z2": {"lat_min": -33.420, "lat_max": -33.390, "lon_min": -70.600, "lon_max": -70.550},
    "Z3": {"lat_min": -33.530, "lat_max": -33.490, "lon_min": -70.790, "lon_max": -70.740},
    "Z4": {"lat_min": -33.460, "lat_max": -33.430, "lon_min": -70.670, "lon_max": -70.630},
    "Z5": {"lat_min": -33.470, "lat_max": -33.430, "lon_min": -70.810, "lon_max": -70.760}
}

# 2. Cargar el dataset en memoria al iniciar
archivo_csv = "dataset_santiago.csv"
if os.path.exists(archivo_csv):
    print(f"Cargando {archivo_csv} en memoria...")
    df_edificios = pd.read_csv(archivo_csv)
    print(f"Dataset cargado. Total de registros: {len(df_edificios)}")
else:
    print(f"ADVERTENCIA: No se encontró {archivo_csv}.")
    df_edificios = None

# --- Funciones Auxiliares ---
def obtener_datos_zona(zona_id: str):
    if df_edificios is None:
        raise HTTPException(status_code=500, detail="Base de datos no cargada")
    if zona_id not in ZONAS:
        raise HTTPException(status_code=404, detail="Zona no válida. Use Z1 a Z5.")
    
    z = ZONAS[zona_id]
    df_zona = df_edificios[
        (df_edificios['latitude'] >= z['lat_min']) & 
        (df_edificios['latitude'] <= z['lat_max']) &
        (df_edificios['longitude'] >= z['lon_min']) & 
        (df_edificios['longitude'] <= z['lon_max'])
    ]
    return df_zona

def calcular_area_km2(zona_id: str):
    z = ZONAS[zona_id]
    lat_mid = math.radians((z['lat_min'] + z['lat_max']) / 2)
    alto_km = abs(z['lat_max'] - z['lat_min']) * 111.1
    ancho_km = abs(z['lon_max'] - z['lon_min']) * 111.1 * math.cos(lat_mid)
    return alto_km * ancho_km

# --- Endpoints de la API ---

@app.get("/ping")
def ping():
    return {"status": "ok", "mensaje": "Generador de Respuestas funcionando al 100%"}

@app.get("/api/q1")
def q1_count(zona_id: str, confidence_min: float = 0.0):
    df_zona = obtener_datos_zona(zona_id)
    resultado = df_zona[df_zona['confidence'] >= confidence_min]
    
    return {
        "consulta": "Q1",
        "zona": zona_id,
        "confidence_min": confidence_min,
        "count": len(resultado)
    }

@app.get("/api/q2")
def q2_area(zona_id: str, confidence_min: float = 0.0):
    df_zona = obtener_datos_zona(zona_id)
    resultado = df_zona[df_zona['confidence'] >= confidence_min]
    
    if len(resultado) == 0:
        return {"avg_area": 0, "total_area": 0, "n": 0}
        
    avg_area = float(resultado['area_in_meters'].mean())
    total_area = float(resultado['area_in_meters'].sum())
    
    return {
        "consulta": "Q2",
        "zona": zona_id,
        "avg_area": avg_area,
        "total_area": total_area,
        "n": len(resultado)
    }

@app.get("/api/q3")
def q3_density(zona_id: str, confidence_min: float = 0.0):
    df_zona = obtener_datos_zona(zona_id)
    resultado = df_zona[df_zona['confidence'] >= confidence_min]
    count = len(resultado)
    
    area_km2 = calcular_area_km2(zona_id)
    densidad = count / area_km2 if area_km2 > 0 else 0
    
    return {
        "consulta": "Q3",
        "zona": zona_id,
        "densidad_por_km2": densidad
    }

@app.get("/api/q4")
def q4_compare(zona_a: str, zona_b: str, confidence_min: float = 0.0):
    df_a = obtener_datos_zona(zona_a)
    count_a = len(df_a[df_a['confidence'] >= confidence_min])
    densidad_a = count_a / calcular_area_km2(zona_a)
    
    df_b = obtener_datos_zona(zona_b)
    count_b = len(df_b[df_b['confidence'] >= confidence_min])
    densidad_b = count_b / calcular_area_km2(zona_b)
    
    ganador = zona_a if densidad_a > densidad_b else zona_b
    if densidad_a == densidad_b:
        ganador = "empate"
        
    return {
        "consulta": "Q4",
        "zone_a": densidad_a,
        "zone_b": densidad_b,
        "winner": ganador
    }

@app.get("/api/q5")
def q5_confidence_dist(zona_id: str, bins: int = 5):
    df_zona = obtener_datos_zona(zona_id)
    scores = df_zona['confidence'].tolist()
    
    if not scores:
        return {"consulta": "Q5", "zona": zona_id, "distribucion": []}
    
    counts, edges = np.histogram(scores, bins=bins, range=(0, 1))
    
    distribucion = []
    for i in range(bins):
        distribucion.append({
            "bucket": i,
            "min": float(edges[i]),
            "max": float(edges[i+1]),
            "count": int(counts[i])
        })
        
    return {
        "consulta": "Q5",
        "zona": zona_id,
        "bins": bins,
        "distribucion": distribucion
    }