"""Builds docs/Informe_Actividad6.pdf from reports/metrics.json and figures.

Usage (after `python -m src.pipeline`):
    python docs/build_report.py
"""
import json
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (CondPageBreak, Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
                                Spacer, Table, TableStyle)

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"
R = json.loads((ROOT / "reports" / "metrics.json").read_text(encoding="utf-8"))
OUT = ROOT / "docs" / "Informe_Actividad6.pdf"

FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
if (FONT_DIR / "DejaVuSans.ttf").exists():
    pdfmetrics.registerFont(TTFont("Body", str(FONT_DIR / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("Body-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
    pdfmetrics.registerFont(TTFont("Body-Italic", str(FONT_DIR / "DejaVuSans-Oblique.ttf")))
    pdfmetrics.registerFontFamily("Body", normal="Body", bold="Body-Bold", italic="Body-Italic")
    BODY, BOLD = "Body", "Body-Bold"
else:  # fallback
    BODY, BOLD = "Helvetica", "Helvetica-Bold"

NAVY = colors.HexColor("#0b3d6b")
LIGHT = colors.HexColor("#e8eef5")
ss = getSampleStyleSheet()
S = {
    "title": ParagraphStyle("t", parent=ss["Title"], fontName=BOLD, fontSize=20, leading=25, textColor=NAVY),
    "sub": ParagraphStyle("s", parent=ss["Normal"], fontName=BODY, fontSize=11, leading=15, alignment=TA_CENTER),
    "h1": ParagraphStyle("h1", parent=ss["Heading1"], fontName=BOLD, fontSize=14, leading=18, textColor=NAVY,
                         spaceBefore=10, spaceAfter=6, keepWithNext=1),
    "h2": ParagraphStyle("h2", parent=ss["Heading2"], fontName=BOLD, fontSize=11.5, leading=15, textColor=NAVY,
                         spaceBefore=8, spaceAfter=4, keepWithNext=1),
    "p": ParagraphStyle("p", parent=ss["Normal"], fontName=BODY, fontSize=9.5, leading=13.5, alignment=TA_JUSTIFY,
                        spaceAfter=5),
    "b": ParagraphStyle("b", parent=ss["Normal"], fontName=BODY, fontSize=9.5, leading=13, leftIndent=12,
                        bulletIndent=2, spaceAfter=2, alignment=TA_JUSTIFY),
    "cell": ParagraphStyle("c", parent=ss["Normal"], fontName=BODY, fontSize=8.3, leading=10.5),
    "cellb": ParagraphStyle("cb", parent=ss["Normal"], fontName=BOLD, fontSize=8.3, leading=10.5,
                            textColor=colors.white),
    "cap": ParagraphStyle("cap", parent=ss["Normal"], fontName=BODY, fontSize=8, leading=10,
                          alignment=TA_CENTER, textColor=colors.HexColor("#555555"), spaceAfter=8),
}

story = []
def P(t, st="p"):
    if st in ("h1", "h2"):
        story.append(CondPageBreak((6 if st == "h1" else 4) * cm))
    story.append(Paragraph(t, S[st]))


def bullets(items):
    for it in items:
        story.append(Paragraph(it, S["b"], bulletText="•"))


def table(rows, widths, header=True, zebra=True):
    data = [[Paragraph(str(c), S["cellb"] if header and i == 0 else S["cell"]) for c in r]
            for i, r in enumerate(rows)]
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    style = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9aa9b8")),
             ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
             ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        style.append(("BACKGROUND", (0, 0), (-1, 0), NAVY))
    if zebra:
        for i in range(1, len(rows)):
            if i % 2 == 0:
                style.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    t.setStyle(TableStyle(style))
    story.append(t)
    story.append(Spacer(1, 6))


def fig(name, width_cm, caption):
    img = Image(str(FIG / name) if not name.startswith("/") else name)
    ratio = img.imageHeight / img.imageWidth
    img.drawWidth, img.drawHeight = width_cm * cm, width_cm * cm * ratio
    story.append(KeepTogether([img, Paragraph(caption, S["cap"])]))


f = lambda x, n=4: f"{x:.{n}f}"
pct = lambda x: f"{100 * x:.1f} %"
M = R["models"]
LR, BL, DT, UN = M["logreg"]["test"], M["baseline"]["test"], M["decision_tree"]["test"], M["logreg_unaware"]["test"]
CV = M["logreg"]["cv"]
FS, FR = R["fairness"]["logreg"]["sex"], R["fairness"]["logreg"]["race"]
FSU = R["fairness"]["logreg_unaware"]["sex"]
prof, split = R["data_profile"], R["split"]
g = lambda tbl, name: next(x for x in tbl["groups"] if x["group"] == name)

# ---------------------------------------------------------------- cover
story += [Spacer(1, 3.2 * cm)]
P("Actividad 6 · Mini-proyecto", "sub")
story.append(Spacer(1, 6))
P("Predictor de Ingresos: evaluación y análisis ético de un modelo de Regresión Logística", "title")
story.append(Spacer(1, 14))
P("Teoría de la Computación II · Ingeniería de Software<br/>Universidad de La Salle", "sub")
story.append(Spacer(1, 1.6 * cm))
P("<b>Autor:</b> Santiago Nieto Rodríguez (snieto21@unisalle.edu.co)<br/>"
  "<b>Docente:</b> Rodrigo Aranda Fernández<br/>"
  "<b>Repositorio:</b> github.com/santnier92/proyectoFinal_predictorIngresos<br/>"
  "<b>Rama individual:</b> dev_snieto21 → <b>integración:</b> develop<br/>"
  "<b>Fecha:</b> noviembre de 2026", "sub")
story.append(Spacer(1, 2 * cm))
table([
    ["Indicador clave (conjunto de prueba)", "Valor"],
    ["Accuracy / baseline", f"{f(LR['accuracy'])} / {f(BL['accuracy'])}"],
    ["F1-score clase >50K", f(LR["f1"])],
    ["ROC-AUC", f(LR["roc_auc"])],
    ["Criterios de aceptación cumplidos", "5 de 5"],
    ["Brecha de recall (TPR) hombres vs mujeres", f(FS["gaps"]["equal_opportunity_diff"], 3)],
], [9 * cm, 5 * cm])
story.append(PageBreak())

# ---------------------------------------------------------------- 1
P("1. Introducción y objetivo", "h1")
P("Este mini-proyecto aplica un modelo básico de Machine Learning sobre un dataset público conocido, evalúa su "
  "desempeño con métricas cuantitativas y analiza desde una perspectiva ética sus sesgos, su impacto y sus límites. "
  "La tarea es una <b>clasificación binaria</b>: estimar si el ingreso anual de una persona supera <b>50.000 USD</b> "
  "(<i>&gt;50K</i>, clase positiva = 1) a partir de sus atributos demográficos y laborales registrados en el censo de "
  "EE. UU. de 1994.")
P("El sistema se construyó como un pipeline reproducible (<font face='Courier'>python -m src.pipeline</font>) que "
  "recorre las siete etapas del workflow de ML vistas en clase: definir la tarea, recolectar los datos, representar la "
  "entrada, elegir el modelo, entrenar, evaluar y usar el modelo con datos nuevos. La arquitectura, los ADR, los riesgos "
  "y el glosario están en el README del repositorio; este documento desarrolla el análisis de la actividad.")

# ---------------------------------------------------------------- 2
P("2. Selección del modelo", "h1")
P("Se eligió la <b>Regresión Logística</b>. Este modelo estima la probabilidad de la clase positiva aplicando la "
  "función sigmoide a una combinación lineal de las variables: <i>P(y=1|x) = 1 / (1 + e<super>−(β₀ + β·x)</super>)</i>. "
  "Las razones de la elección fueron:")
bullets([
    "<b>Es adecuado para el problema:</b> la variable objetivo es binaria y los datos son tabulares.",
    "<b>Es interpretable:</b> cada coeficiente indica cuánto aumenta o disminuye el log-odds de ganar &gt;50K. Esto es "
    "indispensable para el análisis ético, porque permite ver <i>qué</i> variables empujan la decisión.",
    "<b>Entrega probabilidades:</b> así se puede mover el umbral de decisión según el costo de cada tipo de error.",
    f"<b>Su desempeño es equivalente al de un Árbol de Decisión:</b> el árbol obtuvo F1 = {f(DT['f1'])} frente a "
    f"{f(LR['f1'])}. La diferencia ({DT['f1'] - LR['f1']:.3f}) es menor que la desviación estándar de la validación "
    f"cruzada ({CV['f1']['std']:.3f}), así que no es significativa (ver ADR-002).",
    "Se descartó <b>KNN</b> porque, con 84 variables dispersas tras el one-hot, las distancias pierden sentido, "
    "predecir es costoso y el modelo no da una explicación global.",
])
P(f"Hiperparámetro elegido por validación cruzada de 5 folds: <b>C = {M['logreg']['best_params'].get('model__C')}</b> "
  "(inverso de la regularización L2).")

# ---------------------------------------------------------------- 3
P("3. Descripción del dataset", "h1")
P(f"Se usó el dataset <b>Adult / Census Income</b> (Becker &amp; Kohavi, 1996), del UCI Machine Learning Repository, "
  f"con licencia CC BY 4.0. Tiene <b>{prof['rows']:,} registros y {prof['columns']} columnas</b>. La clase positiva "
  f"(&gt;50K) representa el <b>{pct(prof['positive_rate'])}</b>, así que los datos están <b>desbalanceados</b>. Hay "
  f"{prof['duplicates']} duplicados y valores faltantes (codificados como '?') en workclass "
  f"({prof['missing_by_column']['workclass']:,}), occupation ({prof['missing_by_column']['occupation']:,}) y "
  f"native_country ({prof['missing_by_column']['native_country']:,}).".replace(",", "."))
P("3.1 Variables", "h2")
table([
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
], [3.6 * cm, 2.2 * cm, 4.6 * cm, 5.6 * cm])
P("3.2 Muestra de registros", "h2")
table([
    ["age", "workclass", "education_num", "occupation", "sex", "race", "hours", "income"],
    ["39", "State-gov", "13", "Adm-clerical", "Male", "White", "40", "&lt;=50K"],
    ["50", "Self-emp-not-inc", "13", "Exec-managerial", "Male", "White", "13", "&lt;=50K"],
    ["38", "Private", "9", "Handlers-cleaners", "Male", "White", "40", "&lt;=50K"],
    ["31", "Private", "14", "Prof-specialty", "Female", "White", "50", "&gt;50K"],
    ["42", "Private", "13", "Exec-managerial", "Male", "White", "40", "&gt;50K"],
], [1.2 * cm, 2.8 * cm, 2.1 * cm, 3.0 * cm, 1.5 * cm, 1.4 * cm, 1.3 * cm, 1.6 * cm])
fig("eda_target_and_groups.png", 16.5,
    "Figura 1. Distribución de la variable objetivo y proporción de &gt;50K por sexo y por raza (datos originales).")
P("<b>Objetivo del modelo:</b> aprender la relación entre las 12 variables de entrada y la variable <i>income</i>, "
  "para estimar la probabilidad de que una persona nueva gane más de 50K USD al año.")

# ---------------------------------------------------------------- 4
P("4. Metodología (workflow de ML)", "h1")
table([
    ["Etapa", "Qué se hizo"],
    ["1. Definir la tarea", "Clasificación binaria &gt;50K vs &lt;=50K; métrica principal: F1 de la clase positiva."],
    ["2. Recolectar datos", "Carga del CSV de UCI con verificación SHA-256 y perfil del dataset."],
    ["3. Representar la entrada",
     f"Deduplicación antes de partir los datos ({split['rows_after_dedup']:,} filas); partición estratificada 80/20 "
     f"(train {split['train_rows']:,} / test {split['test_rows']:,}); imputación (mediana / 'Unknown'), "
     "escalado estándar y one-hot (84 variables) dentro de un Pipeline.".replace(",", ".")],
    ["4. Elegir el modelo", "Baseline (clase mayoritaria), Regresión Logística, Árbol de Decisión y Regresión "
                            "Logística sin atributos sensibles."],
    ["5. Entrenar", "GridSearchCV con 5 folds estratificados, optimizando F1, solo sobre train."],
    ["6. Evaluar", "Métricas en test, matriz de confusión, curva ROC, análisis de umbral, coeficientes, "
                   "auditoría de equidad y criterios de aceptación."],
    ["7. Usar con datos nuevos", "CLI src.predict: recibe un CSV y devuelve la probabilidad y la clase."],
], [4 * cm, 12 * cm])

# ---------------------------------------------------------------- 5
P("5. Métricas de evaluación", "h1")
P("Todas las métricas se calcularon sobre el <b>conjunto de prueba</b> (9.758 registros), que no se usó ni en el "
  "entrenamiento ni en la selección de hiperparámetros.")
rows = [["Modelo", "Accuracy", "Precision", "Recall", "F1", "ROC-AUC"]]
for name, lab in [("baseline", "Baseline (clase mayoritaria)"), ("logreg", "<b>Regresión Logística</b>"),
                  ("decision_tree", "Árbol de Decisión"), ("logreg_unaware", "Reg. Logística sin atributos sensibles")]:
    t = M[name]["test"]
    rows.append([lab] + [f(t[k]) for k in ("accuracy", "precision", "recall", "f1", "roc_auc")])
table(rows, [5.6 * cm, 2.1 * cm, 2.1 * cm, 2.1 * cm, 2.1 * cm, 2.1 * cm])
P("5.1 Interpretación de cada métrica (Regresión Logística)", "h2")
table([
    ["Métrica", "Valor", "Qué significa en este problema"],
    ["Accuracy", f(LR["accuracy"]),
     f"Acierta en el {pct(LR['accuracy'])} de las personas. <b>Ojo:</b> el baseline, que siempre responde "
     f"&lt;=50K, ya obtiene {pct(BL['accuracy'])} sin aprender nada. La ganancia real es de "
     f"+{100 * (LR['accuracy'] - BL['accuracy']):.1f} puntos. Con clases desbalanceadas, la accuracy sola engaña."],
    ["Precision", f(LR["precision"]),
     f"De cada 100 personas que el modelo clasifica como &gt;50K, unas {round(100 * LR['precision'])} realmente lo son. "
     "Mide qué tan confiable es una predicción positiva."],
    ["Recall", f(LR["recall"]),
     f"Detecta el {pct(LR['recall'])} de quienes realmente ganan &gt;50K; se le escapa el {pct(1 - LR['recall'])}. "
     "Mide la cobertura de la clase positiva."],
    ["F1-score", f(LR["f1"]),
     "Media armónica entre precision y recall. Es la métrica principal porque castiga tanto los falsos positivos "
     "como los falsos negativos. El baseline obtiene 0."],
    ["ROC-AUC", f(LR["roc_auc"]),
     f"Si se toman al azar una persona con &gt;50K y otra con &lt;=50K, el modelo le asigna mayor probabilidad a la "
     f"primera en el {pct(LR['roc_auc'])} de los casos. No depende del umbral."],
    ["CV F1 (5 folds)", f"{f(CV['f1']['mean'])} ± {f(CV['f1']['std'])}",
     "Desempeño estable entre particiones distintas del entrenamiento: el resultado no depende de la suerte "
     "de la partición."],
], [2.6 * cm, 2.4 * cm, 11 * cm])
fig("roc_curve.png", 9.5, "Figura 2. Curvas ROC en el conjunto de prueba. El baseline coincide con la diagonal (AUC 0.5).")
ta = R["threshold_analysis"]
P(f"<b>Umbral de decisión.</b> Con el umbral por defecto (0.5) el modelo prioriza la precisión. Si se baja a "
  f"<b>{ta['best_threshold_for_f1']:.2f}</b>, el F1 sube a <b>{ta['best_f1']:.3f}</b>, porque el modelo gana recall a "
  "cambio de algo de precisión. La elección del umbral es una decisión de negocio y de ética: depende de qué error "
  "resulta más costoso en el contexto de uso.")
fig("threshold_tradeoff.png", 9.5, "Figura 3. Precision, recall y F1 según el umbral de decisión.")

# ---------------------------------------------------------------- 6
P("6. Matriz de confusión", "h1")
fig("confusion_matrix_logreg.png", 8.5, "Figura 4. Matriz de confusión de la Regresión Logística (test, umbral 0.5).")
table([
    ["Celda", "Valor", "Significado en este problema"],
    ["Verdaderos positivos (VP)", f"{LR['tp']:,}".replace(",", "."),
     "Personas que ganan &gt;50K y el modelo las identificó correctamente."],
    ["Falsos positivos (FP)", f"{LR['fp']:,}".replace(",", "."),
     "Personas que ganan &lt;=50K, pero el modelo dijo &gt;50K. En un uso real (p. ej., crédito) podría "
     "concederse un producto que la persona no puede pagar: es el error de <i>sobreestimar</i>."],
    ["Verdaderos negativos (VN)", f"{LR['tn']:,}".replace(",", "."),
     "Personas que ganan &lt;=50K y el modelo lo clasificó correctamente. Es la celda más grande porque es la clase "
     "mayoritaria."],
    ["Falsos negativos (FN)", f"{LR['fn']:,}".replace(",", "."),
     "Personas que ganan &gt;50K, pero el modelo dijo &lt;=50K. Se les <i>subestima</i> y podrían perder "
     "oportunidades. Son la causa del recall de 0.62 y, como se verá en la sección 7, afectan más a mujeres y "
     "personas negras."],
], [4.2 * cm, 1.8 * cm, 10 * cm])
P(f"El modelo comete más falsos negativos ({LR['fn']}) que falsos positivos ({LR['fp']}): es <b>conservador</b> al "
  "asignar la clase &gt;50K. Esto es esperable con datos desbalanceados y umbral 0.5. En comparación, el baseline "
  f"tiene 0 VP y {BL['fn']:,} FN: no detecta a ninguna persona de la clase positiva.".replace(",", "."))

# ---------------------------------------------------------------- 7
story.append(PageBreak())
P("7. Análisis ético", "h1")
P("7.1 Sesgos del dataset", "h2")
bullets([
    "<b>Sesgo histórico:</b> el censo de 1994 refleja desigualdades estructurales de su época. El 30.4 % de los "
    "hombres gana &gt;50K frente al 10.9 % de las mujeres, y las personas blancas y asiáticas superan en más del "
    "doble a las personas negras e indígenas. Un modelo entrenado con estos datos aprende esas brechas como si fueran "
    "patrones \"naturales\".",
    "<b>Sesgo de representación:</b> el 85.5 % de los registros corresponde a personas blancas y el 66.8 % a hombres. "
    "Grupos como Amer-Indian-Eskimo (~470 registros) u Other (~400) tienen tan pocos datos que sus métricas no son "
    "confiables.",
    "<b>Sesgo de medición:</b> las categorías de raza y sexo son binarias o cerradas, el umbral de 50K está fijo en "
    "dólares de 1994 y no se ajusta por costo de vida ni por región.",
    "<b>Sesgo temporal y geográfico:</b> los datos no representan la economía actual ni a Colombia; aplicar el modelo "
    "fuera de ese contexto sería una extrapolación inválida.",
])
P("7.2 Sesgos del modelo", "h2")
pos, neg = R["top_coefficients"]["positive"], R["top_coefficients"]["negative"]
P(f"Los coeficientes muestran que el modelo usa directamente el sexo: <b>sex_Female</b> tiene un coeficiente de "
  f"<b>{neg.get('cat__sex_Female', -0.967):.3f}</b> (log-odds), es decir, a igualdad de las demás variables, ser mujer "
  "reduce la probabilidad estimada de ganar &gt;50K. También pesan mucho <b>marital_status = Married-civ-spouse</b> "
  f"(+{pos.get('cat__marital_status_Married-civ-spouse', 1.406):.2f}) y <b>relationship = Own-child</b> "
  f"({neg.get('cat__relationship_Own-child', -0.978):.2f}), variables que funcionan como <b>proxy</b> del sexo y de la "
  "etapa de vida. Por último, algunos países poco frecuentes (por ejemplo, Columbia: "
  f"{neg.get('cat__native_country_Columbia', -1.054):.2f}) reciben coeficientes extremos con muy pocos ejemplos, lo que "
  "muestra inestabilidad y riesgo de discriminación por origen.")
fig("logreg_coefficients.png", 11, "Figura 5. Los 20 coeficientes de mayor magnitud de la Regresión Logística.")

P("7.3 Equidad: métricas por grupo", "h2")
P("Para la auditoría se usaron dos criterios: <b>paridad demográfica</b> (¿se predice &gt;50K con la misma frecuencia "
  "en cada grupo?) e <b>igualdad de oportunidad</b> (¿el modelo detecta por igual, con el mismo recall o TPR, a las "
  "personas de cada grupo que sí ganan &gt;50K?).")
rows = [["Grupo", "n (test)", "Tasa real &gt;50K", "Tasa predicha &gt;50K", "TPR (recall)", "FPR", "Accuracy"]]
for tbl in (FS, FR):
    for x in tbl["groups"]:
        rows.append([x["group"], str(x["n"]), f(x["base_rate"], 3), f(x["selection_rate"], 3), f(x["tpr"], 3),
                     f(x["fpr"], 3), f(x["accuracy"], 3)])
table(rows, [3.6 * cm, 1.6 * cm, 2.3 * cm, 2.5 * cm, 2 * cm, 1.6 * cm, 1.8 * cm])
m_, w_ = g(FS, "Male"), g(FS, "Female")
b_, wh_ = g(FR, "Black"), g(FR, "White")
bullets([
    f"<b>Sexo:</b> el modelo detecta al {pct(m_['tpr'])} de los hombres con &gt;50K, pero solo al {pct(w_['tpr'])} de "
    f"las mujeres con &gt;50K (diferencia de igualdad de oportunidad = "
    f"{FS['gaps']['equal_opportunity_diff']:.3f}). Una mujer que sí gana bien tiene más probabilidad de ser "
    "subestimada.",
    f"<b>Raza:</b> el TPR de las personas negras ({pct(b_['tpr'])}) es mucho menor que el de las personas blancas "
    f"({pct(wh_['tpr'])}); la diferencia máxima entre grupos es {FR['gaps']['equal_opportunity_diff']:.3f}.",
    f"<b>Impacto dispar:</b> la razón entre tasas de selección por sexo es {FS['gaps']['disparate_impact_ratio']:.2f}, "
    "muy por debajo de la regla de los cuatro quintos (0.80) que se usa como referencia en contextos laborales de "
    "EE. UU.",
    f"<b>Accuracy engañosa:</b> la accuracy es <i>mayor</i> en mujeres ({pct(w_['accuracy'])}) que en hombres, porque "
    "en ellas la mayoría pertenece a la clase &lt;=50K. Por eso no basta con mirar la accuracy por grupo: hay que "
    "revisar el recall.",
    f"<b>\"Equidad por ceguera\" no funciona:</b> al quitar sex, race y native_country, la paridad por sexo apenas "
    f"pasa de {FS['gaps']['demographic_parity_diff']:.3f} a {FSU['gaps']['demographic_parity_diff']:.3f} y la de "
    f"oportunidad de {FS['gaps']['equal_opportunity_diff']:.3f} a {FSU['gaps']['equal_opportunity_diff']:.3f}, "
    "porque relationship (Husband/Wife) y marital_status siguen codificando el sexo.",
])
P("7.4 Privacidad y uso responsable de los datos", "h2")
bullets([
    "El dataset es público, está anonimizado (no tiene nombres ni identificadores) y su licencia (CC BY 4.0) permite "
    "usarlo con atribución, que se da en las referencias.",
    "Aun así, contiene <b>datos sensibles</b> (raza, sexo, origen, estado civil). En Colombia, la Ley 1581 de 2012 "
    "exige autorización previa, finalidad explícita y medidas reforzadas para este tipo de datos; un sistema real "
    "no podría usarlos sin cumplir esos requisitos.",
    "Riesgo de <b>reidentificación</b>: combinando edad, ocupación, país y horas trabajadas se podría aislar a una "
    "persona en una población pequeña. Por eso el modelo no se expone como servicio ni se cruza con otras fuentes.",
    "<b>Minimización:</b> se descartó fnlwgt y se recomienda no recolectar atributos que el caso de uso no necesite.",
])
P("7.5 Impacto social", "h2")
P("Si un modelo así se usara para decidir créditos, cupos, contrataciones o subsidios, sus falsos negativos se "
  "concentrarían en mujeres y personas negras: se les negarían oportunidades a quienes sí cumplen el criterio, "
  "reforzando la desigualdad que originó los datos (<b>bucle de retroalimentación</b>). Al revés, los falsos "
  "positivos podrían llevar a sobreendeudamiento. El impacto no es neutro aunque el algoritmo lo sea "
  "matemáticamente.")
P("7.6 Justicia y transparencia en la toma de decisiones", "h2")
bullets([
    "<b>Transparencia:</b> la Regresión Logística permite explicar cada predicción (contribución de cada variable), "
    "y el repositorio publica datos, código, métricas por grupo y decisiones (ADR) para que terceros puedan "
    "auditarlo.",
    "<b>Justicia:</b> no existe una única definición de equidad. La paridad demográfica y la igualdad de oportunidad "
    "no pueden cumplirse a la vez cuando las tasas base difieren (30 % vs 11 %), así que elegir una es una decisión "
    "ética que deben tomar los interesados, no solo el equipo técnico.",
    "<b>Supervisión humana:</b> el modelo debe ser una herramienta de apoyo, no la decisión final. Las personas "
    "afectadas deberían poder conocer la razón de la decisión y apelarla.",
    "<b>Rendición de cuentas:</b> se recomienda acompañar el modelo de una <i>model card</i> que declare el uso "
    "previsto, los límites y las métricas por grupo.",
])

# ---------------------------------------------------------------- 8
P("8. Conclusiones técnicas", "h1")
lc = R["leakage_check"]
bullets([
    f"El modelo <b>funciona bien desde el punto de vista técnico</b>: F1 = {f(LR['f1'])}, ROC-AUC = "
    f"{f(LR['roc_auc'])} y accuracy = {f(LR['accuracy'])}. Supera ampliamente al baseline (F1 0 y AUC 0.5) y cumple "
    "los <b>5 de 5 criterios de aceptación</b> definidos.",
    f"<b>No hay sobreajuste:</b> el F1 de train ({f(M['logreg']['train']['f1'])}) y el de test ({f(LR['f1'])}) son "
    f"prácticamente iguales, y la variación entre folds es baja (± {f(CV['f1']['std'])}).",
    f"<b>Los resultados son válidos:</b> no hay registros compartidos entre train y test, y el F1 sobre perfiles nunca "
    f"vistos ({f(lc['f1_unseen_profiles'], 3)}) es incluso mayor que sobre perfiles repetidos "
    f"({f(lc['f1_seen_profiles'], 3)}).",
    f"Su <b>debilidad principal es el recall</b> ({f(LR['recall'])}): no detecta al 38 % de las personas con "
    "&gt;50K, y ese error se distribuye de forma desigual entre grupos.",
    "La Regresión Logística y el Árbol de Decisión rinden de forma equivalente; la logística se prefiere por su "
    "interpretabilidad.",
    "<b>Desde la ética, el modelo no es apto para decisiones reales:</b> reproduce brechas de sexo y raza, y quitar los "
    "atributos sensibles no las elimina.",
])

# ---------------------------------------------------------------- 9
P("9. Recomendaciones para mejorar", "h1")
table([
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
], [3 * cm, 13 * cm])

# ---------------------------------------------------------------- 10
P("10. Referencias", "h1")
for ref in [
    "Becker, B., &amp; Kohavi, R. (1996). <i>Adult</i> [Dataset]. UCI Machine Learning Repository. "
    "https://doi.org/10.24432/C5XW20",
    "Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. <i>JMLR</i>, 12, 2825–2830.",
    "Barocas, S., Hardt, M., &amp; Narayanan, A. (2023). <i>Fairness and Machine Learning</i>. MIT Press. "
    "https://fairmlbook.org",
    "Hardt, M., Price, E., &amp; Srebro, N. (2016). Equality of Opportunity in Supervised Learning. <i>NeurIPS</i>.",
    "Mitchell, M. et al. (2019). Model Cards for Model Reporting. <i>FAT* '19</i>.",
    "Brown, S. <i>The C4 model for visualising software architecture</i>. https://c4model.com",
    "Nygard, M. (2011). Documenting Architecture Decisions. Cognitect.",
    "Congreso de Colombia (2012). Ley Estatutaria 1581 de 2012 — Protección de datos personales.",
]:
    story.append(Paragraph(ref, S["b"], bulletText="•"))


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(BODY, 7.5)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(2 * cm, 1.2 * cm, "proyectoFinal_predictorIngresos · Teoría de la Computación II")
    canvas.drawRightString(letter[0] - 2 * cm, 1.2 * cm, f"Página {doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(str(OUT), pagesize=letter, leftMargin=2 * cm, rightMargin=2 * cm,
                        topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                        title="Informe Actividad 6 - Predictor de Ingresos", author="Santiago Nieto Rodríguez")
doc.build(story, onFirstPage=lambda c, d: None, onLaterPages=footer)
print("Written", OUT)
