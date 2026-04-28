from fastapi import FastAPI, Request
import redis
import requests
import json
import time
import csv
import os
from datetime import datetime

app = FastAPI()

# 1. Conectando a Redis
redis_client = redis.Redis(host='redis-db', port=6379, db=0, decode_responses=True)

# 2. Server BackEnd
BACKEND_URL = "http://backend:8000"

# 3. Métricas
archivo_metricas = "metricas.csv"

# Crear el archivo CSV de métricas con sus columnas si no existe
if not os.path.exists(archivo_metricas):
    with open(archivo_metricas, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["timestamp", "evento", "consulta", "latencia_segundos"])

def registrar_metrica(evento, consulta, latencia):
    """Guarda un registro en el archivo CSV cada vez que alguien hace una petición"""
    with open(archivo_metricas, mode="a", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), evento, consulta, f"{latencia:.4f}"])

@app.get("/api/{consulta}")
def cache_proxy(consulta: str, request: Request):
    inicio_tiempo = time.time()

    # A) Llave creada en base a URL
    query_params = str(request.query_params)
    llave_cache = f"{consulta}:{query_params}"
    
    # B) Buscar en Redis la query
    respuesta_guardada = redis_client.get(llave_cache)
    
    if respuesta_guardada:
        print(f"HIT: Encontrado en memoria rápida -> {llave_cache}")
        
        latencia = time.time() - inicio_tiempo
        registrar_metrica("HIT", llave_cache, latencia) 
        
        return json.loads(respuesta_guardada)
    
    # C) Si no está, se le pregunta al Generador de Respuestas
    print(f"MISS: No encontrado. Calculando en backend -> {llave_cache}")
    url_backend = f"{BACKEND_URL}/api/{consulta}?{query_params}"
    
    try:
        # Petición al puerto 8000
        respuesta_backend = requests.get(url_backend)
        respuesta_backend.raise_for_status()
        datos = respuesta_backend.json()
        
        # D) Se guarda la respuesta en Redis como string JSON y TTL 60 seg
        respuesta_json = json.dumps(datos)
        redis_client.set(llave_cache, respuesta_json, ex=60) 
        
        # Guarda metrica del MISS
        latencia = time.time() - inicio_tiempo
        registrar_metrica("MISS", llave_cache, latencia)
        
        return datos
        
    except requests.exceptions.RequestException as e:
        latencia = time.time() - inicio_tiempo
        registrar_metrica("ERROR", llave_cache, latencia) 
        
        return {"error": "El Generador de Respuestas no está disponible", "detalle": str(e)}