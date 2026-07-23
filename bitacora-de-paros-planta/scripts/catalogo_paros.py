"""
construir_catalogo_motivos_paro.py

Fase 2 del proyecto de analítica de pinturas: Catálogo de motivos de paro.

Este script:
1. Carga la bitácora de mantenimiento y paros (texto libre, no estandarizado).
2. Normaliza el texto libre (minúsculas, sin tildes, sin espacios/ruido extra).
3. Genera el catálogo estandarizado dim_motivo_paro.csv.
4. Mapea cada registro de la bitácora a un motivo_paro_id, primero con reglas
   de palabras clave (regex) y, como respaldo, con coincidencia difusa
   (difflib, sin dependencias externas) para tolerar errores de tipeo.
5. Guarda la bitácora enriquecida con motivo_paro_id y un reporte de calidad.

Uso:
    python construir_catalogo_motivos_paro.py
"""

import re
import unicodedata
from pathlib import Path

import pandas as pd
from difflib import SequenceMatcher

# ---------------------------------------------------------------------------
# Configuración de rutas
# ---------------------------------------------------------------------------
RUTA_BITACORA = Path("C:\\Users\\Admin\\Desktop\\Planta de pinturas y recubrimientos\\data\\raw\\bitacora_mantenimiento_paros.csv")
RUTA_SALIDA_CATALOGO = Path("dim_motivo_paro.csv")
RUTA_SALIDA_BITACORA = Path("bitacora_mantenimiento_paros_mapeada.csv")
RUTA_SALIDA_ERRORES = Path("reporte_errores_mapeo_motivos.csv")
RUTA_SALIDA_REPORTE_TXT = Path("reporte_calidad_mapeo_motivos.txt")

UMBRAL_FUZZY = 0.72  # similitud mínima (0-1) para aceptar un match por coincidencia difusa


# ---------------------------------------------------------------------------
# 1. Catálogo estandarizado (dim_motivo_paro)
# ---------------------------------------------------------------------------
CATALOGO = [
    # motivo_paro_id, motivo_estandarizado, categoria, descripcion
    (1, "Falla mecánica", "Mecánico",
     "Paro por rotura, desgaste o falla física de un componente de la máquina (rodamientos, ejes, piezas)."),
    (2, "Falla eléctrica", "Eléctrico",
     "Paro por corte de energía, cortocircuito, fusibles o fallas en el tablero eléctrico."),
    (3, "Falta de materia prima", "Insumos",
     "Paro por ausencia o insuficiencia de materia prima, solventes u otros insumos."),
    (4, "Falta de personal / operario", "Personal",
     "Paro por ausencia, insuficiencia de personal o reasignación del operario a otra tarea."),
    (5, "Problema de calidad / reproceso", "Calidad",
     "Paro por producto fuera de especificación, defectos detectados o necesidad de reproceso."),
    (6, "Cambio de formato / setup", "Planificado",
     "Paro planificado por cambio de color, envase, producto o ajuste de máquina para el siguiente lote."),
    (7, "Limpieza / sanitización", "Planificado",
     "Paro planificado para lavado o limpieza de tanques, líneas o equipos."),
    (8, "Mantenimiento preventivo", "Planificado",
     "Paro planificado por mantenimiento, lubricación o revisión de rutina programada."),
    (9, "Espera de instrucciones / planificación", "Planificado",
     "Paro por falta de orden de producción, instrucciones del supervisor o aprobación pendiente."),
    (10, "Otro / no especificado", "Otro",
     "Paro sin motivo registrado, ambiguo o que no corresponde a ninguna otra categoría."),
]

df_catalogo = pd.DataFrame(
    CATALOGO, columns=["motivo_paro_id", "motivo_estandarizado", "categoria", "descripcion"]
)


