"""
Carga de datos históricos para el panel.
"""

from pathlib import Path

import pandas as pd
import streamlit as st


# Ruta al dataset relativa al fichero, robusta independientemente
# del directorio desde el que se lance Streamlit.
RUTA_DATOS = Path(__file__).parent.parent.parent / "data" / "processed"


@st.cache_data
def cargar_datos_historicos() -> pd.DataFrame:
    """
    Carga el dataset histórico enriquecido de pedidos reales con sus
    variables contextuales (clima, festivos). El resultado se cachea
    en memoria para evitar lecturas repetidas durante la sesión.

    Devuelve un DataFrame con columnas 'fecha' (datetime) y 'n_pedidos'
    (entero), entre otras.
    """
    fichero = RUTA_DATOS / "dataset_enriquecido.csv"
    df = pd.read_csv(fichero, parse_dates=["fecha"])
    return df