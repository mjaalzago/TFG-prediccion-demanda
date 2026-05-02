"""
Obtención de datos meteorológicos desde la API de Open-Meteo.

Implementa una lógica condicional que selecciona la fuente de datos
apropiada en función de la fecha solicitada:

- Fechas pasadas: API histórica (datos meteorológicos reales).
- Fechas en los próximos 16 días: API de forecast (previsión real).
- Fechas a más de 16 días en el futuro: valores medios estacionales.

En caso de fallo de la API, se utilizan valores medios de fallback
y se notifica al usuario.

La ubicación geográfica y los valores de fallback se leen del fichero
de configuración (config.toml), lo que permite adaptar el panel a
distintos restaurantes sin modificar el código.
"""

from datetime import date, timedelta

import pandas as pd
import requests
import streamlit as st

from utils.config import cargar_configuracion


# Endpoints fijos de la API de Open-Meteo
URL_HISTORICA = "https://archive-api.open-meteo.com/v1/archive"
URL_FORECAST = "https://api.open-meteo.com/v1/forecast"

# Variables meteorológicas solicitadas a la API. Estas variables están
# acopladas a los regresores que utiliza el modelo Prophet, por lo que
# no se exponen en la configuración: cambiarlas implicaría reentrenar
# el modelo.
VARIABLES_DIARIAS = "precipitation_sum,wind_speed_10m_max"
UNIDAD_VIENTO = "ms"

# Ventana máxima de la API de forecast (limitación de Open-Meteo)
DIAS_FORECAST = 16


def _obtener_parametros_ubicacion():
    """Devuelve los parámetros de ubicación y unidades para la API."""
    config = cargar_configuracion()
    return {
        "latitude": config["restaurante"]["latitud"],
        "longitude": config["restaurante"]["longitud"],
        "timezone": config["restaurante"]["zona_horaria"],
        "wind_speed_unit": UNIDAD_VIENTO,
        "daily": VARIABLES_DIARIAS,
    }


def _obtener_valores_fallback():
    """Devuelve los valores medios de fallback configurados."""
    config = cargar_configuracion()
    return {
        "precipitacion": config["restaurante"]["precipitacion_media_mm"],
        "viento": config["restaurante"]["viento_medio_ms"],
    }


def _llamar_api_historica(fecha_inicio, fecha_fin):
    """
    Recupera datos meteorológicos históricos de Open-Meteo.

    La API histórica acepta fechas pasadas con un retardo aproximado de
    cinco días respecto a hoy.
    """
    params = _obtener_parametros_ubicacion()
    params["start_date"] = fecha_inicio.strftime("%Y-%m-%d")
    params["end_date"] = fecha_fin.strftime("%Y-%m-%d")
    respuesta = requests.get(URL_HISTORICA, params=params, timeout=10)
    respuesta.raise_for_status()
    return respuesta.json()


def _llamar_api_forecast(fecha_inicio, fecha_fin):
    """
    Recupera previsión meteorológica de Open-Meteo (hasta 16 días).
    """
    params = _obtener_parametros_ubicacion()
    params["start_date"] = fecha_inicio.strftime("%Y-%m-%d")
    params["end_date"] = fecha_fin.strftime("%Y-%m-%d")
    respuesta = requests.get(URL_FORECAST, params=params, timeout=10)
    respuesta.raise_for_status()
    return respuesta.json()


def _construir_dataframe(datos_api, fechas):
    """
    Convierte la respuesta de Open-Meteo en un DataFrame con las
    columnas esperadas por el modelo Prophet.
    """
    fallback = _obtener_valores_fallback()
    df = pd.DataFrame({
        "ds": pd.to_datetime(datos_api["daily"]["time"]),
        "precipitacion_total_serv": datos_api["daily"]["precipitation_sum"],
        "viento_medio_serv": datos_api["daily"]["wind_speed_10m_max"],
    })
    # Reindexamos por las fechas solicitadas y rellenamos posibles huecos
    df = df.set_index("ds").reindex(fechas).reset_index()
    df = df.rename(columns={"index": "ds"})
    df["precipitacion_total_serv"] = df["precipitacion_total_serv"].fillna(
        fallback["precipitacion"]
    )
    df["viento_medio_serv"] = df["viento_medio_serv"].fillna(
        fallback["viento"]
    )
    return df


def _construir_dataframe_fallback(fechas):
    """Construye un DataFrame con valores medios cuando la API no está disponible."""
    fallback = _obtener_valores_fallback()
    return pd.DataFrame({
        "ds": fechas,
        "precipitacion_total_serv": [fallback["precipitacion"]] * len(fechas),
        "viento_medio_serv": [fallback["viento"]] * len(fechas),
    })


def _mensaje_fallback():
    """Construye el mensaje informativo del fallback con los valores actuales."""
    fallback = _obtener_valores_fallback()
    return (
        "No se pudo conectar con la API meteorológica. La predicción "
        "se ha generado con valores medios de fallback "
        f"(precipitación {fallback['precipitacion']} mm/día, "
        f"viento {fallback['viento']} m/s) y puede perder fiabilidad."
    )


def _mensaje_estacional():
    """Construye el mensaje informativo del modo estacional."""
    fallback = _obtener_valores_fallback()
    return (
        f"El periodo solicitado se sitúa más allá de los {DIAS_FORECAST} "
        f"días que cubre la previsión meteorológica de Open-Meteo. La "
        f"predicción utiliza valores medios estacionales "
        f"(precipitación {fallback['precipitacion']} mm/día, "
        f"viento {fallback['viento']} m/s)."
    )


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
    limite_forecast = hoy + timedelta(days=DIAS_FORECAST)
    fechas = pd.date_range(start=fecha_inicio, end=fecha_fin, freq="D")

    # Caso 1: el periodo entero está en el pasado
    if fecha_fin < hoy:
        try:
            datos = _llamar_api_historica(fecha_inicio, fecha_fin)
            df = _construir_dataframe(datos, fechas)
            mensaje = (
                "Datos meteorológicos reales obtenidos de Open-Meteo "
                "para el periodo solicitado."
            )
            return df, "historico", mensaje
        except Exception:
            df = _construir_dataframe_fallback(fechas)
            return df, "fallback", _mensaje_fallback()

    # Caso 2: el periodo entero está dentro de la ventana de forecast
    if fecha_inicio >= hoy and fecha_fin <= limite_forecast:
        try:
            datos = _llamar_api_forecast(fecha_inicio, fecha_fin)
            df = _construir_dataframe(datos, fechas)
            mensaje = (
                "Previsión meteorológica obtenida de Open-Meteo "
                "para el periodo solicitado."
            )
            return df, "forecast", mensaje
        except Exception:
            df = _construir_dataframe_fallback(fechas)
            return df, "fallback", _mensaje_fallback()

    # Caso 3: el periodo está más allá del horizonte de forecast
    df = _construir_dataframe_fallback(fechas)
    return df, "estacional", _mensaje_estacional()