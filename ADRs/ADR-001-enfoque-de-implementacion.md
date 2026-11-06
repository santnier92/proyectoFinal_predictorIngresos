# ADR-001: Enfoque de implementación — pipeline modular en Python + scikit-learn

| Campo | Valor |
|---|---|
| **Estado** | Aceptada |
| **Fecha** | 2026-11-06 |
| **Autor** | Santiago Nieto Rodríguez (`dev_snieto21`) |
| **Drivers** | Reproducibilidad, evidencia de cada etapa del workflow de ML, cero costo de infraestructura |

## Contexto

La actividad exige evidenciar el trabajo en **cada etapa del workflow básico de ML** (definir tarea → recolectar → representar → elegir modelo → entrenar → evaluar → usar con datos nuevos) y que el docente pueda revisar todo desde la rama `develop`. El proyecto lo desarrolla una sola persona, con un plazo corto y sin presupuesto de nube.

Alternativas consideradas:

| Alternativa | A favor | En contra |
|---|---|---|
| **A. Pipeline modular `src/` + notebook de evidencia** | Un módulo por etapa, reproducible por CLI, testeable con `pytest`, el notebook muestra resultados | Requiere algo más de estructura que un notebook suelto |
| B. Un solo notebook Jupyter | Rápido de escribir | Difícil de probar y versionar; los diffs de `.ipynb` son ilegibles; mezcla lógica y presentación |
| C. AWS SageMaker (como en los laboratorios 3.x) | Escalable, despliegue gestionado | Costo, dependencia de credenciales de AWS Academy, complejidad desproporcionada para 48 mil filas |

## Decisión

Se adopta la **alternativa A**: un paquete `src/` con **un módulo por etapa** (`data.py`, `features.py`, `models.py`, `train.py`, `evaluate.py`, `fairness.py`, `predict.py`), orquestado por `src/pipeline.py`. Toda la transformación de datos va dentro de un `sklearn.pipeline.Pipeline`. El notebook `notebooks/workflow_ml.ipynb` reutiliza esos módulos para mostrar la evidencia, sin duplicar la lógica.

## Consecuencias

- ✅ Un solo comando (`python -m src.pipeline`) reproduce todos los números de este repositorio.
- ✅ El preprocesamiento encapsulado en el `Pipeline` evita la fuga de información entre train y test (ver ADR-004).
- ✅ Los criterios de aceptación se verifican automáticamente con `pytest`.
- ⚠️ Corre en una sola máquina: no está pensado para grandes volúmenes ni para inferencia en línea (fuera de alcance).
- ⚠️ Hay que mantener sincronizados el notebook y los módulos; se mitiga porque el notebook solo importa `src`.

## Validación

- `python -m src.pipeline` termina sin errores en ~20 s y genera `reports/metrics.json`.
- `python -m pytest -q` → 6 pruebas superadas.
- El notebook se ejecuta completo con `jupyter nbconvert --execute` sin celdas con error.
