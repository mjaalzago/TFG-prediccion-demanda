"""
Página de Fiabilidad del panel.
Vista orientada al gestor: explica de forma no técnica el grado
de confianza de las predicciones que ofrece el sistema.
"""

from datetime import date
import streamlit as st

from utils.fiabilidad import (
    INICIO_ENTRENAMIENTO,
    FIN_ENTRENAMIENTO,
    MAE_CORTO,
    MAE_MEDIO,
    UMBRAL_VERDE,
    UMBRAL_AMBAR,
    calcular_nivel_fiabilidad,
    mae_segun_horizonte,
)


# ---------------------------------------------------------------
# Parámetros de la página (centralizados para fácil ajuste)
# ---------------------------------------------------------------

# Fin del periodo de entrenamiento del modelo
FIN_ENTRENAMIENTO = date(2019, 8, 3)
INICIO_ENTRENAMIENTO = date(2016, 9, 1)

# Margen de error medio del sistema (de la tabla 11 del TFG)
MAE_CORTO = 6.54   # 14 días
MAE_MEDIO = 7.25   # 30 días

# Umbrales del semáforo en días desde el fin del entrenamiento
# Pendiente de decidir definitivamente. Cambiar aquí cuando se acuerde.
UMBRAL_VERDE = 30    # hasta 30 días del fin: fiabilidad alta
UMBRAL_AMBAR = 180   # entre 30 y 180 días: fiabilidad media
                     # más de 180: fiabilidad baja


# ---------------------------------------------------------------
# Lógica del semáforo
# ---------------------------------------------------------------

def calcular_nivel_fiabilidad(fecha_consulta: date) -> dict:
    """
    Devuelve el nivel de fiabilidad para una fecha de consulta.
    """
    if INICIO_ENTRENAMIENTO <= fecha_consulta <= FIN_ENTRENAMIENTO:
        dias_desde_fin = 0
        dentro_periodo = True
    else:
        dias_desde_fin = (fecha_consulta - FIN_ENTRENAMIENTO).days
        dentro_periodo = False

    if dentro_periodo or dias_desde_fin <= UMBRAL_VERDE:
        return {
            "nivel": "alta",
            "color": "#2ecc71",
            "icono": ":material/check_circle:",
            "titulo": "Fiabilidad alta",
            "dias_desde_fin": dias_desde_fin,
            "dentro_periodo": dentro_periodo,
        }
    elif dias_desde_fin <= UMBRAL_AMBAR:
        return {
            "nivel": "media",
            "color": "#f39c12",
            "icono": ":material/warning:",
            "titulo": "Fiabilidad media",
            "dias_desde_fin": dias_desde_fin,
            "dentro_periodo": False,
        }
    else:
        return {
            "nivel": "baja",
            "color": "#e74c3c",
            "icono": ":material/error:",
            "titulo": "Fiabilidad baja",
            "dias_desde_fin": dias_desde_fin,
            "dentro_periodo": False,
        }


# ---------------------------------------------------------------
# Renderizado de la página
# ---------------------------------------------------------------

st.title("Fiabilidad de las predicciones")
st.markdown(
    "Información sobre el grado de confianza de las predicciones que "
    "ofrece el panel."
)

# ===============================================================
# BLOQUE GENERAL (siempre visible)
# ===============================================================

st.header("¿Cómo medimos la fiabilidad?")
st.markdown(
    "El sistema se ha entrenado con datos reales de pedidos entre "
    f"el **{INICIO_ENTRENAMIENTO.strftime('%d/%m/%Y')}** y el "
    f"**{FIN_ENTRENAMIENTO.strftime('%d/%m/%Y')}**. Su precisión se "
    "ha evaluado comparando las predicciones del sistema con la "
    "demanda real registrada en ese mismo periodo."
)

st.subheader("Margen de error medio del sistema")

col_corto, col_medio = st.columns(2)
with col_corto:
    st.metric(
        label="Predicciones a 14 días",
        value=f"±{MAE_CORTO:.1f} pedidos/día",
    )
    st.caption(
        "Diferencia media esperada entre la predicción del sistema "
        "y la demanda real."
    )
with col_medio:
    st.metric(
        label="Predicciones a 30 días",
        value=f"±{MAE_MEDIO:.1f} pedidos/día",
    )
    st.caption(
        "Las predicciones a más largo plazo acumulan más "
        "incertidumbre."
    )

