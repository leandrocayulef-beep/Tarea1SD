from fastapi import FastAPI, HTTPException
import pandas as pd
import numpy as np
import math
import os

# --- INICIO DEL FRAGMENTO AGREGADO (Importaciones) ---
import asyncio
import json
import requests
import random
import time
from kafka import KafkaConsumer, KafkaProducer
import threading
# --- FIN DEL FRAGMENTO AGREGADO ---

app = FastAPI()

# --- Logica de Kafka ---
TOPICO_PRINCIPAL = 'consultas_principal'
TOPICO_RETRY = 'consultas_retry'
TOPICO_DLQ = 'consultas_dlq'
MAX_RETRIES = 3

URL_PROXY = "http://cache-proxy:8001" 

def escuchar_kafka():
    print("Iniciando Consumidor/Productor de Kafka en el Backend...")
    
    # 1. Para enviar mensajes fallidos a Retry o DLQ
    productor = KafkaProducer(
        bootstrap_servers=['tarea2sd-kafka:9092'],
        api_version=(3, 7, 0),
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

    # 2. Creacion del Consumidor
    consumidor = KafkaConsumer(
        TOPICO_PRINCIPAL,
        TOPICO_RETRY,
        bootstrap_servers=['tarea2sd-kafka:9092'],
        api_version=(3, 7, 0),
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    for mensaje in consumidor:
        datos = mensaje.value
        id_consulta = datos.get("id_consulta")
        ruta_consulta = datos.get("consulta")
        intentos_previos = datos.get("retry_count", 0)
        
        print(f"\n[Kafka] Leyendo ID: {id_consulta} | Intento actual: {intentos_previos}")
        
        try:
            # --- SIMULADOR DE CAOS ---
            # Se hace a proposito un fallo del 20% de las peticiones
            if random.random() < 0.20:
                raise Exception("Fallo simulado de red o base de datos")

            url_completa = f"{URL_PROXY}{ruta_consulta}"
            respuesta = requests.get(url_completa)
            
            if respuesta.status_code == 200:
                print(f"   ¡Éxito! Consulta procesada: {ruta_consulta}")
            else:
                raise Exception(f"Respuesta inesperada del Proxy: {respuesta.status_code}")
                
        except Exception as e:
            print(f"    Error: {e}")
            
            # --- LÓGICA DE RESILIENCIA Y DLQ ---
            datos["retry_count"] += 1
            
            if datos["retry_count"] <= MAX_RETRIES:
                print(f"   Reintentando... Enviando a {TOPICO_RETRY} (Intento {datos['retry_count']}/{MAX_RETRIES})")
                time.sleep(1) # Pausa dramática antes de reenviar
                productor.send(TOPICO_RETRY, value=datos)
            else:
                print(f"   Máximo de reintentos. Enviando a {TOPICO_DLQ}...")
                productor.send(TOPICO_DLQ, value=datos)
                
            productor.flush()

@app.on_event("startup")
async def iniciar_background_task():
    hilo_kafka = threading.Thread(target=escuchar_kafka, daemon=True)
    hilo_kafka.start()
# --- FIN DEL FRAGMENTO AGREGADO ---

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
    df_edificios = pd.read_csv(archivo_csv)
else:
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
    return {"status": "ok"}

@app.get("/api/q1")
def q1_count(zona_id: str, confidence_min: float = 0.0):
    df_zona = obtener_datos_zona(zona_id)
    resultado = df_zona[df_zona['confidence'] >= confidence_min]
    return {"consulta": "Q1", "zona": zona_id, "count": len(resultado)}

@app.get("/api/q2")
def q2_area(zona_id: str, confidence_min: float = 0.0):
    df_zona = obtener_datos_zona(zona_id)
    resultado = df_zona[df_zona['confidence'] >= confidence_min]
    if len(resultado) == 0:
        return {"avg_area": 0, "total_area": 0, "n": 0}
    avg_area = float(resultado['area_in_meters'].mean())
    total_area = float(resultado['area_in_meters'].sum())
    return {"consulta": "Q2", "zona": zona_id, "avg_area": avg_area, "total_area": total_area}

@app.get("/api/q3")
def q3_density(zona_id: str, confidence_min: float = 0.0):
    df_zona = obtener_datos_zona(zona_id)
    count = len(df_zona[df_zona['confidence'] >= confidence_min])
    area_km2 = calcular_area_km2(zona_id)
    densidad = count / area_km2 if area_km2 > 0 else 0
    return {"consulta": "Q3", "zona": zona_id, "densidad_por_km2": densidad}

@app.get("/api/q4")
def q4_compare(zona_a: str, zona_b: str, confidence_min: float = 0.0):
    df_a = obtener_datos_zona(zona_a)
    densidad_a = len(df_a[df_a['confidence'] >= confidence_min]) / calcular_area_km2(zona_a)
    df_b = obtener_datos_zona(zona_b)
    densidad_b = len(df_b[df_b['confidence'] >= confidence_min]) / calcular_area_km2(zona_b)
    ganador = zona_a if densidad_a > densidad_b else zona_b
    if densidad_a == densidad_b: ganador = "empate"
    return {"consulta": "Q4", "zone_a": densidad_a, "zone_b": densidad_b, "winner": ganador}

@app.get("/api/q5")
def q5_confidence_dist(zona_id: str, bins: int = 5):
    df_zona = obtener_datos_zona(zona_id)
    scores = df_zona['confidence'].tolist()
    if not scores: return {"consulta": "Q5", "zona": zona_id, "distribucion": []}
    counts, edges = np.histogram(scores, bins=bins, range=(0, 1))
    distribucion = [{"bucket": i, "min": float(edges[i]), "max": float(edges[i+1]), "count": int(counts[i])} for i in range(bins)]
    return {"consulta": "Q5", "zona": zona_id, "bins": bins, "distribucion": distribucion}
