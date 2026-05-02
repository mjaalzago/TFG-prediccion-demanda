"""
Lógica compartida de cálculo de fiabilidad.
Se usa tanto en la página de Predicción (tarjeta compacta)
como en la página de Fiabilidad (vista completa).
"""

from datetime import date


# Periodo de entrenamiento del modelo
INICIO_ENTRENAMIENTO = date(2016, 9, 1)
FIN_ENTRENAMIENTO = date(2019, 8, 3)

# Margen de error medio del sistema (de la tabla 11 del TFG)
MAE_CORTO = 6.54   # 14 días
MAE_MEDIO = 7.25   # 30 días

# Umbrales del semáforo en días desde el fin del entrenamiento
UMBRAL_VERDE = 30    # hasta 30 días: fiabilidad alta
UMBRAL_AMBAR = 180   # entre 30 y 180 días: fiabilidad media
                     # más de 180: fiabilidad baja


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
            "titulo": "Fiabilidad alta",
            "dias_desde_fin": dias_desde_fin,
            "dentro_periodo": dentro_periodo,
        }
    elif dias_desde_fin <= UMBRAL_AMBAR:
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
    return MAE_CORTO if horizonte == 14 else MAE_MEDIO