"""
Página de Administrador.

Muestra información sobre los modelos entrenados y las métricas
de evaluación comparativa frente al modelo de referencia.

"""

from datetime import date

import pandas as pd
import streamlit as st

from utils.config import cargar_configuracion
from utils.metricas import (
    INICIO_ENTRENAMIENTO,
    FIN_ENTRENAMIENTO,
)


# Encabezado 
st.title("Administrador")
st.markdown(
    "Vista técnica del sistema con información sobre los modelos "
    "entrenados y sus métricas de evaluación."
)

# Información del modelo
st.header("Modelos entrenados")

col_corto, col_medio = st.columns(2)

with col_corto.container(border=True):
    st.markdown("##### Modelo de corto plazo")
    st.markdown(
        f"""
        - **Algoritmo:** Prophet (Meta)
        - **Horizonte:** 14 días
        - **Regresores externos:** temperatura media del día, humedad media del día, viento medio en la ventana de servicio
        - **Estacionalidades:** semanal, anual
        - **Festivos:** habilitados (calendario nacional/regional) + festivos sociales (San Valentín, Mother's Day, Christmas Eve, New Year's Eve)
        """
    )

with col_medio.container(border=True):
    st.markdown("##### Modelo de medio plazo")
    st.markdown(
        f"""
        - **Algoritmo:** Prophet (Meta)
        - **Horizonte:** 30 días
        - **Regresores externos:** ninguno
        - **Estacionalidades:** semanal, anual
        - **Festivos:** habilitados (calendario nacional/regional) + festivos sociales (San Valentín, Mother's Day, Christmas Eve, New Year's Eve
        """
    )

st.subheader("Periodo de entrenamiento")
st.markdown(
    f"Los modelos se han entrenado con datos reales de pedidos "
    f"registrados entre el "
    f"**{INICIO_ENTRENAMIENTO.strftime('%d/%m/%Y')}** y el "
    f"**{FIN_ENTRENAMIENTO.strftime('%d/%m/%Y')}**."
)

st.subheader("Modelo de referencia")
st.markdown(
    "Para validar el rendimiento del modelo principal se ha "
    "implementado un modelo de referencia basado en SARIMA "
    "(*Seasonal ARIMA*), un enfoque estadístico clásico muy "
    "utilizado en predicción de series temporales. La comparativa "
    "permite medir la aportación de las variables contextuales "
    "externas que utiliza Prophet frente al modelo clásico."
)

st.divider()

# Métricas comparativas (Tabla 11 del TFG)-
st.header("Métricas de evaluación comparativa")
st.markdown(
    "Comparación de las métricas de error entre el modelo principal "
    "(Prophet) y el modelo de referencia (SARIMA), evaluadas mediante "
    "validación cruzada sobre el conjunto de prueba."
)

# Datos de la tabla 11 leídos del fichero de configuración
config = cargar_configuracion()

m_pc = config["metricas"]["prophet_corto"]
m_sc = config["metricas"]["sarima_corto"]
m_pm = config["metricas"]["prophet_medio"]
m_sm = config["metricas"]["sarima_medio"]

df_metricas = pd.DataFrame({
    "Modelo": ["Prophet", "SARIMA", "Prophet", "SARIMA"],
    "Horizonte": [
        f"{m_pc['horizonte_dias']} días",
        f"{m_sc['horizonte_dias']} días",
        f"{m_pm['horizonte_dias']} días",
        f"{m_sm['horizonte_dias']} días",
    ],
    "MAE": [m_pc["mae"], m_sc["mae"], m_pm["mae"], m_sm["mae"]],
    "RMSE": [m_pc["rmse"], m_sc["rmse"], m_pm["rmse"], m_sm["rmse"]],
    "MAPE (%)": [
        m_pc.get("mape"),
        m_sc.get("mape"),
        m_pm.get("mape"),
        m_sm.get("mape"),
    ],
})

st.dataframe(
    df_metricas,
    width="stretch",
    hide_index=True,
    column_config={
        "MAE": st.column_config.NumberColumn(format="%.2f"),
        "RMSE": st.column_config.NumberColumn(format="%.2f"),
        "MAPE (%)": st.column_config.NumberColumn(format="%.2f"),
    },
)

st.caption(
    "MAE: Error absoluto medio · RMSE: Raíz del error cuadrático "
    "medio · MAPE: Error porcentual absoluto medio. "
    "El valor MAPE de SARIMA a 30 días se ha omitido por la "
    "presencia de valores próximos a cero en la serie real, que "
    "generan distorsiones porcentuales no representativas."
)

st.subheader("Lectura de los resultados")
st.markdown(
    "El modelo Prophet supera al modelo de referencia SARIMA en "
    "todas las métricas evaluadas y en ambos horizontes. La mejora "
    "es especialmente significativa en el MAPE a 14 días, donde "
    "Prophet reduce el error porcentual a menos de la mitad. En este "
    "caso se observa que las variables contextuales contribuyen a mejorar "
    "el rendimiento de Prophet en este conjunto de datos."
)

# Visualizaciones comparativas.
st.divider()

st.header("Visualización comparativa")
st.markdown(
    "A continuación se muestran las predicciones de Prophet y SARIMA "
    "sobre el último fold de la validación cruzada, en los dos "
    "escenarios operativos del sistema. Las gráficas permiten "
    "apreciar visualmente el comportamiento de ambos modelos frente "
    "a la demanda real."
)

st.subheader("Escenario de corto plazo (14 días)")
st.markdown(
    "Para Prophet se utiliza el modelo de corto plazo, que incluye "
    "festivos y los regresores meteorológicos seleccionados "
    "(precipitación y viento en ventana de servicio). Para SARIMA "
    "se utiliza el modelo seleccionado por *auto_arima*, sin "
    "regresores externos."
)
st.image(
    "panel/assets/figura_comparativa_corto_plazo.png",
    width="stretch",
)

st.subheader("Escenario de medio plazo (30 días)")
st.markdown(
    "Para Prophet se utiliza el modelo de medio plazo, que incluye "
    "festivos pero prescinde de los regresores meteorológicos, dado "
    "que las previsiones del clima no son fiables más allá de 14 "
    "días. La degradación del modelo SARIMA es notablemente más "
    "acusada en este horizonte."
)
st.image(
    "panel/assets/figura_comparativa_medio_plazo.png",
    width="stretch",
)