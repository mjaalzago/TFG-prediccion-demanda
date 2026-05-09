"""
Métricas y lógica de fiabilidad del modelo.

Este módulo muestra las métricas de evaluación de los modelos
(MAE, umbrales del semáforo) y la lógica de cálculo del nivel
de fiabilidad de las predicciones según la fecha consultada.

Las constantes y umbrales se leen del fichero config.toml mediante
el módulo utils.config.

Se usa en la página de Predicción (en la tarjeta compacta de
fiabilidad) y en la página de Fiabilidad  
y la página de Administrador (información de modelos).
"""

from datetime import date

from utils.config import cargar_configuracion


# 
# Acceso a la configuración
def _get_config():
    """Devuelve la configuración actual del panel."""
    return cargar_configuracion()


# Estos valores se obtienen dinámicamente desde la configuración, 
# se definen como atributos del módulo para simplificar su uso 
# y desacoplar el resto del sistema de la fuente de datos.
def _inicio_entrenamiento() -> date:
    return _get_config()["modelo"]["inicio_entrenamiento"]


def _fin_entrenamiento() -> date:
    return _get_config()["modelo"]["fin_entrenamiento"]


# Para mantener la compatibilidad con el código existente, 
# estos valores se definen como atributos del módulo,
# permitiendo obtenerlos dinámicamente desde la configuración
def __getattr__(name):
    """
    Permite acceder a INICIO_ENTRENAMIENTO y FIN_ENTRENAMIENTO
    como si fueran constantes del módulo, pero leyéndolas en cada
    acceso desde la configuración.
    """
    config = _get_config()
    if name == "INICIO_ENTRENAMIENTO":
        return config["modelo"]["inicio_entrenamiento"]
    if name == "FIN_ENTRENAMIENTO":
        return config["modelo"]["fin_entrenamiento"]
    if name == "MAE_CORTO":
        return config["metricas"]["prophet_corto"]["mae"]
    if name == "MAE_MEDIO":
        return config["metricas"]["prophet_medio"]["mae"]
    if name == "UMBRAL_VERDE":
        return config["fiabilidad"]["umbral_verde_dias"]
    if name == "UMBRAL_AMBAR":
        return config["fiabilidad"]["umbral_ambar_dias"]
    raise AttributeError(f"module 'utils.metricas' has no attribute {name!r}")


# 
# Lógica del semáforo
def calcular_nivel_fiabilidad(fecha_consulta: date) -> dict:
    """
    Devuelve el nivel de fiabilidad para una fecha de consulta.
    """
    config = _get_config()
    inicio = config["modelo"]["inicio_entrenamiento"]
    fin = config["modelo"]["fin_entrenamiento"]
    umbral_verde = config["fiabilidad"]["umbral_verde_dias"]
    umbral_ambar = config["fiabilidad"]["umbral_ambar_dias"]

    if inicio <= fecha_consulta <= fin:
        dias_desde_fin = 0
        dentro_periodo = True
    else:
        dias_desde_fin = (fecha_consulta - fin).days
        dentro_periodo = False

    if dentro_periodo or dias_desde_fin <= umbral_verde:
        return {
            "nivel": "alta",
            "color": "#2ecc71",
            "titulo": "Fiabilidad alta",
            "dias_desde_fin": dias_desde_fin,
            "dentro_periodo": dentro_periodo,
        }
    elif dias_desde_fin <= umbral_ambar:
        return {
            "nivel": "media",
            "color": "#f39c12",
            "titulo": "Fiabilidad media",
            "dias_desde_fin": dias_desde_fin,
            "dentro_periodo": False,
        }
    else:
        return {
            "nivel": "baja",
            "color": "#e74c3c",
            "titulo": "Fiabilidad baja",
            "dias_desde_fin": dias_desde_fin,
            "dentro_periodo": False,
        }


def mae_segun_horizonte(horizonte: int) -> float:
    """Devuelve el MAE correspondiente al horizonte de predicción."""
    config = _get_config()
    if horizonte == 14:
        return config["metricas"]["prophet_corto"]["mae"]
    return config["metricas"]["prophet_medio"]["mae"]