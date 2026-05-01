"""
Página de consulta de predicciones de demanda.

Permite seleccionar una fecha de inicio y un horizonte de predicción
desde el panel lateral y muestra la predicción correspondiente con el
intervalo de confianza al 95% en la zona principal.
"""

from datetime import date, timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from utils.clima import obtener_clima
from utils.modelos import seleccionar_modelo

# Encabezado de la página
st.title("Predicción de demanda")
#st.markdown(
#    "Consulta las predicciones de demanda para los próximos días con su "
#    "intervalo de confianza al 95%."
#)

#st.markdown("---")


# Configuración de la consulta en el sidebar
with st.sidebar:
    st.markdown("### Configuración de la consulta")

    fecha_inicio = st.date_input(
        "Fecha de inicio",
        value=date(2019, 6, 1),
        min_value=date(2016, 9, 1),
        max_value=date(2030, 12, 31),
        format="DD/MM/YYYY",
        help="Primer día del periodo a predecir.",
    )

    horizonte = st.radio(
        "Horizonte de predicción",
        options=[14, 30],
        format_func=lambda x: f"{x} días ({'corto' if x == 14 else 'medio'} plazo)",
        help="Número de días que se quieren predecir desde la fecha de inicio.",
    )

    generar = st.button("Generar predicción", type="primary", width="stretch")

# Si no se ha pulsado el botón aún, mostrar mensaje informativo
if not generar:
    st.info(
        "Configure los parámetros en el panel lateral y pulse **Generar "
        "predicción** para visualizar la demanda prevista."
    )

