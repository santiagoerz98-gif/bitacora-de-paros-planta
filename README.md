# 🏭 Industrial Downtime Analytics & Pipeline: De Datos Crudos a Decisiones Operativas

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Google BigQuery](https://img.shields.io/badge/Google_BigQuery-4285F4?style=for-the-badge&logo=googlecloud&logoColor=white)](https://cloud.google.com/bigquery)
[![SQL](https://img.shields.io/badge/SQL-Analytics-CC292B?style=for-the-badge&logo=microsoftsqlserver&logoColor=white)](#)
[![Power BI](https://img.shields.io/badge/Power_BI-Dashboard-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](#)

## 📌 Descripción del Proyecto

En el sector industrial, uno de los principales retos analíticos es transformar las bitácoras operativas registradas en texto libre en KPIs accionables. La falta de estandarización frena la toma de decisiones e impide identificar la verdadera causa raíz de las pérdidas de productividad.

Este proyecto implementa una solución **End-to-End** que automatiza la ingesta, limpieza, estructuración y visualización de datos de paro de planta. El pipeline procesa registros manuales desordenados en un archivo CSV crudo y los transforma en un **Dashboard Ejecutivo en Power BI** impulsado por la potencia de **Google BigQuery**.

---

## 🏗️ Arquitectura de Datos & Pipeline
```markdown
┌─────────────────┐       ┌───────────────────────────┐       ┌───────────────────────────┐       ┌───────────────────────────┐
│                 │       │                           │       │                           │       │                           │
│  CSV Crudo      │ ────> │  Python Script            │ ────> │  Google BigQuery          │ ────> │  Power BI Dashboard       │
│  (Texto Libre)  │       │  (Pandas / Regex / Clean) │       │  (Data Warehouse & Views) │       │  (Import Directo & UX)    │
│                 │       │                           │       │                           │       │                           │
└─────────────────┘       └───────────────────────────┘       └───────────────────────────┘       └───────────────────────────┘

```

```

```
1. **Ingesta y Procesamiento (Python):** 
   - Parseo y estandarización de campos de fecha y tiempos de paro.
   - Normalización de texto libre mediante expresiones regulares (Regex) y categorización automática de causas operativas en motivos estructurados.
2. **Almacenamiento en la Nube (Google BigQuery):**
   - Carga automatizada del dataset procesado hacia el Data Warehouse.
   - Creación de **Vistas Analíticas (`CREATE VIEW`)** escritas en SQL para precalcular KPIs operativos y la lógica acumulada de la Regla de Pareto (80/20).
3. **Visualización & BI (Power BI):**
   - Conexión e importación directa de las vistas de BigQuery para garantizar alto rendimiento de procesamiento.
   - Interfaz ejecutiva en *Dark Mode* con matriz de calor por Área/Turno y Diagrama de Pareto interactivo.

---

## 📂 Estructura del Repositorio

```text
├── data/
│   ├── raw_downtime.csv            # Dataset original con texto libre y fechas sin formato
│   └── cleaned_downtime.csv        # Dataset procesado listo para carga
├── python/
│   ├── main_pipeline.py            # Script principal de ETL y limpieza con Pandas/Regex
│   └── bigquery_uploader.py        # Módulo de carga automatizada hacia GCP BigQuery
├── sql/
│   ├── 01_vw_bitacora_limpia.sql   # Vista base con tipado y filtrado
│   ├── 02_vw_kpis_operativos.sql   # Consultas de agregación por Área y Turno
│   └── 03_vw_pareto_causas.sql     # Vista con ordenamiento y % acumulado (80/20)
├── pbix/
│   └── Dashboard_Paros_Planta.pbix # Reporte interactivo de Power BI
├── docs/
│   └── arquitectura_pipeline.png   # Diagrama explicativo del proceso
├── README.md                       # Documentación del proyecto
└── requirements.txt                # Librerías de Python requeridas
