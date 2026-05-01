"""
Carga de modelos predictivos persistidos.

Los modelos se cargan una sola vez por sesión gracias al sistema de caché
de Streamlit, evitando recargarlos en cada interacción del usuario.
"""

import pickle
from pathlib import Path

import streamlit as st


# Calculamos la ruta de los modelos a partir de la ubicación de este archivo.
# Estructura: panel/utils/modelos.py → ../../data/processed/
RUTA_BASE = Path(__file__).resolve().parent.parent.parent
RUTA_MODELO_CORTO = RUTA_BASE / "data" / "processed" / "modelo_prophet_corto.pkl"
RUTA_MODELO_MEDIO = RUTA_BASE / "data" / "processed" / "modelo_prophet_medio.pkl"


@st.cache_resource
def cargar_modelo_corto():
    """Carga el modelo Prophet de corto plazo (con festivos y clima)."""
    with open(RUTA_MODELO_CORTO, "rb") as f:
        return pickle.load(f)


@st.cache_resource
def cargar_modelo_medio():
    """Carga el modelo Prophet de medio plazo (solo con festivos)."""
    with open(RUTA_MODELO_MEDIO, "rb") as f:
        return pickle.load(f)


def seleccionar_modelo(horizonte_dias):
    """
    Selecciona el modelo apropiado según el horizonte de predicción.

    Para horizontes de hasta 14 días se utiliza el modelo de corto plazo
    (con regresores meteorológicos), y para horizontes superiores se
    utiliza el modelo de medio plazo (solo con festivos).
    """
    if horizonte_dias <= 14:
        return cargar_modelo_corto(), "corto plazo"
    else:
        return cargar_modelo_medio(), "medio plazo"