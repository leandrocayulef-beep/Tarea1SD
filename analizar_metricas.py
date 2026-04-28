import pandas as pd

try:
    df = pd.read_csv('metricas.csv')
    
    hits = df[df['evento'] == 'HIT']
    misses = df[df['evento'] == 'MISS']
    errores = df[df['evento'] == 'ERROR']
    
    print(f"Total de peticiones procesadas: {len(df)}")
    
    if len(df) > 0:
        print(f"Total MISS desde BackEnd: {len(misses)} ({(len(misses)/len(df))*100:.1f}%)")
        print(f"Total HIT desde Caché: {len(hits)} ({(len(hits)/len(df))*100:.1f}%)")
        print(f"Errores: {len(errores)}")
        print("-" * 40)
        
        if not misses.empty:
            print(f"Latencia promedio MISS: {misses['latencia_segundos'].mean():.4f} segundos")
        if not hits.empty:
            print(f"Latencia promedio HIT:  {hits['latencia_segundos'].mean():.4f} segundos")
            
            if not misses.empty and misses['latencia_segundos'].mean() > 0:
                mejora = misses['latencia_segundos'].mean() / hits['latencia_segundos'].mean()
                print(f"La caché es {mejora:.1f} veces más rápida que el backend")

except FileNotFoundError:
    print("No se encontró el archivo metricas.csv. ¡Corre el generador de tráfico primero!")