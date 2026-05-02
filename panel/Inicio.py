"""
Panel de predicción de demanda.

Sistema desarrollado en el marco del Trabajo de Fin de Grado
"Sistema de predicción de demanda para restaurantes con reparto a domicilio".

Autora: María José Álvarez González
UNIR - Grado en Ingeniería Informática
"""

import streamlit as st


def inicio():
    """Página de bienvenida del panel."""
    st.title("Panel de predicción de demanda")
    st.markdown("**Restaurantes con reparto a domicilio**")

    st.divider()

    st.markdown(
        """
        ## Bienvenida

        Esta herramienta permite consultar las predicciones de demanda diarias
        para los próximos días, basadas en un modelo entrenado con el histórico
        de pedidos del restaurante y enriquecido con variables contextuales
        como el clima y los festivos del calendario inglés.

        ### Cómo utilizar el panel

        Utilice el menú lateral para navegar entre las distintas secciones:

        - **Predicción de demanda**: consulta las predicciones para los
          próximos días, con el detalle por día de la semana y el intervalo
          de confianza del modelo.

        - **Fiabilidad de las predicciones**: información sobre el grado de
          confianza de las predicciones para apoyar la toma de decisiones.

        - **Panel de administrador**: vista técnica con información sobre los
          modelos entrenados y métricas de evaluación comparativa.
        """
    )

    st.divider()

    # Información del proyecto al pie
    col_proyecto, col_autora = st.columns(2)
    with col_proyecto:
        st.markdown(
            "**Trabajo de Fin de Grado**  \n"
            "Universidad Internacional de La Rioja (UNIR)  \n"
            "Grado en Ingeniería Informática"
        )
    with col_autora:
        st.markdown(
            "**Autora:** María José Álvarez González  \n"
            "**Curso:** 2025/2026"
        )


# Configuración de la página
st.set_page_config(
    page_title="Panel de predicción de demanda",
    page_icon=":material/insights:",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Definición de las páginas con iconos Material
paginas = [
    st.Page(
        inicio,
        title="Inicio",
        icon=":material/home:",
        default=True,
    ),
    st.Page(
        "pages/prediccion.py",
        title="Predicción de demanda",
        icon=":material/insights:",
    ),
    st.Page(
        "pages/fiabilidad.py",
        title="Fiabilidad de las predicciones",
        icon=":material/verified:",
    ),
    st.Page(
        "pages/administrador.py",
        title="Panel de administrador",
        icon=":material/settings:",
    ),
]

# Navegación principal
pg = st.navigation(paginas)

# Ejecutar la página seleccionada
pg.run()