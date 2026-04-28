import pandas as pd

# 1. Entrada y salida de el archivo
archivo_entrada = '967_buildings(1).csv' 
archivo_salida = 'dataset_santiago.csv'

# 2. Limitando a las columnas especificadas
columnas_requeridas = ['latitude', 'longitude', 'area_in_meters', 'confidence']

# 3. Límites geográficos
zonas = {
    "Z1_Providencia": (-33.445, -33.420, -70.640, -70.600),
    "Z2_Las_Condes":  (-33.420, -33.390, -70.600, -70.550),
    "Z3_Maipu":       (-33.530, -33.490, -70.790, -70.740),
    "Z4_Stgo_Centro": (-33.460, -33.430, -70.670, -70.630),
    "Z5_Pudahuel":    (-33.470, -33.430, -70.810, -70.760)
}

# 4. Procesamiento por trozos (chunks)
chunk_size = 500000  # Lee de a medio millón de filas a la vez
primer_chunk = True
total_guardados = 0

print(f"Iniciando el filtrado del archivo: {archivo_entrada}...")

# Leer el CSV original filtrando solo las columnas necesarias desde el inicio
for chunk in pd.read_csv(archivo_entrada, usecols=columnas_requeridas, chunksize=chunk_size):
    
    # Crear una máscara vacía (todo en Falso)
    mask_total = pd.Series(False, index=chunk.index)
    
    # Aplicar las condiciones de cada zona
    for zona, (min_lat, max_lat, min_lon, max_lon) in zonas.items():
        mask_zona = (
            (chunk['latitude'] >= min_lat) & (chunk['latitude'] <= max_lat) &
            (chunk['longitude'] >= min_lon) & (chunk['longitude'] <= max_lon)
        )
        # Sumar la condición a la máscara total (Operación OR)
        mask_total = mask_total | mask_zona
        
    # Filtrar las filas que cumplen con al menos una zona
    chunk_filtrado = chunk[mask_total]
    
    # Guardar en el nuevo archivo CSV
    if not chunk_filtrado.empty:
        # Modo 'w' (write) para la primera vez, 'a' (append) para las siguientes
        modo_escritura = 'w' if primer_chunk else 'a'
        escribir_encabezado = primer_chunk
        
        chunk_filtrado.to_csv(archivo_salida, mode=modo_escritura, index=False, header=escribir_encabezado)
        
        primer_chunk = False
        total_guardados += len(chunk_filtrado)
        print(f"  -> Guardados {total_guardados} edificios de las zonas requeridas hasta el momento...")

print("\n¡Proceso terminado!")
print(f"Se exportó un total de {total_guardados} registros útiles.")
print(f"Archivo limpio disponible en: {archivo_salida}")