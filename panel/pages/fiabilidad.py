"""
Página de Fiabilidad del panel.
Muestra al usuario cuándo una predicción es más o menos recomendable
"""

import streamlit as st
from datetime import date

from utils.metricas import (
    INICIO_ENTRENAMIENTO,
    FIN_ENTRENAMIENTO,
    MAE_CORTO,
    MAE_MEDIO,
    UMBRAL_VERDE,
    UMBRAL_AMBAR,
    calcular_nivel_fiabilidad,
    mae_segun_horizonte,
)

# Renderizado de la página
st.title("Fiabilidad de las predicciones")
st.markdown(
    "Información sobre el grado de confianza de las predicciones que "
    "ofrece el panel."
)

# Bloque general.
st.header("¿Cómo medimos la fiabilidad?")
st.markdown(
    "El sistema se ha entrenado con datos reales de pedidos entre "
    f"el **{INICIO_ENTRENAMIENTO.strftime('%d/%m/%Y')}** y el "
    f"**{FIN_ENTRENAMIENTO.strftime('%d/%m/%Y')}**. Su precisión se "
    "ha evaluado comparando las predicciones del sistema con la "
    "demanda real registrada en los datos reservados para evaluación."
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


# Si hay fecha en session_state
st.header("Fiabilidad de tu consulta")

# Recuperación del contexto de la consulta.
# Prioridad: session_state (navegación por sidebar) > query params (enlace
# directo desde la tarjeta de Predicción).
fecha_consulta = st.session_state.get("consulta_fecha")
horizonte = st.session_state.get("consulta_horizonte")

if fecha_consulta is None:
    fecha_param = st.query_params.get("fecha")
    horizonte_param = st.query_params.get("horizonte")
    if fecha_param and horizonte_param:
        try:
            fecha_consulta = date.fromisoformat(fecha_param)
            horizonte = int(horizonte_param)
        except (ValueError, TypeError):
            # Si los parámetros son inválidos, los ignoramos.
            fecha_consulta = None
            horizonte = None

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
            "fecha. El sistema solo dispone de una estimación de error "
            "basada en su periodo de entrenamiento."
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