st.subheader("Cuándo confiar más y cuándo confiar menos")

col_v, col_a, col_r = st.columns(3)
with col_v.container(border=True):
    st.markdown("##### :material/check_circle: Fiabilidad alta")
    st.markdown(
        "Predicciones para fechas dentro del periodo histórico "
        f"o hasta {UMBRAL_VERDE} días posteriores al fin del "
        "entrenamiento."
    )
with col_a.container(border=True):
    st.markdown("##### :material/warning: Fiabilidad media")
    st.markdown(
        f"Predicciones entre {UMBRAL_VERDE} y {UMBRAL_AMBAR} "
        "días desde el fin del entrenamiento. Los patrones del "
        "modelo siguen siendo razonables, pero se recomienda "
        "contrastar con datos recientes."
    )
with col_r.container(border=True):
    st.markdown("##### :material/error: Fiabilidad baja")
    st.markdown(
        f"Predicciones a más de {UMBRAL_AMBAR} días desde el fin "
        "del entrenamiento. Se recomienda reentrenar el modelo "
        "con datos actualizados antes de tomar decisiones."
    )

st.divider()

# ===============================================================
# BLOQUE ESPECÍFICO (solo si hay fecha en session_state)
# ===============================================================

st.header("Fiabilidad de tu consulta")

fecha_consulta = st.session_state.get("consulta_fecha")
horizonte = st.session_state.get("consulta_horizonte")

if fecha_consulta is None:
    st.info(
        ":material/info: Selecciona una fecha en la página de "
        "**Predicción de demanda** para ver la fiabilidad "
        "específica de tu consulta."
    )
else:
    info = calcular_nivel_fiabilidad(fecha_consulta)
    mae_consulta = mae_segun_horizonte(horizonte)

    # Semáforo
    st.markdown(
        f"<div style='display:flex; align-items:center; gap:1rem; "
        f"padding:1.5rem; background:{info['color']}15; "
        f"border-left:6px solid {info['color']}; border-radius:6px;'>"
        f"<span style='font-size:2.5rem; color:{info['color']};'>"
        f"●</span>"
        f"<div><h3 style='margin:0; color:{info['color']};'>"
        f"{info['titulo']}</h3></div></div>",
        unsafe_allow_html=True,
    )

    st.markdown("")  # espacio

    # Frase contextual
    if info["dentro_periodo"]:
        contexto = (
            f"Estás consultando una predicción para el "
            f"**{fecha_consulta.strftime('%d/%m/%Y')}**, fecha "
            "que se encuentra dentro del periodo de "
            "entrenamiento del modelo."
        )
    else:
        contexto = (
            f"Estás consultando una predicción para el "
            f"**{fecha_consulta.strftime('%d/%m/%Y')}**, "
            f"a {info['dias_desde_fin']} días del fin del periodo "
            "de entrenamiento del modelo."
        )
    st.markdown(contexto)

    # Margen de error específico (depende del nivel de fiabilidad)
    if info["nivel"] == "alta":
        st.metric(
            label=f"Margen de error esperado para {horizonte} días",
            value=f"±{mae_consulta:.1f} pedidos/día",
        )
    elif info["nivel"] == "media":
        st.metric(
            label=f"Margen de error esperado para {horizonte} días",
            value=f"±{mae_consulta:.1f} pedidos/día (mínimo)",
        )
        st.caption(
            "Este margen corresponde a la precisión medida durante "
            "el entrenamiento. Para fechas alejadas del periodo "
            "histórico el error real puede ser mayor."
        )
    else:  # baja
        st.markdown("**Margen de error esperado**")
        st.markdown(
            "No es posible estimarlo con fiabilidad para esta "
            "fecha. El sistema solo puede garantizar la precisión "
            "medida en su periodo de entrenamiento."
        )

    # Recomendación según nivel
    if info["nivel"] == "alta":
        st.success(
            ":material/lightbulb: La predicción es fiable para "
            "tomar decisiones operativas como compras o "
            "planificación de turnos."
        )
    elif info["nivel"] == "media":
        st.warning(
            ":material/lightbulb: Conviene contrastar la "
            "predicción con tu experiencia reciente antes de "
            "tomar decisiones importantes."
        )
    else:
        st.error(
            ":material/lightbulb: Esta fecha está muy lejos del "
            "periodo de entrenamiento. Se recomienda actualizar "
            "el modelo con datos recientes antes de usar esta "
            "predicción para decisiones operativas."
        )