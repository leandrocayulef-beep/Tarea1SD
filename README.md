## Tecnologías Utilizadas ##
* Lenguaje: Python 3.12
* Framework Web: FastAPI / Uvicorn
* Base de Datos en Memoria: Redis
* Procesamiento de Datos: Pandas / NumPy
* Orquestación: Docker y Docker Compose


## Estructura ##

* `generadorDeRespuestas.py`: Backend que procesa los cálculos pesados leyendo el archivo CSV.
* `modulo_cache.py`: Servidor intermediario o Proxy, conectado a Redis que intercepta las peticiones y gestiona la memoria caché.
* `generador_trafico.py`: Script de pruebas de estrés que simula cientos de peticiones usando distribuciones estadísticas (Uniforme y Ley de Zipf).
* `docker-compose.yml` y `Dockerfile`: Recetas para construir y conectar los contenedores de forma automatizada.
* `dataset_santiago.csv`: Dataset principal con los registros de las edificaciones.

## Requisitos Previos ##

1. [Docker](https://docs.docker.com/get-docker/)
2. [Docker Compose](https://docs.docker.com/compose/install/)
3. Python 3.10+.

## Pasos de Ejecución ##
* Levantar la arquitectura:
  
  sudo docker-compose up --build
  
* Activar tu entorno virtual local:
  
  python3 -m venv entorno_backend
  
  source entorno_backend/bin/activate
  
  pip install -r requirements.txt

* Lanzar el ataque:

  python generador_trafico.py
  
  python analizar_metricas.py
