import time
import random
import numpy as np
import concurrent.futures
import json
import uuid
from datetime import datetime
from kafka import KafkaProducer

# Configuracion para tarea 2 "Inicializacion del productor Kafka"
print("Conectando con el clúster de Kafka...")
productor = KafkaProducer(
    bootstrap_servers=['localhost:9094'],
    api_version=(3, 7, 0),
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)
TOPICO_PRINCIPAL = 'consultas_principal'
print("¡Productor Kafka listo y conectado!")

# Consultas posibles (Q1, Q2 y Q5 para distintas zonas)
ZONAS = ["Z1", "Z2", "Z3", "Z4", "Z5"]
CONSULTAS_POSIBLES = []
for z in ZONAS:
    CONSULTAS_POSIBLES.extend([
        f"/api/q1?zona_id={z}&confidence_min=0.6",
        f"/api/q2?zona_id={z}&confidence_min=0.7",
        f"/api/q3?zona_id={z}",
        f"/api/q4?zona_a={z}&zona_b=Z1",
        f"/api/q5?zona_id={z}&bins=5"
    ])
# 15 tipos de consultas distintas.

# Nueva funcion para que se envie a Kafka, que ya no usan HTTP
def hacer_peticion(consulta_str):
    """Función que envía el mensaje (evento) a Kafka"""
    try:
        # Estructura
        mensaje = {
            "id_consulta": str(uuid.uuid4()),             # Identificador único
            "retry_count": 0,                             # Número de reintentos
            "timestamp": datetime.utcnow().isoformat(),   # Timestamp de creación
            "consulta": consulta_str                      # La ruta de la consulta
        }
        
        # Se envia el mensaje al buzon
        productor.send(TOPICO_PRINCIPAL, value=mensaje)
        
        # 200 en caso de exito
        return 200 
    except Exception as e:
        print(f"Error al enviar a Kafka: {e}")
        return 500

def ejecutar_test(distribucion, total_peticiones):
    print(f"Iniciando bombardeo... Distribución: {distribucion.upper()} ({total_peticiones} peticiones)")
    
    consultas_a_enviar = []
    
    if distribucion == "uniforme":
        # Elegir totalmente al azar (Ya no le pegamos el CACHE_URL al inicio)
        consultas_a_enviar = [random.choice(CONSULTAS_POSIBLES) for _ in range(total_peticiones)]
        
    elif distribucion == "zipf":
        # Distribución Zipf: simulando zonas muy populares
        parametro_zipf = 1.5 
        indices = np.random.zipf(parametro_zipf, total_peticiones)
        
        for idx in indices:
            # se ajusta el índice para que no se salga de la lista de 15 consultas
            indice_ajustado = (idx - 1) % len(CONSULTAS_POSIBLES)
            consultas_a_enviar.append(CONSULTAS_POSIBLES[indice_ajustado])

    # Iniciar cronómetro
    inicio = time.time()
    
    # ThreadPoolExecutor: Peticiones concurrentes
    exitos = 0
    fallos = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        resultados = list(executor.map(hacer_peticion, consultas_a_enviar))
        
    for r in resultados:
        if r == 200:
            exitos += 1
        else:
            fallos += 1
            
    fin = time.time()
    print(f"Terminado en {fin - inicio:.2f}s | Éxitos: {exitos} | Fallos: {fallos}\n")

if __name__ == "__main__":
    print("######################################  Iniciando... ###################################### \n")
    time.sleep(3)
    
    # Ronda 1: Caos total (100 peticiones)
    ejecutar_test(distribucion="uniforme", total_peticiones=1000)
    
    # Ronda 2: Tendencia realista (100 peticiones)
    ejecutar_test(distribucion="zipf", total_peticiones=1000)
    
    print("Vaciando búfer y asegurando la entrega a Kafka...")
    productor.flush()
    print("¡Todos los mensajes han sido forzados a salir y entregados a Kafka exitosamente!")
