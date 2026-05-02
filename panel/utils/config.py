"""
Carga centralizada de la configuración del panel.

Lee el fichero config.toml ubicado en la raíz del panel y expone
los valores como un diccionario. La carga se realiza una sola vez
por sesión gracias al cacheado de Streamlit.

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
def cargar_configuracion() -> dict:
    """
    Carga la configuración del panel desde el fichero TOML.

    Returns:
        Diccionario con la configuración estructurada en secciones.
    """
    with open(RUTA_CONFIG, "rb") as f:
        config = tomllib.load(f)

    # Conversión de las fechas de cadena ISO a objetos date para
    # uso directo en el resto del código.
    config["modelo"]["inicio_entrenamiento"] = date.fromisoformat(
        config["modelo"]["inicio_entrenamiento"]
    )
    config["modelo"]["fin_entrenamiento"] = date.fromisoformat(
        config["modelo"]["fin_entrenamiento"]
    )

    return config