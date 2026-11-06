# ADR-004: Estrategia de separación de datos y métrica principal

| Campo | Valor |
|---|---|
| **Estado** | Aceptada |
| **Fecha** | 2026-11-06 |
| **Autor** | Santiago Nieto Rodríguez (`dev_snieto21`) |
| **Drivers** | Resultados válidos (sin fuga de información), clases desbalanceadas, comparabilidad entre modelos |

## Contexto

El dataset tiene 23.9 % de positivos. Con ese desbalance, un modelo que siempre responde `<=50K` logra 76 % de accuracy sin aportar nada, así que la accuracy por sí sola es engañosa. Además hay 52 registros duplicados y, al descartar `fnlwgt`, el 20.7 % de los perfiles de prueba coincide con algún perfil de entrenamiento (son personas distintas con atributos idénticos), lo que podría inflar las métricas.

## Decisión

1. **Deduplicación antes de la partición** de los registros exactos del censo.
2. **Hold-out estratificado 80/20** (`random_state=42`): 39,032 registros de entrenamiento y 9,758 de prueba, ambos con 23.9 % de positivos. El conjunto de prueba solo se usa en la etapa 6.
3. **Validación cruzada estratificada de 5 folds** sobre train para elegir hiperparámetros y medir la estabilidad.
4. **Todo el preprocesamiento dentro del `Pipeline`**: imputación, escalado y one-hot se ajustan solo con los datos de entrenamiento de cada fold.
5. **Métrica principal: F1 de la clase `>50K`**, porque equilibra precisión y recall. ROC-AUC se usa como métrica secundaria (independiente del umbral) y la accuracy siempre se compara contra el baseline.

## Consecuencias

- ✅ Estimación honesta del desempeño en datos no vistos.
- ✅ Comparación justa entre modelos (mismas particiones y semilla).
- ⚠️ El hold-out único depende de la semilla; se mitiga reportando media ± desviación de la validación cruzada.
- ⚠️ Los datos son de 1994: una partición aleatoria no mide la **deriva temporal** (cómo rendiría el modelo con datos actuales).

## Validación

- `test_no_leakage_between_train_and_test`: ningún registro del censo aparece en ambos conjuntos, y la diferencia de tasa positiva entre ellos es menor a 0.005.
- `test_overlapping_profiles_do_not_inflate_metrics`: el F1 sobre perfiles **nunca vistos** (0.691) no es menor que sobre perfiles repetidos (0.602), así que la coincidencia de perfiles no explica el resultado.
- Desviación estándar del F1 en validación cruzada: 0.0118 (≤ 0.02).
