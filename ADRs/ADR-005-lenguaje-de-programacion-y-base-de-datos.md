# ADR-005: Lenguaje de programación (Python) y almacenamiento de datos (archivos versionados, sin motor de base de datos)

| Campo | Valor |
|---|---|
| **Estado** | Aceptada |
| **Fecha** | 2026-11-06 |
| **Autor** | Santiago Nieto Rodríguez (`dev_snieto21`) |
| **Drivers** | Ecosistema de ML maduro, reproducibilidad, volumen de datos, costo cero |

## Contexto

El sistema tiene que leer un dataset tabular, entrenar y evaluar modelos clásicos y producir métricas, gráficos y reportes. Hay que decidir **en qué lenguaje** se implementa y **dónde se almacenan** los datos de entrada.

Características de los datos (medidas con `python -m src.benchmark`):

| Aspecto | Valor |
|---|---|
| Registros | 48,842 (48,790 sin duplicados) |
| Columnas | 15: 6 numéricas enteras y 9 categóricas de texto |
| Tamaño en disco (CSV) | 5.3 MB |
| Tamaño en memoria (pandas) | ~22 MB |
| Patrón de acceso | Lectura completa por lotes (*batch*), sin escrituras concurrentes ni consultas puntuales |
| Frecuencia de actualización | Ninguna: dataset histórico estático (1994) |

### Alternativas consideradas

**Lenguaje:** Python 3, R y Java (Weka / Tribuo).
**Almacenamiento:** CSV versionado en Git, SQLite, PostgreSQL (p. ej., AWS RDS), MongoDB, Parquet en S3.

## PrOACT

**Problema:** elegir un lenguaje y un almacenamiento acordes con el tamaño, el tipo de datos y el patrón de acceso, sin agregar complejidad innecesaria.

**Objetivos:** (1) bibliotecas de ML y de métricas de equidad disponibles, (2) reproducibilidad, (3) rendimiento suficiente para escenarios de hasta 1 millón de filas, (4) costo y operación mínimos.

### Lenguaje

| Criterio | **Python 3 + scikit-learn** | R (tidymodels) | Java (Weka) |
|---|---|---|---|
| Ecosistema de ML y equidad | Muy amplio (scikit-learn, pandas, Fairlearn, SHAP) | Amplio | Limitado |
| Integración con CI, notebooks y nube | Nativa (Jupyter, GitHub Actions, SageMaker) | Media | Media |
| Curva de aprendizaje del equipo | Baja (usado en los laboratorios del curso) | Media | Alta |
| Rendimiento con 1M de filas | 19 s de entrenamiento (medido) | Similar | Similar |

### Almacenamiento

| Criterio | **CSV versionado + SHA-256** | SQLite | PostgreSQL (RDS) | MongoDB | Parquet en S3 |
|---|---|---|---|---|---|
| Ajuste al patrón de acceso (lectura batch) | Alto | Alto | Medio (sobredimensionado) | Bajo (datos tabulares) | Alto |
| Reproducible al clonar el repo | Sí | Sí | No (servidor externo) | No | No (credenciales) |
| Integridad verificable | Sí (hash) | Parcial | Sí (constraints) | Parcial | Sí |
| Operación (backups, usuarios, parches) | Ninguna | Mínima | Alta | Alta | Media |
| Costo | Cero | Cero | Instancia por hora | Clúster | Almacenamiento |
| Escala a millones de filas | Hasta ~1–5 M en memoria | Decenas de M | Cientos de M+ | Cientos de M+ | Miles de M |

## Decisión

1. **Lenguaje: Python 3.11** con pandas, NumPy, scikit-learn y Matplotlib.
2. **Almacenamiento: archivo CSV versionado en el repositorio** (`data/raw/adult.csv`), con su integridad verificada por SHA-256 en cada carga. **No se usa un motor de base de datos**, porque el volumen (5 MB), la naturaleza estática de los datos y la lectura por lotes no lo justifican.

**Ruta de evolución.** Si el sistema llegara a recibir datos nuevos de forma continua, varios usuarios concurrentes o decenas de millones de registros, los datos pasarían a **PostgreSQL** (por ejemplo, Amazon RDS o Aurora), con un esquema tipado como el siguiente, o a **Parquet particionado en S3** si el uso es solo analítico:

```sql
-- Target schema if the dataset moves to PostgreSQL
CREATE TABLE census_income (
    record_id       BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    age             SMALLINT     NOT NULL CHECK (age BETWEEN 0 AND 120),
    workclass       VARCHAR(32),
    education_num   SMALLINT     NOT NULL CHECK (education_num BETWEEN 1 AND 16),
    marital_status  VARCHAR(32)  NOT NULL,
    occupation      VARCHAR(32),
    relationship    VARCHAR(32)  NOT NULL,
    race            VARCHAR(32)  NOT NULL,
    sex             VARCHAR(8)   NOT NULL,
    capital_gain    INTEGER      NOT NULL DEFAULT 0,
    capital_loss    INTEGER      NOT NULL DEFAULT 0,
    hours_per_week  SMALLINT     NOT NULL CHECK (hours_per_week BETWEEN 1 AND 168),
    native_country  VARCHAR(48),
    income_gt_50k   BOOLEAN      NOT NULL,
    loaded_at       TIMESTAMPTZ  NOT NULL DEFAULT now()
);
-- Sensitive columns (race, sex, native_country) would be restricted via column-level GRANTs.
```

## Consecuencias

- ✅ Cualquier persona clona el repo y ejecuta todo sin instalar ni configurar un servidor.
- ✅ Python permite reutilizar el mismo código en Jupyter, la CLI, el CI y, a futuro, SageMaker.
- ✅ Sin servidor no hay credenciales que proteger ni superficie de ataque de red.
- ⚠️ El CSV no impone tipos ni restricciones: la validación se hace en código (`load_raw`, contrato de columnas en `predict`).
- ⚠️ El enfoque en memoria tiene un techo de escala (~1–5 M filas con 7 GB de RAM); más allá se requiere la ruta de evolución.

## Tradeoffs - Mitigations

| Tradeoff | Mitigación |
|---|---|
| Sin tipos ni constraints a nivel de almacenamiento | Validación por checksum, perfil del dataset y contrato de columnas en la predicción |
| Límite de memoria con volúmenes muy grandes | Benchmark de escala (1M de filas: 19 s, 468 MB); esquema PostgreSQL y opción Parquet documentados |
| Python es más lento que lenguajes compilados en bucles puros | El cómputo pesado lo hacen NumPy y scikit-learn (C/Cython) |
| Datos sensibles en texto plano dentro del repo | El dataset es público y anonimizado; en un caso real, la base de datos tendría GRANTs por columna y cifrado en reposo |

## Validación

- `python -m src.benchmark` → `reports/performance.json`: entrenamiento de 0.8 s con los datos reales y de 19.1 s con 1,000,000 de filas; inferencia por lotes de más de 800,000 filas/s; latencia individual p95 de ~3.4 ms.
- `test_dataset_checksum_and_shape` verifica la integridad del archivo en cada ejecución del CI.
