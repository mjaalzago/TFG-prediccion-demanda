"""
Obtención de datos meteorológicos desde la API de Open-Meteo.

Implementa una lógica condicional que selecciona la fuente de datos
apropiada en función de la fecha solicitada:

- Fechas pasadas: API histórica (datos meteorológicos reales).
- Fechas en los próximos 16 días: API de forecast (previsión real).
- Fechas a más de 16 días en el futuro: valores medios estacionales.

En caso de fallo de la API, se utilizan valores medios de fallback
y se notifica al usuario.
"""

from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st

# Coordenadas geográficas de Londres (sede del caso de estudio)
LATITUD_LONDRES = 51.5074
LONGITUD_LONDRES = -0.1278

# Valores medios de fallback (precipitación en mm/día, viento en m/s)
PRECIPITACION_MEDIA = 0.0
VIENTO_MEDIO = 4.5

# Endpoints de Open-Meteo
URL_HISTORICA = "https://archive-api.open-meteo.com/v1/archive"
URL_FORECAST = "https://api.open-meteo.com/v1/forecast"


def _llamar_api_historica(fecha_inicio, fecha_fin):
    """
    Recupera datos meteorológicos históricos de Open-Meteo.

    La API histórica acepta fechas pasadas con un retardo aproximado de
    cinco días respecto a hoy.
    """
    params = {
        "latitude": LATITUD_LONDRES,
        "longitude": LONGITUD_LONDRES,
        "start_date": fecha_inicio.strftime("%Y-%m-%d"),
        "end_date": fecha_fin.strftime("%Y-%m-%d"),
        "daily": "precipitation_sum,wind_speed_10m_max",
        "timezone": "Europe/London",
        "wind_speed_unit": "ms",
    }
    respuesta = requests.get(URL_HISTORICA, params=params, timeout=10)
    respuesta.raise_for_status()
    return respuesta.json()


def _llamar_api_forecast(fecha_inicio, fecha_fin):
    """
    Recupera previsión meteorológica de Open-Meteo (hasta 16 días).
    """
    params = {
        "latitude": LATITUD_LONDRES,
        "longitude": LONGITUD_LONDRES,
        "start_date": fecha_inicio.strftime("%Y-%m-%d"),
        "end_date": fecha_fin.strftime("%Y-%m-%d"),
        "daily": "precipitation_sum,wind_speed_10m_max",
        "timezone": "Europe/London",
        "wind_speed_unit": "ms",
    }
    respuesta = requests.get(URL_FORECAST, params=params, timeout=10)
    respuesta.raise_for_status()
    return respuesta.json()


def _construir_dataframe(datos_api, fechas):
    """Convierte la respuesta de Open-Meteo en un DataFrame con las columnas esperadas."""
    df = pd.DataFrame({
        "ds": pd.to_datetime(datos_api["daily"]["time"]),
        "precipitacion_total_serv": datos_api["daily"]["precipitation_sum"],
        "viento_medio_serv": datos_api["daily"]["wind_speed_10m_max"],
    })
    # Reindexamos por las fechas solicitadas y rellenamos posibles huecos
    df = df.set_index("ds").reindex(fechas).reset_index()
    df = df.rename(columns={"index": "ds"})
    df["precipitacion_total_serv"] = df["precipitacion_total_serv"].fillna(PRECIPITACION_MEDIA)
    df["viento_medio_serv"] = df["viento_medio_serv"].fillna(VIENTO_MEDIO)
    return df


def _construir_dataframe_fallback(fechas):
    """Construye un DataFrame con valores medios cuando la API no está disponible."""
    return pd.DataFrame({
        "ds": fechas,
        "precipitacion_total_serv": [PRECIPITACION_MEDIA] * len(fechas),
        "viento_medio_serv": [VIENTO_MEDIO] * len(fechas),
    })


@st.cache_data(ttl=3600)
def obtener_clima(fecha_inicio, fecha_fin):
    """
    Obtiene los datos meteorológicos para el periodo solicitado.

    Devuelve una tupla (DataFrame, fuente, mensaje) donde:
    - DataFrame contiene las columnas ds, precipitacion_total_serv y viento_medio_serv.
    - fuente indica de dónde provienen los datos: 'historico', 'forecast',
      'estacional' o 'fallback'.
    - mensaje contiene un texto explicativo para mostrar al usuario.

    El resultado se cachea durante una hora para evitar llamadas innecesarias.
    """
    hoy = date.today()
    limite_forecast = hoy + timedelta(days=16)
    fechas = pd.date_range(start=fecha_inicio, end=fecha_fin, freq="D")

    # Caso 1: el periodo entero está en el pasado
    if fecha_fin < hoy:
        try:
            datos = _llamar_api_historica(fecha_inicio, fecha_fin)
            df = _construir_dataframe(datos, fechas)
            mensaje = (
                f"Datos meteorológicos reales obtenidos de Open-Meteo "
                f"para el periodo solicitado."
            )
            return df, "historico", mensaje
        except Exception:
            df = _construir_dataframe_fallback(fechas)
            mensaje = (
                "No se pudo conectar con la API meteorológica. La predicción "
                "se ha generado con valores medios de fallback "
                f"(precipitación {PRECIPITACION_MEDIA} mm/día, "
                f"viento {VIENTO_MEDIO} m/s) y puede perder fiabilidad."
            )
            return df, "fallback", mensaje

    # Caso 2: el periodo entero está dentro de la ventana de forecast (16 días)
    if fecha_inicio >= hoy and fecha_fin <= limite_forecast:
        try:
            datos = _llamar_api_forecast(fecha_inicio, fecha_fin)
            df = _construir_dataframe(datos, fechas)
            mensaje = (
                f"Previsión meteorológica obtenida de Open-Meteo "
                f"para el periodo solicitado."
            )
            return df, "forecast", mensaje
        except Exception:
            df = _construir_dataframe_fallback(fechas)
            mensaje = (
                "No se pudo conectar con la API meteorológica. La predicción "
                "se ha generado con valores medios de fallback "
                f"(precipitación {PRECIPITACION_MEDIA} mm/día, "
                f"viento {VIENTO_MEDIO} m/s) y puede perder fiabilidad."
            )
            return df, "fallback", mensaje

    # Caso 3: el periodo está más allá del horizonte de forecast (>16 días)
    df = _construir_dataframe_fallback(fechas)
    mensaje = (
        f"El periodo solicitado se sitúa más allá de los 16 días que cubre "
        f"la previsión meteorológica de Open-Meteo. La predicción utiliza "
        f"valores medios estacionales (precipitación {PRECIPITACION_MEDIA} mm/día, "
        f"viento {VIENTO_MEDIO} m/s)."
    )
    return df, "estacional", mensaje