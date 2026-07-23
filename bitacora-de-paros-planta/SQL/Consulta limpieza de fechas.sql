CREATE OR REPLACE TABLE `planta-de-pinturas.produccion.bitacora_de_paros` AS
SELECT 
  -- 1. Traemos todas las columnas MENOS las que vamos a modificar
  * EXCEPT(fecha_hora_inicio_paro, fecha_hora_fin_paro,fecha_hora_inicio_paro_limpia,fecha_hora_fin_paro_limpia),
  
  -- 2. Convertimos las de texto a TIMESTAMP
  SAFE_CAST(fecha_hora_inicio_paro_limpia AS TIMESTAMP) AS timestamp_inicio_paro,
  SAFE_CAST(fecha_hora_fin_paro_limpia AS TIMESTAMP) AS timestamp_fin_paro

FROM `planta-de-pinturas.produccion.bitacora_de_paros`;