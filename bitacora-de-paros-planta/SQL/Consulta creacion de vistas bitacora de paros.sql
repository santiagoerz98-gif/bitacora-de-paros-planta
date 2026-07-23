-- Vista Base
CREATE OR REPLACE VIEW produccion.vw_bitacora_paros
AS (
  SELECT
    id_registro,
    maquina_id,
    nombre_maquina,
    area_planta,
    turno,
    categoria,
    motivo_estandarizado,
    timestamp_inicio_paro,
    timestamp_fin_paro,
    TIMESTAMP_DIFF(timestamp_fin_paro, timestamp_inicio_paro, MINUTE)
      AS duracion_paro_min
  FROM `produccion.bitacora_de_paros`
);

-- Vista del pareto
CREATE OR REPLACE VIEW `produccion.vw_pareto_categorias`
AS
WITH
  tiempo_perdido_por_categoria AS (
    SELECT
      categoria,
      SUM(duracion_paro_min) AS tiempo_perdido_categoria
    FROM `produccion.vw_bitacora_paros`
    GROUP BY categoria
    ORDER BY tiempo_perdido_categoria DESC
  ),
  acumulado_pareto AS (
    SELECT
      categoria,
      tiempo_perdido_categoria,
      SUM(tiempo_perdido_categoria)
        OVER (ORDER BY tiempo_perdido_categoria DESC)
        AS tiempo_perdido_acumulado,
      SUM(tiempo_perdido_categoria) OVER () AS tiempo_perdido_global
    FROM tiempo_perdido_por_categoria
    GROUP BY categoria, tiempo_perdido_categoria
  )
SELECT
  categoria,
  tiempo_perdido_categoria,
  ROUND(tiempo_perdido_acumulado / tiempo_perdido_global, 2) * 100
    AS pct_tiempo_perdido_acumulado,
  CASE
    WHEN (tiempo_perdido_acumulado / tiempo_perdido_global) <= 0.80
      THEN 'A (Alta relevancia / 80% del tiempo perdido)'
    WHEN (tiempo_perdido_acumulado / tiempo_perdido_global) <= 0.95
      THEN 'B (relevancia media / 15% del tiempo perdido)'
    ELSE 'C (Baja relevancia / 5% del tiempo perdido)'
    END AS clasificacion_abc
FROM acumulado_pareto
ORDER BY
  tiempo_perdido_categoria DESC;

-- Vista cuellos de botella
CREATE OR REPLACE VIEW `produccion.vw_cuellos_de_botella_area_turno`
AS
SELECT
  area_planta,
  turno,
  SUM(duracion_paro_min) AS tiempo_perdido_min,
FROM `produccion.vw_bitacora_paros`
GROUP BY area_planta, turno
QUALIFY
  row_number()
    OVER (PARTITION BY area_planta ORDER BY sum(duracion_paro_min) DESC)
  = 1
ORDER BY tiempo_perdido_min DESC;

-- Vista de KPIs por maquina

CREATE OR REPLACE VIEW `produccion.vw_kpis_por_maquina`
AS
SELECT
  maquina_id,
  nombre_maquina,
  area_planta,

  -- 1. Frecuencia: Número total de veces que la máquina se detuvo
  COUNT(id_registro) AS frecuencia_paros,

  -- 2. TTP: Tiempo Total Perdido en minutos
  SUM(duracion_paro_min) AS tiempo_total_perdido_min,

  -- 3. MTTR: Tiempo Medio de Reparación en minutos (Promedio por evento)
  ROUND(AVG(duracion_paro_min), 2) AS mttr_min
FROM `produccion.vw_bitacora_paros`
GROUP BY
  maquina_id,
  nombre_maquina,
  area_planta;
