"""Builds docs/Informe_Actividad6.pdf (APA 7th edition, student paper) from
reports/metrics.json and the figures in reports/figures.

Usage (after `python -m src.pipeline`):
    python docs/build_report.py
"""
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (CondPageBreak, Image, KeepTogether, PageBreak, Paragraph,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"
R = json.loads((ROOT / "reports" / "metrics.json").read_text(encoding="utf-8"))
OUT = ROOT / "docs" / "Informe_Actividad6.pdf"
REPO_URL = "https://github.com/santnier92/proyectoFinal_predictorIngresos/tree/develop"

# --- Fonts: Times New Roman 12 pt (APA 7). Liberation Serif is metric-compatible.
SERIF_DIRS = [Path("C:/Windows/Fonts"), Path("/usr/share/fonts/truetype/msttcorefonts"),
              Path("/usr/share/fonts/truetype/liberation")]
FONT_SETS = [("times.ttf", "timesbd.ttf", "timesi.ttf", "timesbi.ttf"),
             ("Times_New_Roman.ttf", "Times_New_Roman_Bold.ttf", "Times_New_Roman_Italic.ttf",
              "Times_New_Roman_Bold_Italic.ttf"),
             ("LiberationSerif-Regular.ttf", "LiberationSerif-Bold.ttf", "LiberationSerif-Italic.ttf",
              "LiberationSerif-BoldItalic.ttf")]
FONT = "Times-Roman"
for d in SERIF_DIRS:
    for fs in FONT_SETS:
        if all((d / f).exists() for f in fs):
            for name, f in zip(("TNR", "TNR-B", "TNR-I", "TNR-BI"), fs):
                pdfmetrics.registerFont(TTFont(name, str(d / f)))
            pdfmetrics.registerFontFamily("TNR", normal="TNR", bold="TNR-B", italic="TNR-I", boldItalic="TNR-BI")
            FONT = "TNR"
            break
    if FONT == "TNR":
        break
BOLD = "TNR-B" if FONT == "TNR" else "Times-Bold"

NAVY = colors.HexColor("#0b3d6b")
LIGHT = colors.HexColor("#e8eef5")
DS = 24  # double spacing for 12 pt text
S = {
    "title": ParagraphStyle("title", fontName=BOLD, fontSize=12, leading=DS, alignment=TA_CENTER),
    "center": ParagraphStyle("center", fontName=FONT, fontSize=12, leading=DS, alignment=TA_CENTER),
    "h1": ParagraphStyle("h1", fontName=BOLD, fontSize=12, leading=DS, alignment=TA_CENTER, keepWithNext=1),
    "h2": ParagraphStyle("h2", fontName=BOLD, fontSize=12, leading=DS, alignment=TA_LEFT, keepWithNext=1),
    "p": ParagraphStyle("p", fontName=FONT, fontSize=12, leading=DS, firstLineIndent=0.5 * inch,
                        alignment=TA_LEFT),
    "b": ParagraphStyle("b", fontName=FONT, fontSize=12, leading=DS, leftIndent=0.5 * inch,
                        bulletIndent=0.25 * inch, bulletFontName=FONT, alignment=TA_LEFT),
    "label": ParagraphStyle("label", fontName=BOLD, fontSize=12, leading=DS, keepWithNext=1),
    "ttitle": ParagraphStyle("ttitle", fontName=FONT, fontSize=12, leading=DS, keepWithNext=1),
    "note": ParagraphStyle("note", fontName=FONT, fontSize=10.5, leading=13, spaceBefore=4, spaceAfter=12),
    "cell": ParagraphStyle("cell", fontName=FONT, fontSize=10, leading=12),
    "cellb": ParagraphStyle("cellb", fontName=BOLD, fontSize=10, leading=12, textColor=colors.white),
    "ref": ParagraphStyle("ref", fontName=FONT, fontSize=12, leading=DS, leftIndent=0.5 * inch,
                          firstLineIndent=-0.5 * inch, alignment=TA_LEFT),
}

story = []
n_table, n_fig = [0], [0]


def P(text, st="p"):
    if st in ("h1", "h2"):
        story.append(CondPageBreak((5 if st == "h1" else 3.5) * cm))
    story.append(Paragraph(text, S[st]))


def bullets(items):
    for it in items:
        story.append(Paragraph(it, S["b"], bulletText="•"))


def table(title, rows, widths, note=None, header=True):
    """APA table: bold number + italic title above, optional note below."""
    n_table[0] += 1
    data = [[Paragraph(str(c), S["cellb"] if header and i == 0 else S["cell"]) for c in r]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9aa9b8")),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
    for i in range(1, len(rows)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    t.setStyle(TableStyle(style))
    head = [Paragraph(f"Tabla {n_table[0]}", S["label"]), Paragraph(f"<i>{title}</i>", S["ttitle"])]
    story.append(CondPageBreak(4 * cm))
    if len(rows) <= 8:
        story.append(KeepTogether(head + [t]))
    else:
        story.extend(head + [t])
    story.append(Paragraph(f"<i>Nota.</i> {note}", S["note"]) if note else Spacer(1, 12))


def figure(name, width_cm, title, note=None):
    """APA figure: bold number + italic title above, image, optional note below."""
    n_fig[0] += 1
    img = Image(str(name if str(name).startswith("/") else FIG / name))
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth, img.drawHeight = width_cm * cm, width_cm * cm * ratio
    parts = [Paragraph(f"Figura {n_fig[0]}", S["label"]), Paragraph(f"<i>{title}</i>", S["ttitle"]), img]
    parts.append(Paragraph(f"<i>Nota.</i> {note}", S["note"]) if note else Spacer(1, 12))
    story.append(KeepTogether(parts))


f = lambda x, n=4: f"{x:.{n}f}"
pct = lambda x: f"{100 * x:.1f} %"
M = R["models"]
LR, BL, DT = M["logreg"]["test"], M["baseline"]["test"], M["decision_tree"]["test"]
CV = M["logreg"]["cv"]
FS, FR = R["fairness"]["logreg"]["sex"], R["fairness"]["logreg"]["race"]
FSU = R["fairness"]["logreg_unaware"]["sex"]
prof, split, lc, ta = R["data_profile"], R["split"], R["leakage_check"], R["threshold_analysis"]
g = lambda tbl, name: next(x for x in tbl["groups"] if x["group"] == name)
coef = {**R["top_coefficients"]["positive"], **R["top_coefficients"]["negative"]}
thousands = lambda n: f"{n:,}".replace(",", ".")
TITLE = "Predictor de Ingresos: Evaluación y Análisis Ético de un Modelo de Regresión Logística"

# ============================================================== title page (APA 7 student)
story.append(Spacer(1, 2.6 * inch))
P(TITLE, "title")
story.append(Spacer(1, DS))
for line in ["Santiago Nieto Rodríguez",
             "Facultad de Ingeniería, Universidad de La Salle",
             "Teoría de la Computación II: Actividad 6, Mini-proyecto",
             "Rodrigo Aranda Fernández",
             "6 de noviembre de 2026"]:
    P(line, "center")
story.append(PageBreak())

# ============================================================== introduction and objectives
P(TITLE, "title")
P("Introducción", "h1")
P("Cada vez más decisiones que afectan a las personas, como aprobar un crédito, asignar un subsidio u ofrecer "
  "un empleo, se apoyan en modelos de <i>machine learning</i> entrenados con datos históricos. Estos modelos "
  "pueden ahorrar tiempo y dar resultados consistentes, pero también pueden equivocarse más con unos grupos que "
  "con otros y repetir desigualdades del pasado sin que nadie lo note. Por eso, para valorar un modelo no basta "
  "con saber si «acierta mucho»: también hay que entender cómo se equivoca y a quién afectan sus errores "
  "(Barocas et al., 2023).")
P("En este mini-proyecto construí un modelo sencillo de <i>machine learning</i>, medí qué tan bien funciona "
  "y analicé sus riesgos éticos. El modelo responde una pregunta concreta: a partir de datos como la edad, la "
  "educación, la ocupación y las horas de trabajo, ¿la persona gana más de 50.000 dólares al año? Para "
  "responderla usé una regresión logística entrenada con el conjunto de datos <i>Adult</i>, que proviene del "
  "censo de Estados Unidos de 1994 (Becker &amp; Kohavi, 1996). Elegí este conjunto porque es un caso clásico "
  "de estudio y porque incluye variables sensibles, como el sexo y la raza, que permiten hacer un análisis "
  "ético con datos concretos.")
P("Todo el trabajo se puede revisar y volver a ejecutar desde el repositorio del proyecto, en la rama "
  f"<b>develop</b>, que es la que se debe calificar: <a href='{REPO_URL}' color='#0b3d6b'><u>{REPO_URL}</u></a> "
  "(Nieto Rodríguez, 2026). Allí están el código, el modelo entrenado, las pruebas automáticas, los diagramas "
  "de arquitectura, las decisiones técnicas (ADR) y este informe.")
P("El documento sigue el orden de la actividad. Después de los objetivos, explico por qué elegí el modelo y "
  "cómo son los datos. Luego presento las métricas y la matriz de confusión. Después analizo los sesgos, la "
  "equidad, la privacidad y el impacto social del modelo. Al final cierro con las conclusiones y algunas "
  "recomendaciones para mejorarlo. La Tabla 1 resume los resultados principales.")
table("Resumen de indicadores clave del modelo (conjunto de prueba)", [
    ["Indicador clave (conjunto de prueba)", "Valor"],
    ["Accuracy / baseline", f"{f(LR['accuracy'])} / {f(BL['accuracy'])}"],
    ["F1-score clase >50K", f(LR["f1"])],
    ["ROC-AUC", f(LR["roc_auc"])],
    ["Criterios de aceptación cumplidos", "5 de 5"],
    ["Brecha de recall (TPR) hombres vs mujeres", f(FS["gaps"]["equal_opportunity_diff"], 3)],
], [9 * cm, 5 * cm], note="El baseline es un modelo de referencia que siempre predice la clase mayoritaria (≤50K).")

P("Objetivos", "h1")
P("Objetivo General", "h2")
P("Aplicar métricas de evaluación y realizar un análisis ético para valorar un modelo sencillo de <i>machine "
  "learning</i> que predice si una persona gana más de 50.000 dólares al año, y presentar conclusiones "
  "fundamentadas y alineadas con los temas del curso.")
P("Objetivos Específicos", "h2")
for i, txt in enumerate([
    "Seleccionar un modelo básico de clasificación y justificar su elección frente a otras alternativas.",
    "Describir el conjunto de datos <i>Adult</i>: sus variables, la variable objetivo y la calidad de los datos.",
    "Implementar las siete etapas del flujo de trabajo de <i>machine learning</i> en un repositorio "
    "reproducible, con pruebas automáticas y decisiones de arquitectura documentadas.",
    "Evaluar el modelo con accuracy, precision, recall, F1-score, ROC-AUC y la matriz de confusión, "
    "comparándolo con un modelo de referencia y con criterios de aceptación definidos.",
    "Analizar los sesgos, la equidad, la privacidad, el impacto social y la transparencia del modelo, "
    "midiendo su desempeño por sexo, raza y país de origen.",
    "Redactar conclusiones técnicas y proponer recomendaciones para mejorar el modelo.",
], start=1):
    story.append(Paragraph(txt, S["b"], bulletText=f"{i}."))

# ============================================================== model
P("Selección del Modelo", "h1")
P("Elegí la <b>regresión logística</b>. Este modelo calcula la probabilidad de que una persona gane más de "
  "50K combinando sus variables en una fórmula lineal que luego pasa por la función sigmoide: "
  "<i>P(y=1|x) = 1 / (1 + e<super>−(β₀ + β·x)</super>)</i>. Lo elegí por cuatro razones:")
bullets([
    "<b>Encaja con el problema.</b> La respuesta es sí o no (clasificación binaria) y los datos vienen en una "
    "tabla.",
    "<b>Se puede explicar.</b> Cada variable tiene un coeficiente que dice si sube o baja la probabilidad de "
    "ganar más de 50K, y cuánto. Esto es clave para el análisis ético, porque permite ver qué está mirando el "
    "modelo para decidir.",
    "<b>Da probabilidades, no solo etiquetas.</b> Así se puede mover el punto de corte según qué error resulte "
    "más costoso.",
    f"<b>Rinde igual que un árbol de decisión.</b> El árbol obtuvo un F1 de {f(DT['f1'])} y la regresión "
    f"logística {f(LR['f1'])}. La diferencia ({DT['f1'] - LR['f1']:.3f}) es menor que la variación normal entre "
    f"particiones de la validación cruzada ({CV['f1']['std']:.3f}), así que en la práctica empatan.",
])
P("Descarté KNN porque, después de convertir las categorías en columnas, quedan 84 variables. Con tantas "
  "dimensiones las distancias entre puntos pierden sentido, cada predicción es lenta y el modelo no ofrece una "
  "explicación general. El hiperparámetro de la regresión logística se eligió con validación cruzada de cinco "
  f"particiones y el mejor valor fue <b>C = {M['logreg']['best_params'].get('model__C')}</b> (Pedregosa et al., "
  "2011).")

# ============================================================== dataset
P("Descripción del Conjunto de Datos", "h1")
P(f"El conjunto <i>Adult</i> tiene <b>{thousands(prof['rows'])} registros y {prof['columns']} columnas</b> y se "
  f"publica con licencia CC BY 4.0 (Becker &amp; Kohavi, 1996). Solo el <b>{pct(prof['positive_rate'])}</b> de "
  f"las personas gana más de 50K, así que las clases están desbalanceadas. También encontré "
  f"{prof['duplicates']} registros duplicados y datos faltantes, marcados con «?», en las columnas workclass "
  f"({thousands(prof['missing_by_column']['workclass'])}), occupation "
  f"({thousands(prof['missing_by_column']['occupation'])}) y native_country "
  f"({thousands(prof['missing_by_column']['native_country'])}). La Tabla 2 describe cada variable.")
table("Variables del conjunto de datos Adult y su uso en el modelo", [
    ["Variable", "Tipo", "Descripción", "Uso en el modelo"],
    ["age", "Numérica", "Edad en años", "Feature"],
    ["workclass", "Categórica", "Tipo de empleador", "Feature"],
    ["fnlwgt", "Numérica", "Peso muestral del censo", "Descartada (no describe a la persona)"],
    ["education", "Categórica", "Nivel educativo en texto", "Descartada (redundante)"],
    ["education_num", "Numérica", "Nivel educativo 1–16", "Feature"],
    ["marital_status", "Categórica", "Estado civil", "Feature (proxy de sexo)"],
    ["occupation", "Categórica", "Ocupación", "Feature"],
    ["relationship", "Categórica", "Rol en el hogar", "Feature (proxy de sexo)"],
    ["race", "Categórica", "Raza", "Feature sensible / auditada"],
    ["sex", "Categórica", "Sexo", "Feature sensible / auditada"],
    ["capital_gain / capital_loss", "Numéricas", "Ganancias y pérdidas de capital", "Features"],
    ["hours_per_week", "Numérica", "Horas trabajadas por semana", "Feature"],
    ["native_country", "Categórica", "País de origen", "Feature sensible / auditada"],
    ["income", "Binaria", "&gt;50K (1) o &lt;=50K (0)", "Variable objetivo"],
], [3.6 * cm, 2.2 * cm, 4.6 * cm, 5.6 * cm],
    note="Una variable <i>proxy</i> no es sensible por sí misma, pero está muy relacionada con una que sí lo es.")
P("La Tabla 3 muestra cinco registros reales del archivo, para dar una idea de cómo se ven los datos.")
table("Muestra de registros del conjunto de datos", [
    ["age", "workclass", "education_num", "occupation", "sex", "race", "hours", "income"],
    ["39", "State-gov", "13", "Adm-clerical", "Male", "White", "40", "&lt;=50K"],
    ["50", "Self-emp-not-inc", "13", "Exec-managerial", "Male", "White", "13", "&lt;=50K"],
    ["38", "Private", "9", "Handlers-cleaners", "Male", "White", "40", "&lt;=50K"],
    ["31", "Private", "14", "Prof-specialty", "Female", "White", "50", "&gt;50K"],
    ["42", "Private", "13", "Exec-managerial", "Male", "White", "40", "&gt;50K"],
], [1.2 * cm, 2.8 * cm, 2.1 * cm, 3.0 * cm, 1.5 * cm, 1.4 * cm, 1.3 * cm, 1.6 * cm])
figure("eda_target_and_groups.png", 16,
       "Distribución de la variable objetivo y proporción de personas con ingresos mayores a 50K por sexo y raza",
       note="Elaboración propia con los datos originales de Becker y Kohavi (1996).")
P("<b>Objetivo del modelo.</b> Aprender la relación entre las 12 variables de entrada y la variable "
  "<i>income</i>, para estimar la probabilidad de que una persona nueva gane más de 50K al año.")

# ============================================================== method
P("Metodología", "h1")
P("Seguí las siete etapas del flujo de trabajo de <i>machine learning</i> vistas en clase. Cada etapa tiene su "
  "propio módulo en el repositorio y queda registrada en un cuaderno de Jupyter ya ejecutado. La Tabla 4 "
  "resume qué hice en cada una.")
table("Etapas del flujo de trabajo de machine learning aplicadas en el proyecto", [
    ["Etapa", "Qué se hizo"],
    ["1. Definir la tarea", "Clasificación binaria &gt;50K vs &lt;=50K; métrica principal: F1 de la clase positiva."],
    ["2. Recolectar datos", "Carga del CSV de UCI con verificación SHA-256 y perfil del dataset."],
    ["3. Representar la entrada",
     f"Deduplicación antes de partir los datos ({thousands(split['rows_after_dedup'])} filas); partición "
     f"estratificada 80/20 (train {thousands(split['train_rows'])} / test {thousands(split['test_rows'])}); "
     "imputación (mediana / 'Unknown'), escalado estándar y one-hot (84 variables) dentro de un Pipeline."],
    ["4. Elegir el modelo", "Baseline (clase mayoritaria), Regresión Logística, Árbol de Decisión y Regresión "
                            "Logística sin atributos sensibles."],
    ["5. Entrenar", "GridSearchCV con 5 folds estratificados, optimizando F1, solo sobre train."],
    ["6. Evaluar", "Métricas en test, matriz de confusión, curva ROC, análisis de umbral, coeficientes, "
                   "auditoría de equidad y criterios de aceptación."],
    ["7. Usar con datos nuevos", "CLI src.predict: recibe un CSV y devuelve la probabilidad y la clase."],
], [4 * cm, 12 * cm])
P("Un cuidado importante fue evitar la fuga de información. El conjunto de prueba se separó desde el principio "
  "y no se usó para entrenar ni para elegir hiperparámetros. Además, todas las transformaciones de los datos se "
  "ajustan solo con los datos de entrenamiento.")

# ============================================================== metrics
P("Métricas de Evaluación", "h1")
P("Todas las métricas se calcularon con el <b>conjunto de prueba</b>, que tiene 9.758 registros que el modelo "
  "nunca vio. La Tabla 5 compara los cuatro modelos.")
rows = [["Modelo", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]]
for name, lab in [("baseline", "Baseline (clase mayoritaria)"), ("logreg", "<b>Regresión Logística</b>"),
                  ("decision_tree", "Árbol de Decisión"), ("logreg_unaware", "Reg. Logística sin atributos sensibles")]:
    t = M[name]["test"]
    rows.append([lab] + [f(t[k]) for k in ("accuracy", "precision", "recall", "f1", "roc_auc")])
table("Desempeño de los modelos en el conjunto de prueba", rows,
      [5.6 * cm, 2.1 * cm, 2.1 * cm, 2.1 * cm, 2.1 * cm, 2.1 * cm],
      note="La regresión logística es el modelo seleccionado. Valores con umbral de decisión de 0.5.")
P("En palabras sencillas, cada métrica responde una pregunta distinta. La Tabla 6 explica qué significa cada "
  "valor de la regresión logística en este problema.")
table("Interpretación de las métricas de la regresión logística", [
    ["Métrica", "Valor", "Qué significa en este problema"],
    ["Accuracy", f(LR["accuracy"]),
     f"Acierta con el {pct(LR['accuracy'])} de las personas. Pero ojo: un modelo que siempre dice «≤50K» ya "
     f"acierta el {pct(BL['accuracy'])} sin aprender nada. La mejora real es de "
     f"+{100 * (LR['accuracy'] - BL['accuracy']):.1f} puntos. Cuando las clases están desbalanceadas, la accuracy "
     "sola engaña."],
    ["Precision", f(LR["precision"]),
     f"De cada 100 personas que el modelo marca como &gt;50K, unas {round(100 * LR['precision'])} sí lo son. "
     "Indica qué tanto confiar en un «sí» del modelo."],
    ["Recall", f(LR["recall"]),
     f"Encuentra al {pct(LR['recall'])} de quienes de verdad ganan &gt;50K; se le escapa el "
     f"{pct(1 - LR['recall'])}. Indica cuántos casos positivos logra detectar."],
    ["F1-score", f(LR["f1"]),
     "Equilibra precision y recall en un solo número. Es la métrica principal porque castiga los dos tipos de "
     "error. El baseline saca 0."],
    ["ROC-AUC", f(LR["roc_auc"]),
     f"Si se toma al azar una persona con &gt;50K y otra con ≤50K, el modelo le da más probabilidad a la primera "
     f"en el {pct(LR['roc_auc'])} de los casos. No depende del punto de corte."],
    ["CV F1 (5 folds)", f"{f(CV['f1']['mean'])} ± {f(CV['f1']['std'])}",
     "El resultado casi no cambia entre particiones distintas del entrenamiento, así que no es cuestión de "
     "suerte."],
], [2.6 * cm, 2.4 * cm, 11 * cm])
figure("roc_curve.png", 10, "Curvas ROC de los modelos en el conjunto de prueba",
       note="El baseline coincide con la diagonal (AUC = 0.5), que equivale a adivinar al azar.")
P(f"<b>Punto de corte.</b> Por defecto el modelo dice «&gt;50K» cuando la probabilidad supera 0.5. Con ese "
  f"valor es prudente: acierta mucho cuando dice que sí, pero deja pasar varios casos. Si el corte baja a "
  f"<b>{ta['best_threshold_for_f1']:.2f}</b>, el F1 sube a <b>{ta['best_f1']:.3f}</b>, porque el modelo detecta "
  "más casos a cambio de equivocarse un poco más. Elegir el corte no es solo una decisión técnica: depende de "
  "qué error resulta más grave en el uso real (Figura 3).")
figure("threshold_tradeoff.png", 10, "Precision, recall y F1 según el punto de corte de la regresión logística")

# ============================================================== confusion matrix
P("Matriz de Confusión", "h1")
P("La matriz de confusión cruza lo que el modelo predijo con lo que realmente pasó. Así se ven los aciertos y "
  "los dos tipos de error por separado (Figura 4 y Tabla 7).")
figure("confusion_matrix_logreg.png", 8.5, "Matriz de confusión de la regresión logística",
       note="Conjunto de prueba con umbral de decisión de 0.5. Clase 1 = ingresos mayores a 50K.")
table("Significado de cada celda de la matriz de confusión", [
    ["Celda", "Valor", "Significado en este problema"],
    ["Verdaderos positivos (VP)", thousands(LR["tp"]),
     "Personas que ganan &gt;50K y el modelo las reconoció bien."],
    ["Falsos positivos (FP)", thousands(LR["fp"]),
     "Personas que ganan ≤50K, pero el modelo dijo &gt;50K. En un uso real, por ejemplo un crédito, se le podría "
     "aprobar a alguien que no puede pagarlo. Es el error de <i>sobreestimar</i>."],
    ["Verdaderos negativos (VN)", thousands(LR["tn"]),
     "Personas que ganan ≤50K y el modelo acertó. Es la celda más grande porque es la clase más común."],
    ["Falsos negativos (FN)", thousands(LR["fn"]),
     "Personas que ganan &gt;50K, pero el modelo dijo ≤50K. Se les <i>subestima</i> y podrían perder "
     "oportunidades. Explican el recall de 0.62 y, como se ve más adelante, afectan más a mujeres y a personas "
     "negras."],
], [4.2 * cm, 1.8 * cm, 10 * cm])
P(f"El modelo comete más falsos negativos ({LR['fn']}) que falsos positivos ({LR['fp']}). Es decir, es "
  "<b>conservador</b>: le cuesta decir que alguien gana más de 50K. Es lo esperable con clases desbalanceadas "
  f"y un corte de 0.5. En comparación, el baseline tiene 0 verdaderos positivos y {thousands(BL['fn'])} falsos "
  "negativos: no encuentra a nadie de la clase positiva.")

# ============================================================== ethics
P("Análisis Ético", "h1")
P("Un modelo puede tener buenas métricas y aun así ser injusto. Por eso revisé de dónde vienen los sesgos, a "
  "quién afectan los errores y qué condiciones harían falta para usar el modelo de forma responsable "
  "(Barocas et al., 2023).")
P("Sesgos del Conjunto de Datos", "h2")
bullets([
    "<b>Sesgo histórico.</b> El censo de 1994 refleja las desigualdades de esa época. El 30.4 % de los hombres "
    "gana más de 50K, frente al 10.9 % de las mujeres. Las personas blancas y asiáticas superan en más del doble "
    "a las personas negras e indígenas. El modelo aprende esas brechas como si fueran algo normal.",
    "<b>Sesgo de representación.</b> El 85.5 % de los registros son de personas blancas y el 66.8 % de hombres. "
    "Grupos como Amer-Indian-Eskimo (cerca de 470 registros) u Other (cerca de 400) tienen tan pocos datos que sus "
    "métricas no son confiables.",
    "<b>Sesgo de medición.</b> Las categorías de raza y sexo son cerradas, y el límite de 50K está en dólares de "
    "1994, sin ajustar por costo de vida ni por región.",
    "<b>Sesgo temporal y geográfico.</b> Los datos no representan la economía de hoy ni la de Colombia. Usar el "
    "modelo fuera de ese contexto sería extrapolar sin fundamento.",
])
P("Sesgos del Modelo", "h2")
P(f"Los coeficientes muestran que el modelo usa el sexo de forma directa. La variable <b>sex_Female</b> tiene un "
  f"coeficiente de <b>{coef.get('cat__sex_Female', -0.967):.3f}</b>: si todo lo demás es igual, ser mujer baja la "
  "probabilidad estimada de ganar más de 50K. También pesan mucho el estado civil <b>Married-civ-spouse</b> "
  f"(+{coef.get('cat__marital_status_Married-civ-spouse', 1.406):.2f}) y la relación <b>Own-child</b> "
  f"({coef.get('cat__relationship_Own-child', -0.978):.2f}), que funcionan como variables <i>proxy</i> del sexo y "
  "de la etapa de vida. Además, algunos países con muy pocos registros, como Columbia "
  f"({coef.get('cat__native_country_Columbia', -1.054):.2f}), reciben coeficientes extremos. Esto muestra que el "
  "modelo es inestable con esos grupos y que puede discriminar por origen (Figura 5).")
figure("logreg_coefficients.png", 11, "Los 20 coeficientes de mayor magnitud de la regresión logística",
       note="Los valores están en log-odds. En verde los que aumentan la probabilidad de ganar más de 50K y en "
            "rojo los que la disminuyen.")
P("Equidad: Métricas por Grupo", "h2")
P("Para medir la equidad usé dos criterios. La <b>paridad demográfica</b> pregunta si el modelo dice «&gt;50K» con "
  "la misma frecuencia en cada grupo. La <b>igualdad de oportunidad</b> pregunta si el modelo encuentra por igual "
  "a quienes sí ganan más de 50K en cada grupo, es decir, si el recall es parecido (Hardt et al., 2016). La "
  "Tabla 8 muestra los resultados.")
rows = [["Grupo", "n (test)", "Tasa real &gt;50K", "Tasa predicha &gt;50K", "TPR (recall)", "FPR", "Accuracy"]]
for tbl in (FS, FR):
    for x in tbl["groups"]:
        rows.append([x["group"], str(x["n"]), f(x["base_rate"], 3), f(x["selection_rate"], 3), f(x["tpr"], 3),
                     f(x["fpr"], 3), f(x["accuracy"], 3)])
table("Métricas de la regresión logística por sexo y raza", rows,
      [3.6 * cm, 1.6 * cm, 2.3 * cm, 2.5 * cm, 2 * cm, 1.6 * cm, 1.8 * cm],
      note="Solo se incluyen grupos con al menos 100 registros en el conjunto de prueba. TPR = tasa de verdaderos "
           "positivos; FPR = tasa de falsos positivos.")
m_, w_ = g(FS, "Male"), g(FS, "Female")
b_, wh_ = g(FR, "Black"), g(FR, "White")
bullets([
    f"<b>Sexo.</b> El modelo encuentra al {pct(m_['tpr'])} de los hombres que ganan más de 50K, pero solo al "
    f"{pct(w_['tpr'])} de las mujeres en la misma situación (diferencia de "
    f"{FS['gaps']['equal_opportunity_diff']:.3f}). Una mujer que sí gana bien tiene más probabilidad de ser "
    "subestimada.",
    f"<b>Raza.</b> El recall de las personas negras ({pct(b_['tpr'])}) es mucho menor que el de las personas "
    f"blancas ({pct(wh_['tpr'])}). La diferencia máxima entre grupos es de "
    f"{FR['gaps']['equal_opportunity_diff']:.3f}.",
    f"<b>Impacto dispar.</b> La razón entre las tasas de selección de mujeres y hombres es "
    f"{FS['gaps']['disparate_impact_ratio']:.2f}, muy por debajo de la regla de los cuatro quintos (0.80), que se "
    "usa como referencia en contextos laborales de Estados Unidos.",
    f"<b>La accuracy puede engañar.</b> La accuracy es <i>mayor</i> en mujeres ({pct(w_['accuracy'])}) que en "
    "hombres, porque la mayoría de ellas está en la clase ≤50K. Por eso no basta con mirar la accuracy por "
    "grupo; hay que revisar el recall.",
    f"<b>Quitar las variables sensibles no basta.</b> Sin sex, race y native_country, la paridad por sexo apenas "
    f"pasa de {FS['gaps']['demographic_parity_diff']:.3f} a {FSU['gaps']['demographic_parity_diff']:.3f} y la "
    f"igualdad de oportunidad de {FS['gaps']['equal_opportunity_diff']:.3f} a "
    f"{FSU['gaps']['equal_opportunity_diff']:.3f}. Las variables relationship (Husband/Wife) y marital_status "
    "siguen revelando el sexo.",
])
P("Privacidad y Uso Responsable de los Datos", "h2")
bullets([
    "El conjunto de datos es público, no tiene nombres ni identificadores y su licencia (CC BY 4.0) permite usarlo "
    "citando la fuente, como se hace en este informe.",
    "Aun así, contiene <b>datos sensibles</b>: raza, sexo, origen y estado civil. En Colombia, la Ley 1581 de "
    "2012 exige autorización previa, una finalidad clara y protección reforzada para este tipo de datos "
    "(Congreso de la República de Colombia, 2012). Un sistema real no podría usarlos sin cumplir esos "
    "requisitos.",
    "Existe riesgo de <b>reidentificación</b>: al combinar edad, ocupación, país y horas de trabajo se podría "
    "identificar a una persona dentro de un grupo pequeño. Por eso el modelo no se publica como servicio ni se "
    "cruza con otras fuentes.",
    "Se aplicó el principio de <b>minimización</b>: se descartó fnlwgt y se recomienda no recolectar datos que "
    "el caso de uso no necesite.",
])
P("Impacto Social", "h2")
P("Si un modelo así se usara para aprobar créditos, cupos, empleos o subsidios, sus falsos negativos caerían "
  "sobre todo en mujeres y personas negras. Se les negarían oportunidades a personas que sí cumplen el criterio, "
  "y eso reforzaría la misma desigualdad que originó los datos, en un círculo vicioso. En el otro sentido, los "
  "falsos positivos podrían llevar a otras personas a endeudarse más de lo que pueden pagar. Que el algoritmo "
  "sea neutral en lo matemático no hace que su impacto sea neutral.")
P("Justicia y Transparencia en la Toma de Decisiones", "h2")
bullets([
    "<b>Transparencia.</b> Con la regresión logística se puede explicar cada predicción, porque se ve cuánto "
    "aporta cada variable. Además, el repositorio publica los datos, el código, las métricas por grupo y las "
    "decisiones técnicas, para que cualquiera pueda auditarlos.",
    "<b>Justicia.</b> No hay una sola definición de equidad. Cuando las tasas reales de los grupos son distintas "
    "(30 % frente a 11 %), no se puede cumplir a la vez la paridad demográfica y la igualdad de oportunidad. "
    "Elegir cuál priorizar es una decisión ética que deben tomar las personas afectadas y los responsables del "
    "sistema, no solo el equipo técnico.",
    "<b>Supervisión humana.</b> El modelo debería apoyar la decisión, no tomarla solo. Las personas afectadas "
    "deberían poder conocer la razón de la decisión y apelarla.",
    "<b>Rendición de cuentas.</b> Se recomienda acompañar el modelo con una <i>model card</i> que diga para qué "
    "sirve, cuáles son sus límites y cómo rinde en cada grupo (Mitchell et al., 2019).",
])

# ============================================================== conclusions
P("Conclusiones Técnicas", "h1")
bullets([
    f"<b>Técnicamente, el modelo funciona bien.</b> Obtuvo un F1 de {f(LR['f1'])}, un ROC-AUC de "
    f"{f(LR['roc_auc'])} y una accuracy de {f(LR['accuracy'])}. Supera con claridad al baseline (F1 de 0 y AUC de "
    "0.5) y cumple los <b>cinco criterios de aceptación</b> definidos.",
    f"<b>No hay sobreajuste.</b> El F1 en entrenamiento ({f(M['logreg']['train']['f1'])}) y en prueba "
    f"({f(LR['f1'])}) es casi el mismo, y varía poco entre particiones (± {f(CV['f1']['std'])}).",
    f"<b>Los resultados son confiables.</b> Ningún registro está a la vez en entrenamiento y prueba. Además, el "
    f"modelo rinde mejor con perfiles que nunca vio ({f(lc['f1_unseen_profiles'], 3)}) que con perfiles repetidos "
    f"({f(lc['f1_seen_profiles'], 3)}), así que su resultado no depende de haber memorizado casos.",
    f"<b>Su punto débil es el recall</b> ({f(LR['recall'])}): no detecta al 38 % de las personas que ganan más de "
    "50K, y ese error no se reparte igual entre los grupos.",
    "La regresión logística y el árbol de decisión rinden prácticamente igual; preferí la regresión logística "
    "porque se puede explicar.",
    "<b>Éticamente, el modelo no está listo para decisiones reales.</b> Reproduce las brechas de sexo y raza, y "
    "quitar las variables sensibles no las elimina.",
])

# ============================================================== recommendations
P("Recomendaciones para Mejorar", "h1")
P("La Tabla 9 resume las mejoras que propongo, agrupadas por tema.")
table("Recomendaciones de mejora del modelo y del proyecto", [
    ["Ámbito", "Recomendación"],
    ["Desempeño", "Ajustar el umbral (0.35 sube el F1 a 0.695); probar class_weight='balanced'; crear interacciones "
                  "(edad × horas, educación × ocupación) o probar modelos no lineales (Random Forest, Gradient "
                  "Boosting) comparándolos contra este modelo como referencia."],
    ["Datos", "Usar datos recientes y locales (p. ej., la GEIH del DANE para Colombia); agrupar países por región; "
              "conseguir más ejemplos de los grupos subrepresentados."],
    ["Equidad", "Aplicar mitigación con Fairlearn: reponderación en el preprocesamiento, ExponentiatedGradient con "
                "restricción de igualdad de oportunidad en el entrenamiento, o umbrales por grupo en el "
                "postprocesamiento. Reportar siempre las métricas por grupo junto a las globales."],
    ["Transparencia", "Publicar una model card; agregar explicaciones locales (SHAP) por predicción; documentar el "
                      "uso previsto y las prohibiciones de uso."],
    ["Validación", "Validación cruzada repetida o anidada; intervalos de confianza por bootstrap; calibración de "
                   "probabilidades (curva de confiabilidad)."],
    ["Ingeniería", "Integración continua (GitHub Actions) que ejecute pipeline + pytest en cada PR hacia develop; "
                   "monitoreo de deriva si algún día se despliega."],
], [3 * cm, 13 * cm], note="La integración continua ya quedó implementada en el repositorio.")

# ============================================================== references (APA 7, new page, hanging indent)
story.append(PageBreak())
P("Referencias", "h1")
for ref in [
    "Barocas, S., Hardt, M., &amp; Narayanan, A. (2023). <i>Fairness and machine learning: Limitations and "
    "opportunities</i>. MIT Press. https://fairmlbook.org",
    "Becker, B., &amp; Kohavi, R. (1996). <i>Adult</i> [Conjunto de datos]. UCI Machine Learning Repository. "
    "https://doi.org/10.24432/C5XW20",
    "Brown, S. (s.f.). <i>The C4 model for visualising software architecture</i>. Recuperado el 6 de noviembre "
    "de 2026, de https://c4model.com",
    "Congreso de la República de Colombia. (2012, 17 de octubre). <i>Ley Estatutaria 1581 de 2012: Por la cual se "
    "dictan disposiciones generales para la protección de datos personales</i>.",
    "Hardt, M., Price, E., &amp; Srebro, N. (2016). Equality of opportunity in supervised learning. <i>Advances "
    "in Neural Information Processing Systems, 29</i>.",
    "Mitchell, M., Wu, S., Zaldivar, A., Barnes, P., Vasserman, L., Hutchinson, B., Spitzer, E., Raji, I. D., "
    "&amp; Gebru, T. (2019). Model cards for model reporting. En <i>Proceedings of the Conference on Fairness, "
    "Accountability, and Transparency</i> (pp. 220–229). Association for Computing Machinery. "
    "https://doi.org/10.1145/3287560.3287596",
    "Nieto Rodríguez, S. (2026). <i>proyectoFinal_predictorIngresos</i> [Repositorio de código fuente]. GitHub. "
    f"<a href='{REPO_URL}'>{REPO_URL}</a>",
    "Nygard, M. (2011, 15 de noviembre). <i>Documenting architecture decisions</i>. Cognitect. "
    "https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions",
    "Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., Blondel, M., Prettenhofer, "
    "P., Weiss, R., Dubourg, V., Vanderplas, J., Passos, A., Cournapeau, D., Brucher, M., Perrot, M., &amp; "
    "Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. <i>Journal of Machine Learning Research, "
    "12</i>, 2825–2830.",
]:
    story.append(Paragraph(ref, S["ref"]))


def page_number(canvas, doc):
    """APA 7: page number in the top right corner of every page, title page included."""
    canvas.saveState()
    canvas.setFont(FONT, 12)
    canvas.drawRightString(letter[0] - inch, letter[1] - 0.5 * inch, str(doc.page))
    canvas.restoreState()


doc = SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=inch, rightMargin=inch,
                        topMargin=inch, bottomMargin=inch,
                        title=TITLE, author="Santiago Nieto Rodríguez",
                        subject="Teoría de la Computación II - Actividad 6")
doc.build(story, onFirstPage=page_number, onLaterPages=page_number)
print("Written", OUT, "font:", FONT)
