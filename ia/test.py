import polars as pl

data1_path = r"C:\Users\oak\ti\api-fastapi-login-example\datasets\processed_docs\chunks_procesados.parquet"
data1 = pl.read_parquet(data1_path)
print(data1.head())
print("Número total de filas:", data1.height)
