"""
Carga de festivos para el panel y los notebooks.

Permite obtener festivos nacionales y regionales mediante la librería
holidays, y añadir festivos locales definidos en la configuración.
Se utiliza tanto en el entrenamiento del modelo (notebooks) 
como en la visualización del panel (Streamlit).
"""

import pandas as pd
import holidays


def cargar_festivos(
    pais_codigo: str,
    subdivision: str = None,
    años: range = None,
    festivos_locales: list[tuple[str, str]] = None,
) -> pd.DataFrame:
    """
    Carga los festivos para un país y opcionalmente una subdivisión,
    permitiendo añadir festivos locales.

    Parámetros
    ----------
    pais_codigo : código ISO del país (ej. 'GB', 'ES').
    subdivision : código de la subdivisión regional (ej. 'ENG', 'MD').
                  None para festivos nacionales únicamente.
    años : rango de años a incluir.
    festivos_locales : lista de tuplas (fecha, nombre) con
                       festivos locales (son opcionales).
    
    Devuelve
    --------
    DataFrame con columnas 'fecha' (datetime64) y 'festivo_nombre',
    ordenado cronológicamente y sin duplicados por fecha.
    """
    festivos_lib = holidays.country_holidays(
        pais_codigo,
        subdiv=subdivision,
        years=años,
    )

    filas = [(fecha, nombre) for fecha, nombre in festivos_lib.items()]

    if festivos_locales:
        filas.extend(festivos_locales)

    df = pd.DataFrame(filas, columns=["fecha", "festivo_nombre"])
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = (
        df
        .drop_duplicates(subset=["fecha"])
        .sort_values("fecha")
        .reset_index(drop=True)
    )

    return df