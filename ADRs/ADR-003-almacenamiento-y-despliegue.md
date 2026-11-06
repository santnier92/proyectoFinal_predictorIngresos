# ADR-003: Almacenamiento de datos/modelo y despliegue — artefactos versionados en Git, ejecución local por CLI

| Campo | Valor |
|---|---|
| **Estado** | Aceptada |
| **Fecha** | 2026-11-06 |
| **Autor** | Santiago Nieto Rodríguez (`dev_snieto21`) |
| **Drivers** | El docente debe poder reproducir y revisar todo desde la rama `develop`; integridad de datos; costo cero |

## Contexto

El sistema necesita guardar tres tipos de artefactos: el **dataset de entrada**, el **modelo entrenado** y los **reportes** (métricas y figuras). Además, debe poder usarse con datos nuevos (etapa 7 del workflow). No hay requerimiento de inferencia en línea ni de usuarios concurrentes.

| Alternativa | A favor | En contra |
|---|---|---|
| **A. CSV + `.joblib` + reportes versionados en Git; predicción por CLI** | Reproducible, revisable en GitHub, sin costo, sin credenciales | No sirve predicciones en línea |
| B. Dataset en S3 + endpoint de SageMaker | Escalable, desplegable en producción | Costo, credenciales temporales de AWS Academy, el docente no podría reproducirlo |
| C. API REST (FastAPI) en un contenedor | Muestra un despliegue real | Fuera del alcance de la actividad; más superficie de ataque y mantenimiento |

## PrOACT

**Problema:** persistir datos, modelo y reportes, y permitir el uso del modelo con datos nuevos, sin depender de infraestructura externa.

**Objetivos:** (1) que el docente reproduzca todo desde `develop`, (2) integridad de los datos, (3) costo cero, (4) una superficie de ataque mínima.

| Criterio | A. Git + `.joblib` + CLI | B. S3 + SageMaker endpoint | C. API FastAPI en contenedor |
|---|---|---|---|
| Reproducible desde el repo | Sí | No (requiere cuenta de AWS) | Parcial |
| Integridad verificable | Sí (SHA-256) | Sí (versionado de S3) | Depende |
| Costo | Cero | Por hora del endpoint | Hosting |
| Superficie de ataque | Mínima (local) | Endpoint público | API expuesta |
| Inferencia en línea | No | Sí | Sí |

**Consecuencias evaluadas:** A cumple todos los objetivos; la inferencia en línea está fuera del alcance.

**Tradeoffs:** no hay servicio en línea, a cambio de simplicidad y reproducibilidad.

## Decisión

- **Datos**: `data/raw/adult.csv` (5.3 MB, licencia CC BY 4.0) versionado en el repositorio. Su **hash SHA-256** queda en `src/config.py` y se verifica en cada carga, así que cualquier alteración del archivo detiene el pipeline.
- **Modelo**: el `Pipeline` completo (preprocesamiento + modelo) serializado en `models/logreg.joblib` (~8 KB). Al guardar el preprocesamiento junto con el modelo, la inferencia aplica exactamente las mismas transformaciones que el entrenamiento.
- **Reportes**: `reports/metrics.json`, CSV y PNG versionados como evidencia.
- **Despliegue / uso**: CLI local `python -m src.predict --input <csv> [--threshold t]`, que valida las columnas de entrada antes de predecir.

## Consecuencias

- ✅ Cualquier persona clona el repositorio y obtiene exactamente los mismos números.
- ✅ La integridad del dataset se puede verificar (control contra cambios accidentales o maliciosos en los datos).
- ⚠️ Los archivos `.joblib` solo deben cargarse si vienen de una fuente confiable (pickle puede ejecutar código); el modelo lo genera el propio pipeline.
- ⚠️ El modelo depende de la versión de scikit-learn; se fija una versión mínima en `requirements.txt`.
- 🔜 Evolución posible: empaquetar `src.predict` detrás de una API y desplegarla en SageMaker o en un contenedor si apareciera un caso de uso real.

## Tradeoffs - Mitigations

| Tradeoff | Mitigación |
|---|---|
| Sin inferencia en línea | CLI `src.predict` con contrato de entrada validado; ruta de evolución a API documentada |
| `.joblib` (pickle) puede ejecutar código al cargarse | Solo se cargan modelos generados por el propio pipeline y versionados en el repo |
| Dependencia de la versión de scikit-learn | Versión mínima en `requirements.txt` y CI que reentrena y valida en cada PR |
| Dataset de 5 MB dentro del repo | Tamaño aceptable; hash en `config.py` para detectar cualquier cambio |

## Validación

- `test_dataset_checksum_and_shape` verifica el hash y la forma (48842 × 15).
- `test_prediction_contract` verifica que las probabilidades estén en [0, 1], que las etiquetas sean válidas y que el sistema rechace entradas sin las columnas requeridas.
