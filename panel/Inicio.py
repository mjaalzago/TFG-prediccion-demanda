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

    st.markdown("---")

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

        - **Fiabilidad del modelo**: información sobre el rendimiento
          histórico del modelo y comparativa con un modelo de referencia.
        """
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
        title="Fiabilidad del modelo",
        icon=":material/verified:",
    ),
]

# Navegación principal
pg = st.navigation(paginas)

# Pie informativo en sidebar
st.sidebar.markdown("---")
st.sidebar.caption(
    "Trabajo de Fin de Grado · UNIR\n\n"
    "Grado en Ingeniería Informática"
)

# Ejecutar la página seleccionada
pg.run()