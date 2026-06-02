import pandas as pd
import numpy as np

try:
    print("Cargando datos...")
    df = pd.read_csv('metricas.csv')
    
    hits = df[df['evento'] == 'HIT']
    misses = df[df['evento'] == 'MISS']
    errores = df[df['evento'] == 'ERROR']
    
    total = len(df)
    
    print("\n" + "=" * 55)
    print("REPORTE DE RENDIMIENTO DEL SISTEMA (KAFKA + CACHÉ)")
    print("=" * 55)
    print(f"Total de peticiones procesadas registradas: {total}")
    
    if total > 0:
        hit_rate = (len(hits) / total) * 100
        miss_rate = (len(misses) / total) * 100
        
        print(f"\nTotal HIT (desde Caché):   {len(hits)} ({hit_rate:.1f}%)")
        print(f"Total MISS (desde Backend): {len(misses)} ({miss_rate:.1f}%)")
        print(f"Errores:                    {len(errores)}")
        print("-" * 55)
        
        if not misses.empty:
            print(f"Latencia promedio MISS (Backend): {misses['latencia_segundos'].mean():.4f} segundos")
        if not hits.empty:
            print(f"Latencia promedio HIT (Caché):    {hits['latencia_segundos'].mean():.4f} segundos")
            
            if not misses.empty and misses['latencia_segundos'].mean() > 0:
                mejora = misses['latencia_segundos'].mean() / hits['latencia_segundos'].mean()
                print(f"Impacto: La caché es {mejora:.1f} veces más rápida que el backend.")
        
        print("-" * 55)
        print("ANÁLISIS AVANZADO")
        if 'latencia_segundos' in df.columns:
            # El p95 nos dice el tiempo máximo que esperó el 95% de los usuarios
            p95 = np.percentile(df['latencia_segundos'].dropna(), 95)
            print(f"P95 (El 95% de las peticiones tardaron menos de): {p95:.4f} seg")
        
        # Comparación de distribuciones
        if total >= 200:
            print("\nRENDIMIENTO POR TIPO DE TRÁFICO (Últimas 200 peticiones)")
            print("   (Demostración del calentamiento de caché)")
            
            # Se toma el último bloque de 100 (Zipf) y el penúltimo (Uniforme)
            df_uniforme = df.iloc[-200:-100]
            df_zipf = df.iloc[-100:]
            
            hit_rate_uni = (len(df_uniforme[df_uniforme['evento'] == 'HIT']) / 100) * 100
            hit_rate_zipf = (len(df_zipf[df_zipf['evento'] == 'HIT']) / 100) * 100
            
            print(f"   ➤ Distribución UNIFORME (Azar):    Cache Hit Rate = {hit_rate_uni:.1f}%")
            print(f"   ➤ Distribución ZIPF (Tendencias):  Cache Hit Rate = {hit_rate_zipf:.1f}%")

except FileNotFoundError:
    print("No se encontró el archivo metricas.csv")
except Exception as e:
    print(f"Ocurrió un error inesperado al leer las métricas: {e}")
