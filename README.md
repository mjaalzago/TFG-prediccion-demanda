# TFG - Sistema de predicción de demanda para restaurantes con reparto a domicilio

Trabajo Fin de Grado para el Grado en Ingeniería Informática de la Universidad Internacional de La Rioja (UNIR).

**Autora:** María José Álvarez González
**Director:** Luis Pedraza Gomara

## Descripción

Herramienta de predicción de demanda diseñada específicamente para restaurantes con reparto a domicilio. El sistema combina un modelo Prophet enriquecido con variables contextuales externas (meteorología y festivos) y un modelo SARIMA como referencia estadística. Los resultados se consultan a través de un panel de visualización interactivo orientado al gestor del restaurante.

## Estructura del repositorio
├── data/
│   ├── raw/               # Dataset original sin modificar
│   ├── external/          # Datos descargados de APIs (clima, festivos)
│   └── processed/         # Dataset enriquecido listo para modelar
├── notebooks/
│   ├── 00_seleccion_dataset/     # Análisis exploratorio para la selección del dataset
│   ├── 01_carga_datos.ipynb      # Carga y preparación de la serie diaria
│   ├── 02_enriquecimiento_datos.ipynb  # Incorporación de clima y festivos
│   └── 03_modelo_prophet.ipynb   # Entrenamiento del modelo principal
├── requirements.txt       # Dependencias del proyecto
└── README.md

## Requisitos previos

- Python 3.10 o superior
- Sistema operativo: Windows, macOS o Linux

## Instalación

Clonar el repositorio y crear un entorno virtual:

```bash
git clone https://github.com/mjaalzago/TFG-prediccion-demanda.git
cd TFG-prediccion-demanda
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Notas de instalación en Windows

Prophet puede presentar problemas de compilación en Windows cuando se instala mediante `pip`, debido a dependencias nativas de la librería Stan (por ejemplo, `tbb.dll`). Si al ejecutar `pip install -r requirements.txt` se producen errores relacionados con `stan_backend` o DLLs faltantes, se recomienda instalar Prophet alternativamente desde conda-forge, que empaqueta todas las dependencias nativas de forma coherente:

```bash
conda install -c conda-forge prophet
```

## Dataset

El sistema se ha validado sobre el dataset [Takeaway Food Orders](https://www.kaggle.com/datasets/henslersoftware/19560-indian-takeaway-orders), que contiene pedidos reales de dos restaurantes de comida india para llevar ubicados en Londres entre 2015 y 2019.

Los CSV originales deben descargarse manualmente de Kaggle y colocarse en `data/raw/` antes de ejecutar los notebooks.

## Ejecución

Los notebooks están numerados según el orden de ejecución previsto y pueden ejecutarse secuencialmente desde Jupyter o VS Code. Cada notebook genera las entradas necesarias para el siguiente.

## Licencia

Este proyecto se publica con fines académicos en el marco del TFG del Grado en Ingeniería Informática de la UNIR.