import os
import pandas as pd
from google.cloud import bigquery

# ==========================================
# 1. CONFIGURACIÓN Y CREDENCIALES
# ==========================================
# Si no configuraste la variable en el sistema, descomenta la siguiente línea:
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\Users\\Admin\\Downloads\\planta-de-pinturas-3847032b0596.json"

PROJECT_ID = "planta-de-pinturas"
DATASET_ID = "produccion"
TABLE_ID = "bitacora_de_paros"

# Archivo de entrada y columnas a procesar
CSV_FILE = ".\\data\\clean\\bitacora_mantenimiento_paros_fechas_limpia.csv"
COL_INICIO = "fecha_hora_inicio_paro"
COL_FIN = "fecha_hora_fin_paro"

# Referencia completa a la tabla en BigQuery
table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

# ==========================================
# 2. LECTURA Y LIMPIEZA CON PANDAS
# ==========================================
print(f"1. Leyendo archivo local: {CSV_FILE}...")
df = pd.read_csv(CSV_FILE)

print("2. Limpiando y estandarizando timestamps...")

def limpiar_timestamp(columna):
    #  Reemplazar puntos por dos puntos para normalizar horas como 20.45 -> 20:45
    columna_normalizada = columna.astype(str).str.replace('.', ':', regex=False)
    # Convierte múltiples formatos a datetime de Pandas
    fechas = pd.to_datetime(
        columna_normalizada,
        format='mixed',    # Soporta formatos mixtos
        dayfirst=True,     # Asume DD/MM/YYYY en fechas ambiguas (cambia a False si es EE.UU.)
        utc=True,          # Normaliza zonas horarias
        errors='coerce'    # Si hay texto corrupto, lo convierte a NaN (NULL)
    )
    # Convierte de vuelta a cadena en formato ISO estándar para BigQuery
    return fechas.dt.strftime('%Y-%m-%d %H:%M:%S')

# Aplicar la limpieza a ambas columnas
df[COL_INICIO] = limpiar_timestamp(df[COL_INICIO])
df[COL_FIN] = limpiar_timestamp(df[COL_FIN])
print(df[df["id_registro"]==29][[COL_INICIO, COL_FIN]].head())

# ==========================================
# 3. CARGA DIRECTA A BIGQUERY
# ==========================================
print(f"3. Conectando a BigQuery para subir a {table_ref}...")
client = bigquery.Client(project=PROJECT_ID)

# Configurar cómo se comportará la carga
job_config = bigquery.LoadJobConfig(
    # Detecta los tipos de datos del DataFrame (INTEGER, STRING, TIMESTAMP, etc.)
    autodetect=True,
    
    # Comportamiento de la tabla:
    # WRITE_TRUNCATE -> Sobrescribe la tabla entera
    # WRITE_APPEND   -> Añade las filas al final de la tabla
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
)

# Cargar el DataFrame procesado directamente en BigQuery
job = client.load_table_from_dataframe(
    df, 
    destination=table_ref, 
    job_config=job_config
)

# Esperar a que la tarea termine
job.result()

# ==========================================
# 4. CONFIRMACIÓN
# ==========================================
tabla_resultado = client.get_table(table_ref)
print("--------------------------------------------------")
print(f"¡Proceso completado con éxito!")
print(f"Tabla cargada: {TABLE_ID}")
print(f"Total de filas registradas: {tabla_resultado.num_rows}")
print("--------------------------------------------------")