# ---------------------------------------------------------------------------
# 2. Reglas de palabras clave por motivo estandarizado.
#    Se aplican sobre el texto ya normalizado y sin ruido; la primera regla
#    que haga match gana (el orden de este diccionario importa).
# ---------------------------------------------------------------------------
REGLAS_KEYWORDS = {
    # Se revisa primero para no dejar que palabras genéricas ("operario", etc.)
    # de otras categorías capturen frases que en realidad no informan un motivo.
    "Otro / no especificado": [
        r"no indicado", r"no indica", r"sin motivo", r"motivo no registrado",
        r"pendiente de detalle", r"sin especificar", r"no especificado", r"^otro$",
    ],
    "Falla mecánica": [
        r"falla\s*mec", r"vibracion anormal", r"roda\s*miento", r"rotura",
        r"pieza rota", r"mecanic", r"correa", r"fuga de aceite", r"hidraulico",
    ],
    "Falla eléctrica": [
        r"electric", r"\belect\b", r"energia", r"fusible", r"termico", r"cortocircuito",
        r"tablero", r"voltaje", r"fluctuacion",
    ],
    "Falta de materia prima": [
        r"materia prima", r"\bmp\b", r"m\.p\.", r"insumo", r"proveedor", r"pigmento",
        r"solvente", r"resina",
    ],
    "Falta de personal / operario": [
        r"ausent", r"a\s*usent", r"personal insuficiente", r"operario", r"operador",
        r"mano de obra", r"falta.*turno", r"turno demorado", r"falta de personal",
    ],
    "Problema de calidad / reproceso": [
        r"reproceso", r"defecto", r"fuera de especificacion", r"control de calidad",
        r"no conforme", r"correccion de formula", r"fuera de rango", r"no cumple especificacion",
        r"falla de calidad",
    ],
    "Cambio de formato / setup": [
        r"cambio de color", r"cambio de envase", r"seteo", r"setup", r"cambio de boquilla",
        r"ca\s*mbio de boquilla", r"ajuste.*lote", r"preparacion de maquina", r"nuevo lote",
        r"cambio de formato",
    ],
    "Limpieza / sanitización": [
        r"lavado", r"limpieza", r"\bcip\b", r"sanitiza", r"\baseo\b",
    ],
    "Mantenimiento preventivo": [
        r"lubricacion", r"revision de rutina", r"revision periodica", r"mantenimiento preventivo",
        r"mantenimiento planificado", r"ma\s*ntenimiento", r"chequeo preventivo", r"mantto preventivo", r"cambio de aceite",
        r"\bmtto\b", r"segun plan", r"cambio de filtros",
    ],
    "Espera de instrucciones / planificación": [
        r"esperando instruccion", r"sin orden de produccion", r"instruccion de supervisor",
        r"aprobacion de laboratorio", r"sin programa de produccion", r"esperando definicion",
        r"instrucciones claras", r"reprogramacion", r"a la espera", r"esperando aprobacion",
    ],
}
# Cualquier texto vacío / "nan" / no clasificado por lo anterior ni por el
# respaldo difuso cae también en "Otro / no especificado".


# ---------------------------------------------------------------------------
# Funciones de normalización y mapeo
# ---------------------------------------------------------------------------
def quitar_tildes(texto: str) -> str:
    """Elimina tildes/diacríticos conservando la letra base (á -> a)."""
    return "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )


def normalizar_texto(texto) -> str:
    """Normaliza un texto libre: minúsculas, sin tildes, sin símbolos ni espacios extra."""
    if pd.isna(texto):
        return ""
    texto = str(texto).lower()
    texto = quitar_tildes(texto)
    texto = re.sub(r"[^\w\s/.\-]", " ", texto)  # símbolos raros -> espacio
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto


