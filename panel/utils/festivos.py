"""
Carga de festivos para el panel y los notebooks.

Permite obtener festivos nacionales y regionales mediante la librería
holidays, y añadir festivos personalizados (festivos locales 
municipales o festividades sociales recurrentes) definidos en la 
configuración. Se utiliza tanto en el entrenamiento del modelo
(notebooks) como en la visualización del panel (Streamlit).
"""

import pandas as pd
import holidays


def cargar_festivos(
    pais_codigo: str,
    subdivision: str = None,
    años: range = None,
    festivos_personalizados: list[tuple[str, str]] = None,
) -> pd.DataFrame:
    """
    Carga los festivos para un país y opcionalmente una subdivisión,
    permitiendo añadir festivos personalizados.

    Los festivos personalizados pueden tener dos formatos de fecha:
    - "YYYY-MM-DD": fecha específica de un año concreto, útil para
      festividades de fecha variable como el Mother's Day del Reino
      Unido (cuarto domingo de Cuaresma).
    - "MM-DD": fecha recurrente anual, el sistema la expande
      automáticamente a todos los años del rango proporcionado.
      Útil para festividades de fecha fija como San Valentín o 
      Nochebuena.

    Parámetros
    ----------
    pais_codigo : código ISO del país (ej. 'GB', 'ES').
    subdivision : código de la subdivisión regional (ej. 'ENG', 'MD').
                  None para festivos nacionales únicamente.
    años : rango de años a incluir.
    festivos_personalizados : lista de tuplas (fecha, nombre) con
                              festividades no recogidas en la 
                              librería: festivos locales municipales
                              o festividades sociales recurrentes.
                              La fecha admite los formatos 
                              "YYYY-MM-DD" o "MM-DD".

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

    if festivos_personalizados:
        for fecha_str, nombre in festivos_personalizados:
            if len(fecha_str) == 5 and fecha_str.count("-") == 1:
                # Formato MM-DD: recurrente anual, expandir a todos los años
                for año in años:
                    filas.append((f"{año}-{fecha_str}", nombre))
            elif len(fecha_str) == 10 and fecha_str.count("-") == 2:
                # Formato YYYY-MM-DD: fecha específica
                filas.append((fecha_str, nombre))
            else:
                raise ValueError(
                    f"Formato de fecha no reconocido: '{fecha_str}'. "
                    f"Use 'MM-DD' para recurrentes anuales o "
                    f"'YYYY-MM-DD' para fechas específicas."
                )

    df = pd.DataFrame(filas, columns=["fecha", "festivo_nombre"])
    df["fecha"] = pd.to_datetime(df["fecha"])
    df = (
        df
        .drop_duplicates(subset=["fecha"])
        .sort_values("fecha")
        .reset_index(drop=True)
    )

    return df