# Lógica de generación de la predicción
if generar:

    with st.spinner("Generando predicción..."):
        # Selección del modelo según el horizonte
        modelo, nombre_modelo = seleccionar_modelo(horizonte)

        # Construcción del DataFrame de fechas a predecir
        fechas = pd.date_range(
            start=fecha_inicio,
            periods=horizonte,
            freq="D",
        )
        df_futuro = pd.DataFrame({"ds": fechas})

        # Para el modelo de corto plazo, obtenemos los regresores
        # meteorológicos desde la API de Open-Meteo
        if horizonte <= 14:
            df_clima, fuente_clima, mensaje_clima = obtener_clima(
                fecha_inicio,
                fecha_inicio + timedelta(days=horizonte - 1),
            )
            df_futuro["precipitacion_total_serv"] = df_clima["precipitacion_total_serv"].values
            df_futuro["viento_medio_serv"] = df_clima["viento_medio_serv"].values
        else:
            fuente_clima = None
            mensaje_clima = None

        # Generación de la predicción
        prediccion = modelo.predict(df_futuro)

    # Aviso si la fecha está fuera del horizonte recomendado
    fecha_fin_entrenamiento = date(2019, 8, 3)
    dias_desde_entrenamiento = (fecha_inicio - fecha_fin_entrenamiento).days

    if dias_desde_entrenamiento > 30:
        st.warning(
            f"La predicción se ha solicitado para una fecha que dista "
            f"{dias_desde_entrenamiento} días del final del periodo de "
            f"entrenamiento del modelo (03/08/2019). Las predicciones para "
            f"fechas muy alejadas del entrenamiento pueden perder fiabilidad. "
            f"Los escenarios operativos validados son de 14 días (corto plazo) "
            f"y 30 días (medio plazo) desde el final del entrenamiento."
        )
    
    # Aviso si la fecha está dentro del periodo de entrenamiento
    if dias_desde_entrenamiento <= 0:
        st.info(
            "La fecha solicitada se encuentra dentro del periodo de "
            "entrenamiento del modelo (septiembre 2016 - agosto 2019). "
            "La predicción mostrada es un ajuste in-sample del modelo, útil "
            "para validación visual y comparación con los datos reales conocidos."
        )

    # Información sobre la fuente de los datos meteorológicos
    if mensaje_clima is not None:
        if fuente_clima == "fallback":
            st.warning(mensaje_clima)
        elif fuente_clima == "estacional":
            st.info(mensaje_clima)
        else:  # 'historico' o 'forecast'
            st.caption(f"ℹ️ {mensaje_clima}")

    # Construcción del gráfico interactivo con Plotly
    fig = go.Figure()

    # Banda del intervalo de confianza
    fig.add_trace(
        go.Scatter(
            x=prediccion["ds"],
            y=prediccion["yhat_upper"],
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=prediccion["ds"],
            y=prediccion["yhat_lower"],
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(0, 151, 178, 0.2)",
            name="Intervalo de confianza 95%",
            hoverinfo="skip",
        )
    )

    # Línea de la predicción central
    fig.add_trace(
        go.Scatter(
            x=prediccion["ds"],
            y=prediccion["yhat"],
            mode="lines+markers",
            line=dict(color="#0097b2", width=2),
            marker=dict(size=6),
            name="Predicción",
            hovertemplate=(
                "<b>%{x|%d/%m/%Y}</b><br>"
                "Pedidos previstos: %{y:.0f}<extra></extra>"
            ),
        )
    )

    # Configuración visual del gráfico
    fig.update_layout(
        title=f"Predicción de pedidos diarios - Horizonte de {horizonte} días",
        xaxis_title="Fecha",
        yaxis_title="Pedidos previstos",
        hovermode="x unified",
        template="plotly_white",
        height=450,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
        ),
    )

    st.plotly_chart(fig, width="stretch", key="calendario_heatmap")

    # ============================================================
    # Calendario heatmap de la predicción
    # ============================================================
    st.subheader("Vista de calendario")

    # Construcción del DataFrame con la información del calendario
    df_cal = pd.DataFrame({
        "fecha": prediccion["ds"],
        "pedidos": prediccion["yhat"].round().astype(int),
    })
    df_cal["dia_semana"] = df_cal["fecha"].dt.dayofweek  # Lunes=0, Domingo=6
    df_cal["semana"] = df_cal["fecha"].dt.isocalendar().week
    df_cal["dia_mes"] = df_cal["fecha"].dt.day
    df_cal["mes_anio"] = df_cal["fecha"].dt.strftime("%B %Y")

    # Reorganización para el heatmap: filas = semanas, columnas = días
    semanas_unicas = sorted(df_cal["semana"].unique())
    dias_orden = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

    # Matriz de pedidos (semanas × días)
    matriz_pedidos = []
    matriz_etiquetas = []
    matriz_textos = []

    for semana in semanas_unicas:
        fila_pedidos = []
        fila_etiquetas = []
        fila_textos = []
        for dia in range(7):
            registro = df_cal[(df_cal["semana"] == semana) & (df_cal["dia_semana"] == dia)]
            if len(registro) > 0:
                fecha_dia = registro["fecha"].iloc[0]
                pedidos = registro["pedidos"].iloc[0]
                fila_pedidos.append(pedidos)
                fila_etiquetas.append(
                    f"<b>{fecha_dia.strftime('%d/%m')}</b><br>{pedidos} pedidos"
                )
                fila_textos.append(f"{fecha_dia.day}<br><b>{pedidos}</b>")
            else:
                fila_pedidos.append(None)
                fila_etiquetas.append("")
                fila_textos.append("")
        matriz_pedidos.append(fila_pedidos)
        matriz_etiquetas.append(fila_etiquetas)
        matriz_textos.append(fila_textos)

    # Construcción del heatmap con Plotly
    fig_cal = go.Figure(
        data=go.Heatmap(
            z=matriz_pedidos,
            x=dias_orden,
            y=[f"Semana {s}" for s in semanas_unicas],
            text=matriz_textos,
            texttemplate="%{text}",
            textfont={"size": 13, "color": "#1f3a5f"},
            customdata=matriz_etiquetas,
            hovertemplate="%{customdata}<extra></extra>",
            colorscale=[
                [0.0, "#e6f4f7"],
                [0.5, "#7fc5d4"],
                [1.0, "#0097b2"],
            ],
            colorbar=dict(
                title=dict(
                    text="Pedidos",
                    side="right",
                ),
            ),
            xgap=3,
            ygap=3,
        )
    )

    fig_cal.update_layout(
        height=max(180, len(semanas_unicas) * 70),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(side="top", tickfont=dict(size=12)),
        yaxis=dict(tickfont=dict(size=11), autorange="reversed"),
        plot_bgcolor="white",
    )

    st.plotly_chart(fig_cal, width="stretch", key="grafico_lineas")

    # ============================================================
    # Métricas resumidas
    # ============================================================
    st.subheader("Resumen de la predicción")

    col_m1, col_m2, col_m3 = st.columns(3)

    with col_m1:
        st.metric(
            label="Total pedidos previstos",
            value=f"{prediccion['yhat'].sum():.0f}",
        )

    with col_m2:
        st.metric(
            label="Media diaria",
            value=f"{prediccion['yhat'].mean():.1f}",
        )

    with col_m3:
        st.metric(
            label="Día con más pedidos",
            value=f"{prediccion['yhat'].max():.0f}",
            help=f"El día {prediccion.loc[prediccion['yhat'].idxmax(), 'ds'].strftime('%d/%m/%Y')}",
        )

        # Resultado: información del modelo utilizado
    st.success(
        f"Predicción generada con el modelo de **{nombre_modelo}** "
        f"para el periodo del {fecha_inicio.strftime('%d/%m/%Y')} al "
        f"{fechas[-1].strftime('%d/%m/%Y')}."
    )