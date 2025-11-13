import polars as pl

# Ruta del archivo parquet
data1_path = r"C:\Users\oak\ti\api-fastapi-login-example\datasets\processed_docs\chunks_procesados.parquet"

# Leer el archivo parquet
data1 = pl.read_parquet(data1_path)

# Imprimir las primeras líneas
print(data1.head())

# Imprimir el número de filas
print("Número total de filas:", data1.height)