def quitar_ruido(texto: str) -> str:
    """Quita modificadores frecuentes que no aportan al motivo (urgencia, turno, recurrencia)."""
    patrones_ruido = [
        r"\burgente\b", r"\bleve\b",
        r"turno\s*(noche|dia|tarde)",
        r"\(?\d+.?(da|ra)\s*vez\s*esta\s*semana\)?",
        r"en linea [a-z]\b",
        r"ver detalle abajo", r"ver observaciones",
    ]
    for patron in patrones_ruido:
        texto = re.sub(patron, " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def clasificar_por_keywords(texto_normalizado: str):
    """Devuelve el motivo_estandarizado si alguna keyword hace match, si no None."""
    for motivo, patrones in REGLAS_KEYWORDS.items():
        for patron in patrones:
            if re.search(patron, texto_normalizado):
                return motivo
    return None


def clasificar_por_fuzzy(texto_normalizado: str, ejemplos_por_motivo: dict):
    """
    Respaldo para textos que no matchean ninguna keyword (ej. errores de tipeo
    fuertes). Compara contra frases representativas de cada motivo usando
    similitud de secuencia (difflib), sin depender de librerías externas.
    """
    mejor_motivo, mejor_score = None, 0.0
    for motivo, ejemplos in ejemplos_por_motivo.items():
        for ejemplo in ejemplos:
            score = SequenceMatcher(None, texto_normalizado, ejemplo).ratio()
            if score > mejor_score:
                mejor_motivo, mejor_score = motivo, score
    if mejor_score >= UMBRAL_FUZZY:
        return mejor_motivo, mejor_score
    return None, mejor_score


def clasificar_texto(texto_libre, ejemplos_por_motivo):
    """Devuelve (motivo_estandarizado, metodo_usado, confianza) para un texto libre."""
    normalizado = normalizar_texto(texto_libre)
    limpio = quitar_ruido(normalizado)

    if not limpio or limpio in {"nan", "otro", "n a", "na"}:
        return "Otro / no especificado", "vacio_o_generico", 1.0

    motivo = clasificar_por_keywords(limpio)
    if motivo:
        return motivo, "keyword", 1.0

    motivo, score = clasificar_por_fuzzy(limpio, ejemplos_por_motivo)
    if motivo:
        return motivo, "fuzzy", round(score, 2)

    return "Otro / no especificado", "sin_match", 0.0


# Frases "semilla" para el respaldo fuzzy (una muestra representativa por motivo)
EJEMPLOS_POR_MOTIVO = {
    "Falla mecánica": [
        "falla mecanica", "vibracion anormal se detuvo por precaucion", "rotura de rodamiento",
        "correa cortada", "fuga de aceite hidraulico",
    ],
    "Falla eléctrica": [
        "falla electrica", "problema electrico se llamo a electricista", "se quemo un fusible",
        "fluctuacion de voltaje", "falla elect panel control",
    ],
    "Falta de materia prima": [
        "falta de materia prima", "falta de mp", "esperando material del proveedor",
        "no llego la resina a tiempo",
    ],
    "Falta de personal / operario": [
        "operario ausente", "personal insuficiente", "sin operador disponible", "cambio de turno demorado",
    ],
    "Problema de calidad / reproceso": [
        "reproceso por color no conforme", "producto fuera de especificacion",
        "falla de calidad detectada por supervisor",
    ],
    "Cambio de formato / setup": [
        "cambio de color en linea", "seteo de linea", "cambio de boquilla",
        "cambio de formato", "preparacion de maquina",
    ],
    "Limpieza / sanitización": ["lavado de tanque", "limpieza fin de turno", "limpieza cip", "aseo de linea"],
    "Mantenimiento preventivo": [
        "lubricacion general", "revision de rutina", "mantenimiento preventivo programado",
        "mtto preventivo segun plan", "cambio de filtros programado",
    ],
    "Espera de instrucciones / planificación": [
        "esperando instrucciones", "sin orden de produccion", "a la espera de planificacion",
        "parada por reprogramacion",
    ],
}


# ---------------------------------------------------------------------------
# Proceso principal
# ---------------------------------------------------------------------------
def main():
    df = pd.read_csv(RUTA_BITACORA, encoding="utf-8-sig")

    df["motivo_texto_normalizado"] = df["motivo_paro_texto_libre"].apply(normalizar_texto)
    df["motivo_texto_limpio"] = df["motivo_texto_normalizado"].apply(quitar_ruido)

    resultados = df["motivo_texto_limpio"].apply(lambda t: clasificar_texto(t, EJEMPLOS_POR_MOTIVO))
    df["motivo_estandarizado"] = resultados.apply(lambda r: r[0])
    df["metodo_mapeo"] = resultados.apply(lambda r: r[1])
    df["confianza_mapeo"] = resultados.apply(lambda r: r[2])

    df = df.merge(
        df_catalogo[["motivo_paro_id", "motivo_estandarizado", "categoria"]],
        on="motivo_estandarizado", how="left",
    )

    # --- Validación contra la columna de referencia (solo existe en el dataset simulado) ---
    if "_categoria_real_referencia" in df.columns:
        df["coincide_referencia"] = df["motivo_estandarizado"] == df["_categoria_real_referencia"]
        aciertos = int(df["coincide_referencia"].sum())
        total = len(df)
        pct = aciertos / total * 100

        lineas = []
        lineas.append(f"Registros totales: {total}")
        lineas.append(f"Aciertos vs _categoria_real_referencia: {aciertos} ({pct:.1f}%)")
        lineas.append("")
        lineas.append("Registros por método de mapeo usado:")
        lineas.append(df["metodo_mapeo"].value_counts().to_string())
        lineas.append("")
        lineas.append("Aciertos por método de mapeo:")
        lineas.append(df.groupby("metodo_mapeo")["coincide_referencia"].agg(["sum", "count"]).to_string())
        lineas.append("")
        lineas.append("Matriz de confusión (filas=referencia real, columnas=mapeo obtenido):")
        matriz = pd.crosstab(df["_categoria_real_referencia"], df["motivo_estandarizado"])
        lineas.append(matriz.to_string())
        lineas.append("")

        errores = df[~df["coincide_referencia"]][
            ["id_registro", "motivo_paro_texto_libre", "motivo_texto_limpio",
             "motivo_estandarizado", "_categoria_real_referencia", "metodo_mapeo", "confianza_mapeo"]
        ]
        lineas.append(f"Registros mal clasificados ({len(errores)}) — revisar manualmente:")
        lineas.append(errores.to_string(index=False))

        reporte_texto = "\n".join(lineas)
        RUTA_SALIDA_REPORTE_TXT.write_text(reporte_texto, encoding="utf-8")
        errores.to_csv(RUTA_SALIDA_ERRORES, index=False, encoding="utf-8-sig")

        print(reporte_texto)
    else:
        print("Columna _categoria_real_referencia no encontrada: se omite la validación automática.")

    # --- Guardar catálogo y bitácora enriquecida ---
    df_catalogo.to_csv(RUTA_SALIDA_CATALOGO, index=False, encoding="utf-8-sig")

    columnas_salida = [
        "id_registro", "maquina_id", "nombre_maquina", "area_planta", "turno",
        "fecha_hora_inicio_paro", "fecha_hora_fin_paro", "duracion_minutos_estimada",
        "operario_reporta", "motivo_paro_texto_libre", "motivo_paro_id",
        "motivo_estandarizado", "categoria", "metodo_mapeo", "confianza_mapeo", "observaciones",
    ]
    df[columnas_salida].to_csv(RUTA_SALIDA_BITACORA, index=False, encoding="utf-8-sig")

    print(f"\nCatálogo guardado en: {RUTA_SALIDA_CATALOGO.resolve()}")
    print(f"Bitácora mapeada guardada en: {RUTA_SALIDA_BITACORA.resolve()}")


if __name__ == "__main__":
    main()