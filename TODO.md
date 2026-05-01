# TODO del proyecto TFG

## Funcionalidades pendientes

### Selección automática de regresores
- [ ] Implementar módulo `src/models/auto_selection.py` durante el refactor.
- [ ] El módulo debe probar varios conjuntos de regresores candidatos
      mediante validación cruzada y elegir el mejor según MAE.
- [ ] Conjuntos a evaluar (mínimo 6-7):
  - Solo festivos.
  - Festivos + 1 variable individual (precipitación, temperatura, viento).
  - Festivos + 2 variables (combinaciones).
  - Festivos + 3 variables (ventana de servicio reducida).
  - Festivos + 5 variables (ventana de servicio completa).
- [ ] Aplicar el módulo automáticamente al entrenar un modelo nuevo
      desde el panel administrativo.
- [ ] Para el caso de estudio (Londres) se mantiene la selección manual
      basada en análisis MCMC.

## Refactor a src/
- [ ] Mover funciones de los notebooks a módulos.
- [ ] Tests unitarios.

## Panel Streamlit
- [ ] RF08: Visualización de predicción + intervalo de confianza.
- [ ] RF09: Desglose por franja horaria.
- [ ] Gestión manual de eventos puntuales.

## Memoria del TFG (acumulado)
- [ ] Corregir frase capítulo 4 sobre festivos locales.
- [ ] Corregir errata `make_holydays_df` → `make_holidays_df`.
- [ ] Aclarar que `make_holidays_df` es función de Prophet.
- [ ] Mencionar la función propia `cargar_festivos`.
- [ ] Justificar exclusión de eventos del entrenamiento.
- [ ] Describir gestión de eventos desde el panel.
- [ ] Justificar limitación clima a 14 días + estrategia dos modelos.
- [ ] Documentar problema instalación Prophet en Windows.
- [ ] Incluir gráfica de componentes Prophet con interpretación.
- [ ] Mencionar análisis MCMC con coeficientes estandarizados.
- [ ] Explicar redundancia temperatura/estacionalidad anual con experimento.
- [ ] Justificar exclusión de la temperatura del conjunto reducido.
- [ ] Mencionar la selección automática de regresores como mecanismo de generalización del sistema.