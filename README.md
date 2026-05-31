# Arquitectura Orientada a Eventos con Kafka, Caché y DLQ

Este proyecto implementa un sistema asíncrono y tolerante a fallos diseñado para procesar consultas pesadas sobre un dataset geoespacial. Utiliza Apache Kafka para encolar ráfagas de peticiones, Redis para mitigar la carga computacional mediante caché, y un sistema de Worker resiliente con reintentos automáticos y Dead Letter Queue (DLQ).

## Tecnologías Utilizadas
* **Lenguaje:** Python 3.12
* **Framework Web:** FastAPI / Uvicorn
* **Message Broker:** Apache Kafka (Manejo asíncrono de eventos)
* **Base de Datos en Memoria:** Redis (Manejo de Caché LRU)
* **Procesamiento de Datos:** Pandas / NumPy
* **Orquestación:** Docker y Docker Compose

## Estructura del Proyecto

* `generadorDeRespuestas.py`: El "Worker" del sistema. Actúa como **Consumidor y Productor de Kafka**. Extrae mensajes de la cola, realiza cálculos espaciales pesados, consulta el proxy de caché e implementa resiliencia (Reintentos y envío a `consultas_dlq` si hay fallo crítico).
* `modulo_cache.py`: Servidor intermediario (Proxy) conectado a Redis. Intercepta las peticiones del Worker para verificar si el resultado ya fue calculado previamente (Cache Hit/Miss).
* `generador_trafico.py`: Script de pruebas de estrés (**Productor de Kafka**). Simula cientos de eventos asíncronos hacia el servidor utilizando distribuciones estadísticas (Uniforme aleatoria y Ley de Zipf para zonas populares).
* `analizar_metricas.py`: Herramienta de auditoría que evalúa el rendimiento del sistema, Hit Rate de la caché, latencias y el Percentil 95 (P95) agrupado por tipo de tráfico.
* `docker-compose.yml` y `Dockerfile`: Recetas para construir y conectar los servicios (Backend, Proxy, Kafka y Redis) en una misma red virtual.
* `dataset_santiago.csv`: Dataset principal con los registros de las edificaciones.

## Requisitos Previos

1. [Docker](https://docs.docker.com/get-docker/)
2. [Docker Compose](https://docs.docker.com/compose/install/)
3. Python 3.10+.

## Pasos de Ejecución Inicial

**1. Levantar la infraestructura en Docker**

  sudo docker compose up -d --build

**2. Activar entorno virtual local e instalar dependencias**

  python3 -m venv entorno_backend
  
  source entorno_backend/bin/activate
  
  pip install -r requirements.txt
  
  pip install pandas numpy

**3. Iniciar bombardeo de peticiones**

  python generador_trafico.py

## Reinicio Completo y Pruebas Limpias

**1. Apagar y destruir todos los contenedores y volúmenes (Terminal 1)**

  sudo docker compose down -v --remove-orphans

**2. Borrar el historial de métricas local (Terminal 1)**

  rm metricas.csv

**3. Levantar la arquitectura desde cero (Terminal 1)**

  sudo docker compose up -d --build

**4. Lanzar el bombardeo (Terminal 2)**

  python generador_trafico.py
