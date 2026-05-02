"""
Carga centralizada de la configuración del panel.

Lee el fichero config.toml ubicado en la raíz del panel y expone
los valores como un diccionario. La carga se realiza una sola vez
por sesión gracias al cacheado de Streamlit, y se invalida
automáticamente si el fichero de configuración se modifica.

El uso de un fichero de configuración externo permite adaptar el
panel a un nuevo restaurante o a un reentrenamiento del modelo
sin necesidad de modificar el código.
"""

from datetime import date
from pathlib import Path

import streamlit as st
import tomllib


# Ruta al fichero de configuración relativa al fichero actual.
# Esto permite que la carga funcione independientemente del
# directorio desde el que se lance Streamlit.
RUTA_CONFIG = Path(__file__).parent.parent / "config.toml"


@st.cache_data
def _cargar_configuracion_cacheada(mtime: float) -> dict:
    """
    Carga interna cacheada. La clave de caché incluye el mtime del
    fichero para que se invalide automáticamente al editarlo.
    """
    with open(RUTA_CONFIG, "rb") as f:
        config = tomllib.load(f)

    # Conversión de las fechas de cadena ISO a objetos date.
    config["modelo"]["inicio_entrenamiento"] = date.fromisoformat(
        config["modelo"]["inicio_entrenamiento"]
    )
    config["modelo"]["fin_entrenamiento"] = date.fromisoformat(
        config["modelo"]["fin_entrenamiento"]
    )

    # Si no hay festivos locales configurados, dejamos lista vacía
    # para que el resto del código no necesite hacer comprobaciones.
    if "festivos_locales" not in config:
        config["festivos_locales"] = []

    return config


def cargar_configuracion() -> dict:
    """
    Carga la configuración del panel desde el fichero TOML.

    El resultado se cachea internamente y se invalida automáticamente
    cuando el fichero se modifica.
    """
    return _cargar_configuracion_cacheada(RUTA_CONFIG.stat().st_mtime)