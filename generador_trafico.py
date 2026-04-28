import requests
import time
import random
import numpy as np
import concurrent.futures

# Se apunta al Caché
CACHE_URL = "http://localhost:8001"

# Consultas posibles (Q1, Q2 y Q5 para distintas zonas)
ZONAS = ["Z1", "Z2", "Z3", "Z4", "Z5"]
CONSULTAS_POSIBLES = []
for z in ZONAS:
    CONSULTAS_POSIBLES.extend([
        f"/api/q1?zona_id={z}&confidence_min=0.6",
        f"/api/q2?zona_id={z}&confidence_min=0.7",
        f"/api/q3?zona_id={z}",
        f"/api/q4?zona_id={z}",
        f"/api/q5?zona_id={z}&bins=5"
    ])
# 15 tipos de consultas distintas.

def hacer_peticion(url):
    """Función que realiza la llamada HTTP a la API"""
    try:
        r = requests.get(url)
        return r.status_code
    except Exception:
        return 500

def ejecutar_test(distribucion, total_peticiones):
    print(f"Iniciando bombardeo... Distribución: {distribucion.upper()} ({total_peticiones} peticiones)")
    
    urls_a_consultar = []
    
    if distribucion == "uniforme":
        # Elegir totalmente al azar
        urls_a_consultar = [CACHE_URL + random.choice(CONSULTAS_POSIBLES) for _ in range(total_peticiones)]
        
    elif distribucion == "zipf":
        # Distribución Zipf: simulando zonas muy populares
        parametro_zipf = 1.5 
        indices = np.random.zipf(parametro_zipf, total_peticiones)
        
        for idx in indices:
            # Ajustamos el índice para que no se salga de nuestra lista de 15 consultas
            indice_ajustado = (idx - 1) % len(CONSULTAS_POSIBLES)
            urls_a_consultar.append(CACHE_URL + CONSULTAS_POSIBLES[indice_ajustado])

    # Iniciar cronómetro
    inicio = time.time()
    
    # ThreadPoolExecutor: Peticiones simultaneas
    hilos_simultaneos = 10 
    exitos = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=hilos_simultaneos) as executor:
        resultados = list(executor.map(hacer_peticion, urls_a_consultar))
        exitos = resultados.count(200) # Contador de '200 OK'

    # Detener cronómetro
    fin = time.time()
    tiempo_total = fin - inicio
    rendimiento = total_peticiones / tiempo_total
    
    # Imprimir métricas
    print(f"Exitosas: {exitos}/{total_peticiones}")
    print(f"Tiempo total: {tiempo_total:.2f} segundos")
    print(f"Rendimiento: {rendimiento:.2f} peticiones/segundo\n")

if __name__ == "__main__":
    print("######################################  Iniciando... ###################################### \n")
    time.sleep(3)
    
    # Ronda 1: Caos total (100 peticiones)
    ejecutar_test(distribucion="uniforme", total_peticiones=100)
    
    # Ronda 2: Tendencia realista (100 peticiones)
    ejecutar_test(distribucion="zipf", total_peticiones=100)