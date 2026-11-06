# User Personas — Predictor de Ingresos

**Contexto del proyecto.** El *Predictor de Ingresos* es un sistema académico que estima si una persona gana más de 50.000 USD al año (censo de EE. UU., 1994) y, sobre todo, **audita qué tan confiable y justo es ese modelo** antes de pensar en usarlo. Su valor no es la predicción en sí, sino la evidencia que entrega: métricas, matriz de confusión, desempeño por grupo y decisiones documentadas.

Estas 12 personas representan a quienes **usarían, evaluarían, operarían o se verían afectados** por un modelo de este tipo. Cada una está asociada a una categoría de interesado del proceso de arquitectura (patrocinador, usuario final, operación TI, seguridad y datos, equipo de desarrollo, afectados).

## Resumen

| # | Persona | Rol | Categoría | Necesidad principal | Prioridad |
|---|---|---|---|---|---|
| 1 | Rodrigo | Docente evaluador | Patrocinador | Verificar la rúbrica desde `develop` | Alta |
| 2 | Laura | Analista de riesgo de crédito | Usuario final | Saber si el modelo es confiable antes de adoptarlo | Alta |
| 3 | Jorge | Analista de políticas públicas | Usuario final | Focalizar subsidios sin excluir grupos | Alta |
| 4 | Camila | Profesional solicitante de crédito | Afectada | Trato justo y explicación de la decisión | Alta |
| 5 | Marcela | Oficial de protección de datos | Seguridad y datos | Cumplir la Ley 1581 de 2012 | Alta |
| 6 | Valentina | Auditora de ética de IA (ONG) | Seguridad y datos | Auditar sesgos con evidencia pública | Alta |
| 7 | Andrés | Científico de datos junior | Equipo de desarrollo | Un pipeline reproducible para aprender y extender | Media |
| 8 | Esteban | Ingeniero DevOps / MLOps | Operación TI | Automatizar pruebas y preparar un despliegue | Media |
| 9 | Ricardo | DBA / ingeniero de datos | Operación TI | Integridad, volumen y almacenamiento de los datos | Media |
| 10 | Diego | Gerente de producto fintech | Patrocinador | Entender el costo de cada tipo de error | Media |
| 11 | Sofía | Estudiante de Ingeniería de Software | Equipo de desarrollo | Entender el proyecto con la documentación | Media |
| 12 | Luis | Trabajador migrante | Afectado | No ser penalizado por su país de origen | Alta |

---

## Fichas detalladas

### 1. Rodrigo — Docente evaluador
- **Contexto:** profesor de Teoría de la Computación II; revisa varios repositorios por semana.
- **Objetivo:** comprobar que el trabajo cumple la rúbrica (modelo, métricas, arquitectura, ética, organización del repo).
- **Frustraciones:** repositorios sin instrucciones, resultados que no se pueden reproducir, commits que no muestran el aporte individual.
- **Cómo lo aborda el proyecto:** rama `develop` como rama por defecto, README con tabla de contenido, `python -m src.pipeline` + `pytest`, CI en verde, commits por etapa en `dev_snieto21`.

### 2. Laura — Analista de riesgo de crédito (cooperativa financiera)
- **Contexto:** evalúa si conviene usar modelos de ingreso para preaprobar créditos de consumo.
- **Objetivo:** saber qué tan bien predice el modelo y qué errores comete.
- **Frustraciones:** proveedores que solo muestran la *accuracy*; no saber cuántos clientes buenos se rechazan.
- **Cómo lo aborda el proyecto:** comparación contra el baseline, precision/recall/F1, matriz de confusión con la interpretación de FP y FN, análisis de umbral.

### 3. Jorge — Analista de políticas públicas
- **Contexto:** trabaja en la focalización de subsidios para hogares de bajos ingresos.
- **Objetivo:** identificar a quién beneficiar sin dejar por fuera a grupos vulnerables.
- **Frustraciones:** modelos de "caja negra" que no se pueden explicar a los entes de control.
- **Cómo lo aborda el proyecto:** modelo interpretable (coeficientes), métricas por sexo, raza y país, discusión sobre paridad demográfica vs igualdad de oportunidad.

