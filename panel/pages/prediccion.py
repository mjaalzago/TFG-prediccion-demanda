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
import holidays

from utils.clima import obtener_clima
from utils.modelos import seleccionar_modelo
from utils.datos import cargar_datos_historicos
from utils.fiabilidad import (
    calcular_nivel_fiabilidad,
    mae_segun_horizonte,
)



# Encabezado de la página
st.title("Predicción de demanda")

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

        # Carga de datos reales para superponer en el gráfico cuando la
        # ventana de consulta solapa con el periodo de entrenamiento.
        df_historico = cargar_datos_historicos()
        fecha_fin = fecha_inicio + timedelta(days=horizonte - 1)
        df_real_overlap = df_historico[
            (df_historico["fecha"].dt.date >= fecha_inicio) &
            (df_historico["fecha"].dt.date <= fecha_fin)
        ].copy()

        # Festivos del Reino Unido (Inglaterra) en la ventana consultada.
        # Se utiliza la misma fuente que el modelo Prophet usa internamente
        # para los efectos de festivos.
        festivos_uk = holidays.UnitedKingdom(
            subdiv="ENG",
            years=range(fecha_inicio.year, fecha_fin.year + 1),
        )
        festivos_periodo = [
            (f, festivos_uk[f]) for f in festivos_uk
            if fecha_inicio <= f <= fecha_fin
        ]

    # Solo se muestran arriba las alertas reales (fecha muy alejada del
    # entrenamiento o fallback en la API de clima). El resto de información
    # de la consulta se agrupa al final en la caja "Detalles de la consulta".
    fecha_fin_entrenamiento = date(2019, 8, 3)
    dias_desde_entrenamiento = (fecha_inicio - fecha_fin_entrenamiento).days

    if dias_desde_entrenamiento > 30:
        st.warning(
            f"La predicción se ha solicitado para una fecha que dista "
            f"{dias_desde_entrenamiento} días del final del periodo de "
            f"entrenamiento del modelo (03/08/2019). Las predicciones para "
            f"fechas muy alejadas del entrenamiento pueden perder fiabilidad."
        )

    if mensaje_clima is not None and fuente_clima == "fallback":
        st.warning(mensaje_clima)

    # Construcción del gráfico interactivo de líneas con Plotly
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

    # Línea de pedidos reales (solo si hay solape con el histórico)
    if len(df_real_overlap) > 0:
        fig.add_trace(
            go.Scatter(
                x=df_real_overlap["fecha"],
                y=df_real_overlap["n_pedidos"],
                mode="lines",
                line=dict(color="#1f3a5f", width=1.5),
                opacity=0.6,
                name="Pedidos reales",
                hovertemplate=(
                    "<b>%{x|%d/%m/%Y}</b><br>"
                    "Pedidos reales: %{y:.0f}<extra></extra>"
                ),
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

    # ============================================================
    # Visualización: layout adaptativo según el horizonte
    # Para 14 días: dos columnas (gráfico izquierda + calendario derecha)
    # Para 30 días: vertical (gráfico arriba, calendario debajo)
    # ============================================================

    st.markdown(f"#### Predicción diaria - Horizonte de {horizonte} días")

    if horizonte == 14:
        col_grafico, col_calendario = st.columns(2)
        contenedor_grafico = col_grafico
        contenedor_calendario = col_calendario
    else:
        contenedor_grafico = st.container()
        contenedor_calendario = st.container()

    with contenedor_grafico:
        st.plotly_chart(fig, width="stretch", key="grafico_lineas")

    with contenedor_calendario:

        # Construcción del DataFrame con la información del calendario
        df_cal = pd.DataFrame({
            "fecha": prediccion["ds"],
            "pedidos": prediccion["yhat"].round().astype(int),
        })
        df_cal["dia_semana"] = df_cal["fecha"].dt.dayofweek
        df_cal["anio_iso"] = df_cal["fecha"].dt.isocalendar().year
        df_cal["semana"] = df_cal["fecha"].dt.isocalendar().week
        df_cal["dia_mes"] = df_cal["fecha"].dt.day
        df_cal["mes_anio"] = df_cal["fecha"].dt.strftime("%B %Y")

        # Reorganización para el heatmap: filas = semanas, columnas = días.
        # Ordenamos por (año ISO, semana) para evitar problemas en consultas
        # que cruzan el cambio de año (ej: semana 52/2018 antes que 1/2019).
        semanas_unicas = (
            df_cal[["anio_iso", "semana"]]
            .drop_duplicates()
            .sort_values(["anio_iso", "semana"])
            .apply(tuple, axis=1)
            .tolist()
        )
        dias_orden = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

        # Matriz de pedidos (semanas × días)
        matriz_pedidos = []
        matriz_etiquetas = []
        matriz_textos = []

        for anio, semana in semanas_unicas:
            fila_pedidos = []
            fila_etiquetas = []
            fila_textos = []
            for dia in range(7):
                registro = df_cal[
                    (df_cal["anio_iso"] == anio) &
                    (df_cal["semana"] == semana) &
                    (df_cal["dia_semana"] == dia)
                ]
                if len(registro) > 0:
                    fecha_dia = registro["fecha"].iloc[0]
                    pedidos = registro["pedidos"].iloc[0]
                    fila_pedidos.append(pedidos)

                    # Detectar si la fecha es festivo
                    es_festivo = any(fecha_dia.date() == f[0] for f in festivos_periodo)

                    # Etiqueta del tooltip
                    if es_festivo:
                        nombre_fest = next(f[1] for f in festivos_periodo if f[0] == fecha_dia.date())
                        fila_etiquetas.append(
                            f"<b>{fecha_dia.strftime('%d/%m')}</b><br>"
                            f"{pedidos} pedidos<br>"
                            f"<i>{nombre_fest}</i>"
                        )
                    else:
                        fila_etiquetas.append(
                            f"<b>{fecha_dia.strftime('%d/%m')}</b><br>{pedidos} pedidos"
                        )

                    # Texto en la celda: número del día en rojo y negrita si es festivo
                    if es_festivo:
                        fila_textos.append(
                            f"<b><span style='color:#e74c3c'>{fecha_dia.day}</span></b>"
                            f"<br><b>{pedidos}</b>"
                        )
                    else:
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
                y=[f"Semana {s}" for _, s in semanas_unicas],
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

        st.plotly_chart(fig_cal, width="stretch", key="calendario_heatmap")

        if festivos_periodo:
            st.caption(
                "Los días con el número en rojo en el calendario "
                "corresponden a festivos."
            )

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

    # Cálculo del día con más pedidos y su fecha
    idx_max = prediccion["yhat"].idxmax()
    fecha_pico = prediccion.loc[idx_max, "ds"]
    valor_pico = prediccion.loc[idx_max, "yhat"]

    DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves",
                   "viernes", "sábado", "domingo"]
    MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
             "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
    fecha_formateada = (
        f"{DIAS_SEMANA[fecha_pico.weekday()]} "
        f"{fecha_pico.day} de {MESES[fecha_pico.month - 1]}"
    )

    with col_m3:
        st.metric(
            label="Día con más pedidos",
            value=f"{valor_pico:.0f}",
        )
        st.caption(fecha_formateada.capitalize())

    # ---------------------------------------------------------------
    # Tarjeta compacta de fiabilidad
    # ---------------------------------------------------------------

    info = calcular_nivel_fiabilidad(fecha_inicio)
    mae = mae_segun_horizonte(horizonte)

    if info["nivel"] == "alta":
        texto_margen = f"Margen ±{mae:.1f} pedidos/día"
    elif info["nivel"] == "media":
        texto_margen = f"Margen ±{mae:.1f} pedidos/día (mínimo)"
    else:
        texto_margen = "Margen no estimable con fiabilidad"

    st.markdown(
        f"""
        <div style='display:flex; align-items:center; gap:1rem;
                    padding:0.75rem 1rem; background:{info['color']}15;
                    border-left:4px solid {info['color']};
                    border-radius:6px; margin: 0.5rem 0;'>
            <span style='font-size:1.2rem; color:{info['color']};'>●</span>
            <div style='flex:1;'>
                <strong style='color:{info['color']};'>{info['titulo']}</strong>
                <span style='color:#555;'> · {texto_margen}</span>
            </div>
            <a href='/fiabilidad' target='_self'
            style='color:#3896b0; text-decoration:none; font-size:0.9rem;'>
                Ver detalle ↗
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------------
    # Caja con los detalles informativos de la consulta
    # ---------------------------------------------------------------

    with st.expander("Detalles de la consulta", expanded=False):

        # Modelo y periodo
        st.markdown(
            f"**Modelo utilizado:** {nombre_modelo}  \n"
            f"**Periodo predicho:** del "
            f"{fecha_inicio.strftime('%d/%m/%Y')} al "
            f"{fechas[-1].strftime('%d/%m/%Y')}"
        )

        # Festivos del periodo (si los hay)
        if festivos_periodo:
            DIAS_SEMANA_CORTO = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
            lineas_festivos = []
            for fecha_fest, nombre_fest in festivos_periodo:
                dia = DIAS_SEMANA_CORTO[fecha_fest.weekday()]
                lineas_festivos.append(
                    f"- **{fecha_fest.strftime('%d/%m/%Y')}** "
                    f"({dia}): {nombre_fest}"
                )
            st.markdown(
                "**Festivos en el periodo:**\n" +
                "\n".join(lineas_festivos)
            )

        # Información sobre el periodo de entrenamiento
        if dias_desde_entrenamiento <= 0:
            st.markdown(
                "**Periodo de entrenamiento:** La fecha consultada se "
                "encuentra dentro del periodo de entrenamiento del modelo "
                "(septiembre 2016 - agosto 2019). La predicción es un "
                "ajuste in-sample, útil para validación visual y "
                "comparación con los datos reales conocidos."
            )

        # Información sobre la fuente de los datos meteorológicos
        if mensaje_clima is not None and fuente_clima != "fallback":
            st.markdown(f"**Datos meteorológicos:** {mensaje_clima}")

    # Guardamos la fecha y horizonte para que la página de Fiabilidad
    # pueda mostrar la información específica de esta consulta
    st.session_state["consulta_fecha"] = fecha_inicio
    st.session_state["consulta_horizonte"] = horizonte