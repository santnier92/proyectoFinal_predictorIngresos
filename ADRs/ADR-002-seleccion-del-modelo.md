# ADR-002: Selección del modelo — Regresión Logística

| Campo | Valor |
|---|---|
| **Estado** | Aceptada |
| **Fecha** | 2026-11-06 |
| **Autor** | Santiago Nieto Rodríguez (`dev_snieto21`) |
| **Drivers** | Interpretabilidad (necesaria para el análisis ético), probabilidades útiles para ajustar el umbral, desempeño superior al modelo de referencia |

## Contexto

La tarea es una **clasificación binaria** (`>50K` vs `<=50K`) con datos tabulares mixtos (5 numéricas y 7 categóricas) y clases desbalanceadas (23.9 % positivos). La actividad pide un modelo básico (Regresión Logística, Árbol de Decisión, KNN, etc.) y un análisis ético que exige **explicar por qué** el modelo decide lo que decide.

Se compararon los candidatos con el mismo preprocesamiento, ajuste de hiperparámetros por validación cruzada de 5 folds y evaluación sobre el mismo conjunto de prueba:

| Modelo | Accuracy | Precision | Recall | F1 | ROC-AUC | F1 CV (media ± desv.) |
|---|---|---|---|---|---|---|
| Baseline (clase mayoritaria) | 0.7606 | 0.0000 | 0.0000 | 0.0000 | 0.5000 | 0.0000 |
| **Regresión Logística (C=1.0)** | **0.8562** | **0.7376** | **0.6199** | **0.6736** | **0.9095** | **0.6565 ± 0.0118** |
| Árbol de Decisión (prof. 10, hoja 20) | 0.8660 | 0.7888 | 0.6010 | 0.6822 | 0.9113 | 0.6595 ± 0.0124 |

KNN se descartó de antemano: con 84 variables tras el one-hot y ~39 mil filas, predecir es costoso y las distancias pierden sentido con muchas variables dispersas; además no ofrece una explicación global del modelo.

## Decisión

Se selecciona la **Regresión Logística** (`C=1.0`, `lbfgs`, umbral 0.5) como modelo del sistema. El Árbol de Decisión se mantiene solo como **modelo de comparación**.

Justificación: la diferencia de F1 con el árbol (0.009) es menor que una desviación estándar de la validación cruzada (~0.012), así que **los dos modelos son estadísticamente equivalentes**. Ante ese empate, la Regresión Logística ofrece:

1. **Coeficientes globales e interpretables** (log-odds por variable). Con ellos se detectó que `sex_Female` (−0.97) y variables *proxy* como `relationship` y `marital_status` influyen en la predicción, algo clave para el análisis ético.
2. **Probabilidades suaves**: permiten ajustar el umbral de decisión (con 0.35 el F1 sube a 0.695) y analizar el balance entre precisión y recall.
3. **Estabilidad**: menos varianza entre particiones y menos riesgo de sobreajuste que un árbol profundo.

## Consecuencias

- ✅ Modelo explicable y auditable, coherente con los principios de transparencia del análisis ético.
- ✅ Pocos hiperparámetros, entrenamiento en segundos.
- ⚠️ Asume relaciones lineales en log-odds: no captura interacciones (por ejemplo, edad × horas trabajadas) a menos que se construyan a mano.
- ⚠️ Sacrifica ~1 punto de accuracy frente al árbol.
- ⚠️ Los coeficientes de países poco frecuentes son inestables (pocos ejemplos); se mitiga agrupando categorías con menos de 20 casos (`min_frequency=20`).

## Validación

- Supera al baseline en +0.0956 de accuracy y en +0.6736 de F1.
- Cumple los 5 criterios de aceptación (ver README, sección *Calidad y evaluación*).
- Registro en `reports/model_comparison.csv` y `reports/metrics.json`.