### 4. Camila — Profesional solicitante de crédito (persona afectada)
- **Contexto:** ingeniera de 34 años con ingresos altos que solicita un crédito.
- **Objetivo:** que la decisión dependa de su capacidad real de pago, no de su sexo o estado civil.
- **Frustraciones:** rechazos sin explicación y sin forma de apelar.
- **Cómo lo aborda el proyecto:** la auditoría muestra que el modelo detecta peor a las mujeres con ingresos altos (TPR 0.48 vs 0.65); se recomienda supervisión humana, explicación y apelación.

### 5. Marcela — Oficial de protección de datos
- **Contexto:** responde por el cumplimiento de la Ley 1581 de 2012 en su organización.
- **Objetivo:** que los datos sensibles se usen con finalidad clara, minimización y seguridad.
- **Frustraciones:** proyectos que recolectan "todo por si acaso".
- **Cómo lo aborda el proyecto:** dataset público y anonimizado, descarte de `fnlwgt`, sin servicio expuesto, análisis de riesgo de reidentificación, integridad con SHA-256.

### 6. Valentina — Auditora de ética de IA (ONG de derechos digitales)
- **Contexto:** publica informes sobre el uso de algoritmos en decisiones públicas y privadas.
- **Objetivo:** verificar con datos si un modelo discrimina.
- **Frustraciones:** no tener acceso a las métricas por grupo ni al código.
- **Cómo lo aborda el proyecto:** `reports/fairness_*.csv`, experimento sin atributos sensibles, código y datos abiertos, informe con limitaciones explícitas.

### 7. Andrés — Científico de datos junior
- **Contexto:** recién egresado; quiere una base para sus propios proyectos de clasificación.
- **Objetivo:** un pipeline limpio, por etapas y fácil de extender con otro modelo.
- **Frustraciones:** notebooks gigantes que solo funcionan en el computador del autor.
- **Cómo lo aborda el proyecto:** un módulo por etapa en `src/`, `Pipeline` de scikit-learn sin fuga de datos, catálogo de modelos en `models.py`.

### 8. Esteban — Ingeniero DevOps / MLOps
- **Contexto:** lleva modelos a producción en la nube.
- **Objetivo:** que cada cambio se pruebe automáticamente y que el modelo sea portable.
- **Frustraciones:** modelos sin pruebas ni versiones fijadas.
- **Cómo lo aborda el proyecto:** GitHub Actions (pipeline + pytest), modelo serializado con su preprocesamiento, ruta de evolución a API/SageMaker (ADR-003), benchmark de rendimiento.

### 9. Ricardo — DBA / ingeniero de datos
- **Contexto:** administra bases de datos de producción y pipelines de ingesta.
- **Objetivo:** saber qué volumen y tipos de datos maneja el sistema y cómo escalarían.
- **Frustraciones:** proyectos de ML que asumen que los datos "caben en memoria" sin medirlo.
- **Cómo lo aborda el proyecto:** caracterización de tipos y volumen, prueba de escala con 1.000.000 de filas, ADR-005 (lenguaje y almacenamiento), mapeo de columnas a tipos SQL para una futura base de datos.

### 10. Diego — Gerente de producto en una fintech
- **Contexto:** decide si incorporar un modelo de ingresos al flujo de originación.
- **Objetivo:** entender el impacto de negocio de los falsos positivos (mora) y los falsos negativos (clientes perdidos).
- **Frustraciones:** métricas técnicas sin traducción al negocio.
- **Cómo lo aborda el proyecto:** interpretación de cada métrica en lenguaje simple, curva de umbral, criterios de aceptación explícitos.

### 11. Sofía — Estudiante de Ingeniería de Software
- **Contexto:** compañera de semestre que debe hacer un proyecto similar.
- **Objetivo:** entender cómo se conectan el problema, la arquitectura, el modelo y la ética.
- **Frustraciones:** documentación que asume conocimientos previos.
- **Cómo lo aborda el proyecto:** glosario, diagramas C4, ADR con PrOACT, notebook ejecutado con explicaciones.

### 12. Luis — Trabajador migrante (persona afectada)
- **Contexto:** nació fuera de EE. UU.; trabaja tiempo completo como técnico.
- **Objetivo:** no ser clasificado como de ingresos bajos por su país de origen.
- **Frustraciones:** sistemas que usan la nacionalidad como factor de riesgo.
- **Cómo lo aborda el proyecto:** auditoría por país (EE. UU. vs resto), detección de coeficientes inestables en países con pocos datos, recomendación de agrupar o excluir `native_country`.
