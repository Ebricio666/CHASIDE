# ============================================
# APP CHASIDE · 3 pestañas laterales
# Presentación | Análisis general | Información individual
# ============================================

import io
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
st.set_page_config(page_title="Diagnóstico Vocacional - Escala CHASIDE", layout="wide")

# -------------------------------------------------
# CONSTANTES
# -------------------------------------------------
AREAS = ['C', 'H', 'A', 'S', 'I', 'D', 'E']

AREAS_LONG = {
    "C": "Administrativo",
    "H": "Humanidades y Sociales",
    "A": "Artístico",
    "S": "Ciencias de la Salud",
    "I": "Enseñanzas Técnicas",
    "D": "Defensa y Seguridad",
    "E": "Ciencias Experimentales"
}

INTERESES_ITEMS = {
    'C': [1, 12, 20, 53, 64, 71, 78, 85, 91, 98],
    'H': [9, 25, 34, 41, 56, 67, 74, 80, 89, 95],
    'A': [3, 11, 21, 28, 36, 45, 50, 57, 81, 96],
    'S': [8, 16, 23, 33, 44, 52, 62, 70, 87, 92],
    'I': [6, 19, 27, 38, 47, 54, 60, 75, 83, 97],
    'D': [5, 14, 24, 31, 37, 48, 58, 65, 73, 84],
    'E': [17, 32, 35, 42, 49, 61, 68, 77, 88, 93]
}

APTITUDES_ITEMS = {
    'C': [2, 15, 46, 51],
    'H': [30, 63, 72, 86],
    'A': [22, 39, 76, 82],
    'S': [4, 29, 40, 69],
    'I': [10, 26, 59, 90],
    'D': [13, 18, 43, 66],
    'E': [7, 55, 79, 94]
}

DEFAULT_PERFILES = {
    'Arquitectura': ['A', 'I', 'C'],
    'Contador Público': ['C', 'D'],
    'Licenciatura en Administración': ['C', 'D'],
    'Ingeniería Ambiental': ['I', 'C', 'E'],
    'Ingeniería Bioquímica': ['I', 'C', 'E'],
    'Ingeniería en Gestión Empresarial': ['C', 'D', 'H'],
    'Ingeniería Industrial': ['C', 'D', 'H'],
    'Ingeniería en Inteligencia Artificial': ['I', 'E'],
    'Ingeniería Mecatrónica': ['I', 'E'],
    'Ingeniería en Sistemas Computacionales': ['I', 'E']
}

ESTRATEGIAS_CHASIDE = {
    "C": {
        "area": "Administrativo",
        "estrategia": (
            "Fortalecer organización, planeación, seguimiento de instrucciones, "
            "gestión del tiempo y resolución estructurada de problemas."
        )
    },
    "H": {
        "area": "Humanidades y Sociales",
        "estrategia": (
            "Promover comunicación oral y escrita, argumentación, comprensión de textos, "
            "análisis de casos y trabajo colaborativo."
        )
    },
    "A": {
        "area": "Artístico",
        "estrategia": (
            "Incorporar ejercicios de creatividad, diseño, visualización de ideas, "
            "prototipos y solución innovadora de problemas."
        )
    },
    "S": {
        "area": "Ciencias de la Salud",
        "estrategia": (
            "Favorecer observación, precisión, estudio de casos, empatía profesional "
            "y actividades con orientación al servicio."
        )
    },
    "I": {
        "area": "Enseñanzas Técnicas",
        "estrategia": (
            "Reforzar pensamiento lógico, modelado, cálculo, uso de herramientas, "
            "prácticas guiadas y resolución técnica de problemas."
        )
    },
    "D": {
        "area": "Defensa y Seguridad",
        "estrategia": (
            "Impulsar liderazgo, disciplina, trabajo en equipo, responsabilidad "
            "y toma de decisiones en contextos estructurados."
        )
    },
    "E": {
        "area": "Ciencias Experimentales",
        "estrategia": (
            "Estimular observación sistemática, experimentación, interpretación de datos, "
            "método y pensamiento crítico."
        )
    }
}

DESC_INTENSIDAD = {
    "Sin perfil": "Estudiante cuya elección de carrera no muestra correspondencia con su perfil vocacional.",
    "Perfil en riesgo": "Estudiante cuyo perfil vocacional presenta una coincidencia mínima con la carrera elegida.",
    "Perfil en transición": "Estudiante cuya elección profesional y perfil vocacional presentan congruencia, aunque aún en proceso de consolidación.",
    "Jóven promesa": "Estudiante con alta congruencia entre su perfil vocacional y la carrera elegida."
}

CAT_MAP_LARGO = {
    'Verde': 'El perfil coincide con la carrera elegida',
    'Amarillo': 'El perfil NO va acorde con la carrera elegida',
    'Rojo': 'No se observa un perfil prioritario',
    'Sin sugerencia': 'No se observa un perfil prioritario',
    'Respondió siempre igual': 'Respondió siempre igual'
}

COLUMNA_EMAIL = 'Dirección de correo electrónico'

# -------------------------------------------------
# UTILIDADES
# -------------------------------------------------
def col_item(columnas_items, i: int) -> str:
    return columnas_items[i - 1]


def transformar_url_google_sheets(url: str) -> str:
    url = url.strip()

    if "export?format=csv" in url:
        return url

    if "docs.google.com/spreadsheets" in url:
        try:
            file_id = url.split("/d/")[1].split("/")[0]

            gid = "0"
            if "gid=" in url:
                gid = url.split("gid=")[-1].split("&")[0].split("#")[0]

            return f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&gid={gid}"
        except Exception:
            raise ValueError(
                "No se pudo transformar automáticamente el enlace de Google Sheets. "
                "Pega el vínculo en formato /edit o directamente en formato /export?format=csv."
            )

    return url


@st.cache_data(show_spinner=False)
def load_data(url: str) -> pd.DataFrame:
    final_url = transformar_url_google_sheets(url)
    return pd.read_csv(final_url)


def dataframe_a_excel_bytes(dic_hojas: dict) -> bytes:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for nombre_hoja, df_hoja in dic_hojas.items():
            nombre_limpio = str(nombre_hoja)[:31] if nombre_hoja else "Hoja"
            df_hoja.to_excel(writer, index=False, sheet_name=nombre_limpio)
    output.seek(0)
    return output.getvalue()


def process_data(df: pd.DataFrame, perfil_carreras: dict, peso_intereses: float, peso_aptitudes: float):
    df = df.copy()
    df.columns = df.columns.str.strip()

    columna_nombre = 'Ingrese su nombre completo'
    columna_carrera = '¿A qué carrera desea ingresar?'

    faltantes = [c for c in [columna_nombre, columna_carrera] if c not in df.columns]
    if faltantes:
        raise ValueError(
            f"Faltan columnas requeridas: {faltantes}. "
            f"Columnas detectadas: {list(df.columns)}"
        )

    columnas_items = df.columns[6:104]

    if len(columnas_items) != 98:
        raise ValueError(
            f"Se esperaban 98 reactivos CHASIDE, pero se detectaron {len(columnas_items)}. "
            f"Verifica el orden de columnas del archivo."
        )

    df_items = (
        df[columnas_items]
        .astype(str)
        .apply(lambda col: col.str.strip().str.lower())
        .replace({
            'sí': 1, 'si': 1, 's': 1, '1': 1, 'true': 1, 'verdadero': 1, 'x': 1,
            'no': 0, 'n': 0, '0': 0, 'false': 0, 'falso': 0, '': 0, 'nan': 0
        })
        .apply(pd.to_numeric, errors='coerce')
        .fillna(0)
        .astype(int)
    )
    df[columnas_items] = df_items

    df['Desv_Intrapersona'] = df[columnas_items].std(axis=1)
    umbral_intrapersonal = df['Desv_Intrapersona'].quantile(0.10)
    df['Respondio_Siempre_Igual'] = df['Desv_Intrapersona'] <= umbral_intrapersonal

    for a in AREAS:
        df[f'INTERES_{a}'] = df[[col_item(columnas_items, i) for i in INTERESES_ITEMS[a]]].sum(axis=1)
        df[f'APTITUD_{a}'] = df[[col_item(columnas_items, i) for i in APTITUDES_ITEMS[a]]].sum(axis=1)

    for a in AREAS:
        df[f'PUNTAJE_COMBINADO_{a}'] = (
            df[f'INTERES_{a}'] * peso_intereses +
            df[f'APTITUD_{a}'] * peso_aptitudes
        )
        df[f'TOTAL_{a}'] = df[f'INTERES_{a}'] + df[f'APTITUD_{a}']

    df['Area_Fuerte_Ponderada'] = df.apply(
        lambda r: max(AREAS, key=lambda a: r[f'PUNTAJE_COMBINADO_{a}']),
        axis=1
    )

    score_cols = [f'PUNTAJE_COMBINADO_{a}' for a in AREAS]
    df['Score'] = df[score_cols].max(axis=1)

    def evaluar(area_chaside, carrera):
        p = perfil_carreras.get(str(carrera).strip())
        if not p:
            return 'Sin perfil definido'
        if area_chaside in p:
            return 'Coherente'
        return 'Neutral'

    df['Coincidencia_Ponderada'] = df.apply(
        lambda r: evaluar(r['Area_Fuerte_Ponderada'], r[columna_carrera]),
        axis=1
    )

    def carrera_mejor(r):
        if r['Respondio_Siempre_Igual']:
            return 'Información no confiable'
        a = r['Area_Fuerte_Ponderada']
        c_actual = str(r[columna_carrera]).strip()
        sugeridas = [c for c, letras in perfil_carreras.items() if a in letras]
        return c_actual if c_actual in sugeridas else (
            ', '.join(sugeridas) if sugeridas else 'Sin sugerencia clara'
        )

    def diagnostico(r):
        if r['Carrera_Mejor_Perfilada'] == 'Información no confiable':
            return 'Información no confiable'
        if str(r[columna_carrera]).strip() == str(r['Carrera_Mejor_Perfilada']).strip():
            return 'Perfil adecuado'
        if r['Carrera_Mejor_Perfilada'] == 'Sin sugerencia clara':
            return 'Sin sugerencia clara'
        return f"Sugerencia: {r['Carrera_Mejor_Perfilada']}"

    def semaforo(r):
        diag = r['Diagnóstico Primario Vocacional']
        if diag == 'Información no confiable':
            return 'Respondió siempre igual'
        if diag == 'Sin sugerencia clara':
            return 'Sin sugerencia'
        if diag == 'Perfil adecuado' and r['Coincidencia_Ponderada'] == 'Coherente':
            return 'Verde'
        if diag == 'Perfil adecuado' and r['Coincidencia_Ponderada'] == 'Neutral':
            return 'Amarillo'
        if isinstance(diag, str) and diag.startswith('Sugerencia:') and r['Coincidencia_Ponderada'] == 'Coherente':
            return 'Verde'
        if isinstance(diag, str) and diag.startswith('Sugerencia:') and r['Coincidencia_Ponderada'] == 'Neutral':
            return 'Amarillo'
        return 'Rojo'

    df['Carrera_Mejor_Perfilada'] = df.apply(carrera_mejor, axis=1)
    df['Diagnóstico Primario Vocacional'] = df.apply(diagnostico, axis=1)
    df['Semáforo Vocacional'] = df.apply(semaforo, axis=1)

    df['Carrera_Corta'] = (
        df[columna_carrera]
        .astype(str)
        .str.replace('Ingeniería', 'Ing.', regex=False)
    )

    df_intensidad = df[df['Semáforo Vocacional'].isin(['Verde', 'Amarillo'])].copy()

    def asignar_niveles_por_carrera(grupo):
        grupo = grupo.copy()
        grupo['Nivel_Intensidad'] = pd.Series(index=grupo.index, dtype='object')

        amar = grupo[grupo['Semáforo Vocacional'] == 'Amarillo'].copy()
        ver = grupo[grupo['Semáforo Vocacional'] == 'Verde'].copy()

        if len(amar) > 0:
            amar = amar.sort_values('Score', ascending=True).copy()
            amar['rank_pct'] = (np.arange(len(amar)) + 1) / len(amar)
            amar['Nivel_Intensidad'] = np.where(
                amar['rank_pct'] <= 0.25,
                'Sin perfil',
                'Perfil en riesgo'
            )
            grupo.loc[amar.index, 'Nivel_Intensidad'] = amar['Nivel_Intensidad'].astype(object)

        if len(ver) > 0:
            ver = ver.sort_values('Score', ascending=True).copy()
            ver['rank_pct'] = (np.arange(len(ver)) + 1) / len(ver)
            ver['Nivel_Intensidad'] = np.where(
                ver['rank_pct'] > 0.75,
                'Jóven promesa',
                'Perfil en transición'
            )
            grupo.loc[ver.index, 'Nivel_Intensidad'] = ver['Nivel_Intensidad'].astype(object)

        return grupo

    if not df_intensidad.empty:
        df_intensidad = (
            df_intensidad
            .groupby(columna_carrera, group_keys=False)
            .apply(asignar_niveles_por_carrera)
            .copy()
        )

    def letras_carrera(carrera):
        return perfil_carreras.get(str(carrera).strip(), [])

    def puntaje_promedio_carrera(row, carrera):
        letras = letras_carrera(carrera)
        if not letras:
            return np.nan
        return np.mean([row[f'PUNTAJE_COMBINADO_{l}'] for l in letras])

    def mejor_destino_compatible(row):
        carrera = str(row[columna_carrera]).strip()
        letras = letras_carrera(carrera)

        mejor = carrera
        mejor_score = puntaje_promedio_carrera(row, carrera)

        for c, letras_c in perfil_carreras.items():
            if len(set(letras).intersection(letras_c)) >= 2:
                score = puntaje_promedio_carrera(row, c)
                if pd.notna(score) and score > mejor_score:
                    mejor_score = score
                    mejor = c

        return mejor

    df['Destino_Compatible'] = df.apply(mejor_destino_compatible, axis=1)

    return df, df_intensidad, columnas_items, columna_carrera, columna_nombre, umbral_intrapersonal


def build_pdf_report(estudiante, carrera, categoria, intensidad, texto_ubicacion, conclusion_txt):
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm
    )

    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='TitleBlue',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0F766E"),
        alignment=TA_LEFT,
        spaceAfter=10
    ))
    styles.add(ParagraphStyle(
        name='HeadingTeal',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0F766E"),
        spaceBefore=8,
        spaceAfter=6
    ))
    styles.add(ParagraphStyle(
        name='BodySmall',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        spaceAfter=6
    ))

    story = []
    story.append(Paragraph("Reporte individual CHASIDE", styles['TitleBlue']))
    story.append(Paragraph(f"<b>Estudiante:</b> {estudiante}", styles['BodySmall']))
    story.append(Paragraph(f"<b>Carrera:</b> {carrera}", styles['BodySmall']))
    story.append(Paragraph(f"<b>Perfil identificado:</b> {categoria}", styles['BodySmall']))
    story.append(Paragraph(f"<b>Intensidad vocacional:</b> {intensidad}", styles['BodySmall']))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Ubicación dentro del análisis general", styles['HeadingTeal']))
    for linea in texto_ubicacion.split("\n"):
        if linea.strip():
            story.append(Paragraph(linea.strip(), styles['BodySmall']))

    story.append(Paragraph("Conclusión y recomendación", styles['HeadingTeal']))
    story.append(Paragraph(conclusion_txt, styles['BodySmall']))

    doc.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def construir_conclusion_recomendacion(al, carrera_sel, destino_compatible, nivel_alumno):
    categoria = al['Semáforo Vocacional']
    respondio_igual = bool(al.get('Respondio_Siempre_Igual', False))

    if respondio_igual or categoria == 'Respondió siempre igual':
        return (
            "El patrón de respuestas sugiere baja variabilidad, por lo que el perfil obtenido debe interpretarse con cautela. "
            "Esto puede indicar que la prueba fue contestada con respuestas muy homogéneas o sin suficiente diferenciación entre intereses y aptitudes. "
            "Se recomienda reaplicar la prueba en condiciones controladas y posteriormente realizar una entrevista breve de orientación vocacional."
        )

    if nivel_alumno == 'Sin perfil':
        if destino_compatible != carrera_sel:
            return (
                f"El estudiante muestra baja correspondencia entre su perfil vocacional y la carrera elegida. "
                f"Además, el análisis compatible sugiere mayor afinidad hacia {destino_compatible}. "
                f"Se recomienda repetir la prueba y, si el resultado persiste, valorar orientación vocacional y posible transición."
            )
        return (
            f"El estudiante muestra baja correspondencia entre su perfil vocacional y la carrera elegida. "
            f"Se recomienda repetir la prueba y acompañar el proceso con orientación vocacional individual."
        )

    if nivel_alumno == 'Perfil en riesgo':
        if destino_compatible != carrera_sel:
            return (
                f"El estudiante presenta coincidencia mínima entre su perfil vocacional y la carrera elegida. "
                f"El análisis compatible sugiere mejor ajuste hacia {destino_compatible}. "
                f"Se recomienda seguimiento tutorial temprano y orientación vocacional."
            )
        return (
            f"El estudiante presenta coincidencia mínima entre su perfil vocacional y la carrera elegida. "
            f"Se recomienda seguimiento tutorial, fortalecimiento de hábitos de estudio y revisión vocacional complementaria."
        )

    if nivel_alumno == 'Perfil en transición':
        return (
            f"El estudiante muestra una congruencia vocacional funcional con la carrera elegida. "
            f"Se recomienda acompañamiento académico preventivo y seguimiento durante el primer semestre."
        )

    if nivel_alumno == 'Jóven promesa':
        return (
            f"El estudiante presenta alta congruencia entre su perfil vocacional y la carrera elegida. "
            f"Se recomienda fortalecer su trayectoria y promover actividades de alto desempeño."
        )

    if categoria == 'Verde':
        return "El perfil identificado coincide con la carrera elegida. Se recomienda mantener acompañamiento preventivo."

    if categoria == 'Amarillo':
        return "El perfil identificado no coincide plenamente con la carrera elegida. Se recomienda orientación vocacional y seguimiento tutorial."

    return "El resultado sugiere la necesidad de una interpretación complementaria mediante orientación y seguimiento académico."

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.title("CHASIDE · Navegación")

seccion = st.sidebar.radio(
    "Ir a",
    ["Presentación", "Análisis general", "Información individual"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Escala / fuente de datos")
url = st.sidebar.text_input(
    "URL de la escala (CSV export)",
    "https://docs.google.com/spreadsheets/d/1BNAeOSj2F378vcJE5-T8iJ8hvoseOleOHr-I7mVfYu4/export?format=csv"
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Ajustes del algoritmo")

preset = st.sidebar.selectbox(
    "Relación Intereses / Aptitudes",
    [
        "80 / 20 (predeterminado)",
        "70 / 30",
        "60 / 40",
        "50 / 50",
        "Personalizado"
    ],
    index=0
)

if preset == "80 / 20 (predeterminado)":
    peso_intereses = 0.8
    peso_aptitudes = 0.2
elif preset == "70 / 30":
    peso_intereses = 0.7
    peso_aptitudes = 0.3
elif preset == "60 / 40":
    peso_intereses = 0.6
    peso_aptitudes = 0.4
elif preset == "50 / 50":
    peso_intereses = 0.5
    peso_aptitudes = 0.5
else:
    wi = st.sidebar.slider("Peso de Intereses (%)", 0, 100, 80, 5)
    peso_intereses = wi / 100
    peso_aptitudes = 1 - peso_intereses

st.sidebar.caption(
    f"Pesos activos → Intereses: {peso_intereses:.2f} | Aptitudes: {peso_aptitudes:.2f}"
)

st.sidebar.markdown("### Perfil esperado por carrera")

if "usar_predeterminados" not in st.session_state:
    st.session_state.usar_predeterminados = True

usar_predeterminados = st.sidebar.checkbox(
    "Usar perfiles predeterminados",
    value=st.session_state.usar_predeterminados,
    help="Activa los perfiles originales diseñados para cada carrera."
)
st.session_state.usar_predeterminados = usar_predeterminados

perfil_config = {}
for carrera, letras_default in DEFAULT_PERFILES.items():
    widget_key = f"perfil_{carrera}"

    if usar_predeterminados:
        st.session_state[widget_key] = letras_default

    if widget_key not in st.session_state:
        st.session_state[widget_key] = letras_default

    perfil_config[carrera] = st.sidebar.multiselect(
        carrera,
        AREAS,
        default=st.session_state[widget_key],
        key=widget_key
    )

# -------------------------------------------------
# CARGA DE DATOS
# -------------------------------------------------
try:
    df_raw = load_data(url)
    df, df_intensidad, columnas_items, columna_carrera, columna_nombre, umbral_intrapersonal = process_data(
        df_raw,
        perfil_config,
        peso_intereses,
        peso_aptitudes
    )
except Exception as e:
    st.error(f"❌ No fue posible cargar/procesar el archivo: {e}")
    st.stop()

# -------------------------------------------------
# RENDER 1 · PRESENTACIÓN
# -------------------------------------------------
def render_presentacion():
    st.title("Diagnóstico Vocacional - Escala CHASIDE")

    st.markdown(
        """
En México, por cada 100 niños y niñas que inician su educación primaria, aproximadamente **32** realizan su proceso de ingreso a educación superior y, de éstos, alrededor de **20** concluirán su formación académica.

Este déficit se vuelve particularmente visible en el **primer año de licenciatura**, etapa en la que suele identificarse la mayor deserción escolar. Entre los factores que pueden intervenir se encuentran:

- Seguir la expectativa familiar de continuar con cierta profesión.
- Elegir una carrera universitaria por tendencia o moda.
- Basar la decisión solo en la promesa económica del área laboral.
- Confundir la **aptitud** con el **interés**.
- No contar aún con la madurez suficiente para valorar con claridad los pros y contras de una elección profesional.
"""
    )

    st.markdown(
        """
Estas áreas de oportunidad han sido abordadas mediante la selección y aplicación de **pruebas vocacionales**, instrumentos que buscan estimar de manera estructurada intereses, aptitudes y patrones de afinidad académica. 
Aunque ninguna prueba sustituye el acompañamiento humano, su utilidad radica en que integran múltiples reactivos, reducen el peso de la intuición inmediata y dificultan respuestas manipuladas cuando se interpretan con criterios de consistencia.
"""
    )

    st.markdown("## ¿Qué es CHASIDE y para qué sirve?")
    st.markdown(
        """
La escala **CHASIDE** es una prueba vocacional que integra dos componentes principales:

- **Intereses**: aquello que al estudiante le atrae o despierta curiosidad.
- **Aptitudes**: aquello para lo que el estudiante parece tener mayor facilidad o potencial.

La escala organiza estas tendencias en siete áreas:

- **C**: Administrativo  
- **H**: Humanidades y Sociales  
- **A**: Artístico  
- **S**: Ciencias de la Salud  
- **I**: Enseñanzas Técnicas  
- **D**: Defensa y Seguridad  
- **E**: Ciencias Experimentales  

Su propósito es identificar qué tan alineada está la elección profesional del estudiante con su perfil vocacional.
"""
    )

    st.markdown("## Propuesta Única de Valor (PUV)")
    st.markdown(
        """
Esta aplicación transforma los resultados de CHASIDE en un sistema de **diagnóstico vocacional interpretable**, 
capaz de:

- estimar el grado de ajuste entre el estudiante y la carrera elegida,
- identificar perfiles en riesgo o de alto potencial,
- sugerir trayectorias vocacionales compatibles,
- y orientar decisiones académicas de forma más objetiva y accionable.
"""
    )

# -------------------------------------------------
# RENDER 2 · ANÁLISIS GENERAL
# -------------------------------------------------
def render_analisis_general():
    st.title("Diagnóstico Vocacional - Escala CHASIDE")
    st.caption(
        f"Criterio de calidad de respuesta: el 10% inferior de la desviación intrapersona "
        f"se clasifica como 'Respondió siempre igual'. Umbral actual = {umbral_intrapersonal:.4f}"
    )

    # -------------------------
    # Pastel
    # -------------------------
    st.subheader("📊 Distribución de respuestas del estudiantado")

    df_pastel = df.copy()
    df_pastel['Categoría_Pastel'] = df_pastel['Semáforo Vocacional'].replace(CAT_MAP_LARGO)

    resumen = df_pastel['Categoría_Pastel'].value_counts().reset_index()
    resumen.columns = ['Categoría', 'N']

    fig = px.pie(
        resumen,
        names='Categoría',
        values='N',
        hole=0.4,
        color='Categoría',
        color_discrete_map={
            'El perfil coincide con la carrera elegida': '#22c55e',
            'El perfil NO va acorde con la carrera elegida': '#f59e0b',
            'No se observa un perfil prioritario': '#6b7280',
            'Respondió siempre igual': '#ef4444'
        }
    )
    fig.update_traces(textposition='inside', texttemplate='%{percent:.1%}')
    fig.update_layout(
        legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"),
        margin=dict(t=40, b=120)
    )
    st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # Barras por carrera
    # -------------------------
    st.header("📊 Distribución por carrera y categoría")

    df_barras = df.copy()
    df_barras['Categoría_Barras'] = df_barras['Semáforo Vocacional'].replace(CAT_MAP_LARGO)

    cats_order_largo = [
        'El perfil coincide con la carrera elegida',
        'El perfil NO va acorde con la carrera elegida',
        'No se observa un perfil prioritario',
        'Respondió siempre igual'
    ]

    stacked = (
        df_barras[df_barras['Categoría_Barras'].isin(cats_order_largo)]
        .groupby(['Carrera_Corta', 'Categoría_Barras'], dropna=False)
        .size()
        .reset_index(name='N')
        .rename(columns={'Categoría_Barras': 'Categoría'})
    )

    fig_stacked = px.bar(
        stacked,
        x='Carrera_Corta',
        y='N',
        color='Categoría',
        category_orders={'Categoría': cats_order_largo},
        color_discrete_map={
            'El perfil coincide con la carrera elegida': '#22c55e',
            'El perfil NO va acorde con la carrera elegida': '#f59e0b',
            'No se observa un perfil prioritario': '#6b7280',
            'Respondió siempre igual': '#ef4444'
        },
        barmode='stack',
        text='N'
    )
    fig_stacked.update_layout(
        height=650,
        xaxis_tickangle=-30,
        legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
        margin=dict(t=40, b=140)
    )
    st.plotly_chart(fig_stacked, use_container_width=True)

    # -------------------------
    # Intensidad
    # -------------------------
    st.header("📊 Intensidad del perfil vocacional por carrera")

    if df_intensidad.empty:
        st.warning("No hay datos de intensidad.")
    else:
        resumen_intensidad = (
            df_intensidad
            .groupby(['Carrera_Corta', 'Nivel_Intensidad'])
            .size()
            .reset_index(name='N')
        )

        orden_niveles = ['Sin perfil', 'Perfil en riesgo', 'Perfil en transición', 'Jóven promesa']

        fig_int = px.bar(
            resumen_intensidad,
            x='Carrera_Corta',
            y='N',
            color='Nivel_Intensidad',
            category_orders={'Nivel_Intensidad': orden_niveles},
            color_discrete_map={
                'Sin perfil': '#dc2626',
                'Perfil en riesgo': '#f59e0b',
                'Perfil en transición': '#84cc16',
                'Jóven promesa': '#16a34a'
            },
            barmode='stack'
        )
        fig_int.update_layout(
            height=700,
            xaxis_tickangle=-30,
            legend=dict(orientation="h", y=-0.2, x=0.5, xanchor="center"),
            margin=dict(t=40, b=140)
        )
        st.plotly_chart(fig_int, use_container_width=True)

        # -------------------------
        # Listados de intervención por intensidad
        # -------------------------
        st.markdown("## 📋 Listado de estudiantes por intensidad vocacional")
        st.caption(
            "Este apartado permite identificar a los estudiantes clasificados en cada nivel "
            "de intensidad vocacional para facilitar acciones de acompañamiento, canalización o seguimiento."
        )

        columnas_exportar = [
            columna_nombre,
            COLUMNA_EMAIL,
            columna_carrera,
            'Carrera_Corta',
            'Semáforo Vocacional',
            'Nivel_Intensidad'
        ]
        columnas_exportar = [c for c in columnas_exportar if c in df_intensidad.columns]

        tabs_int = st.tabs([
            "Sin perfil",
            "Perfil en riesgo",
            "Perfil en transición",
            "Jóven promesa"
        ])

        hojas_intensidad = {}

        for tab, nivel in zip(
            tabs_int,
            ['Sin perfil', 'Perfil en riesgo', 'Perfil en transición', 'Jóven promesa']
        ):
            with tab:
                sub_nivel = df_intensidad[df_intensidad['Nivel_Intensidad'] == nivel].copy()

                if sub_nivel.empty:
                    st.info(f"No hay estudiantes clasificados como '{nivel}'.")
                    hojas_intensidad[nivel] = pd.DataFrame(columns=[
                        'Nombre del estudiante',
                        'Correo electrónico',
                        'Carrera',
                        'Carrera corta',
                        'Semáforo vocacional',
                        'Nivel de intensidad'
                    ])
                else:
                    tabla = sub_nivel[columnas_exportar].copy()

                    columnas_orden = [c for c in [columna_carrera, columna_nombre] if c in tabla.columns]
                    if columnas_orden:
                        tabla = tabla.sort_values(columnas_orden)

                    tabla = tabla.rename(columns={
                        columna_nombre: 'Nombre del estudiante',
                        COLUMNA_EMAIL: 'Correo electrónico',
                        columna_carrera: 'Carrera',
                        'Carrera_Corta': 'Carrera corta',
                        'Semáforo Vocacional': 'Semáforo vocacional',
                        'Nivel_Intensidad': 'Nivel de intensidad'
                    })

                    st.dataframe(tabla, use_container_width=True)
                    st.metric("Total de estudiantes", len(tabla))
                    hojas_intensidad[nivel] = tabla

        excel_intensidad = dataframe_a_excel_bytes(hojas_intensidad)

        st.download_button(
            label="⬇️ Descargar listado de intensidad vocacional (.xlsx)",
            data=excel_intensidad,
            file_name="listado_intensidad_vocacional.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            key="download_intensidad_xlsx"
        )

    # -------------------------
    # Sankey
    # -------------------------
    st.header("🌊 Transición vocacional compatible por carrera")

    df_sankey = df.copy()
    df_sankey = df_sankey[df_sankey['Semáforo Vocacional'] != 'Respondió siempre igual'].copy()

    carreras = sorted(df_sankey[columna_carrera].dropna().astype(str).unique())

    if carreras:
        carrera_sel = st.selectbox("Selecciona carrera:", carreras, key="sankey_carrera")

        sub = df_sankey[df_sankey[columna_carrera] == carrera_sel].copy()

        if not sub.empty:
            flujos = sub['Destino_Compatible'].value_counts().reset_index()
            flujos.columns = ['Destino_Compatible', 'N']

            labels = [carrera_sel] + flujos['Destino_Compatible'].tolist()
            source = [0] * len(flujos)
            target = list(range(1, len(flujos) + 1))
            value = flujos['N'].tolist()

            fig = go.Figure(go.Sankey(
                node=dict(label=labels),
                link=dict(source=source, target=target, value=value)
            ))

            st.plotly_chart(fig, use_container_width=True)

            # -------------------------
            # Listados de transición
            # -------------------------
            st.markdown("## 📋 Listado de estudiantes por transición vocacional compatible")
            st.caption(
                "Aquí se muestran los estudiantes de la carrera seleccionada agrupados según su "
                "destino vocacional compatible. Esto permite identificar a quiénes conviene intervenir."
            )

            columnas_exportar_trans = [
                columna_nombre,
                COLUMNA_EMAIL,
                columna_carrera,
                'Area_Fuerte_Ponderada',
                'Semáforo Vocacional',
                'Destino_Compatible'
            ]
            columnas_exportar_trans = [c for c in columnas_exportar_trans if c in sub.columns]

            destinos_ordenados = flujos['Destino_Compatible'].tolist()
            tabs_trans = st.tabs(destinos_ordenados)

            hojas_transicion = {}

            for tab_dest, destino in zip(tabs_trans, destinos_ordenados):
                with tab_dest:
                    sub_dest = sub[sub['Destino_Compatible'] == destino].copy()

                    if sub_dest.empty:
                        st.info(f"No hay estudiantes con destino compatible '{destino}'.")
                        hojas_transicion[destino] = pd.DataFrame(columns=[
                            'Nombre del estudiante',
                            'Correo electrónico',
                            'Carrera elegida',
                            'Área fuerte CHASIDE',
                            'Semáforo vocacional',
                            'Carrera sugerida compatible'
                        ])
                    else:
                        tabla_dest = sub_dest[columnas_exportar_trans].copy()

                        if columna_nombre in tabla_dest.columns:
                            tabla_dest = tabla_dest.sort_values(columna_nombre)

                        tabla_dest = tabla_dest.rename(columns={
                            columna_nombre: 'Nombre del estudiante',
                            COLUMNA_EMAIL: 'Correo electrónico',
                            columna_carrera: 'Carrera elegida',
                            'Area_Fuerte_Ponderada': 'Área fuerte CHASIDE',
                            'Semáforo Vocacional': 'Semáforo vocacional',
                            'Destino_Compatible': 'Carrera sugerida compatible'
                        })

                        st.dataframe(tabla_dest, use_container_width=True)
                        st.metric("Total de estudiantes", len(tabla_dest))
                        hojas_transicion[destino] = tabla_dest

            excel_transicion = dataframe_a_excel_bytes(hojas_transicion)

            st.download_button(
                label=f"⬇️ Descargar listado de transición vocacional de {str(carrera_sel)} (.xlsx)",
                data=excel_transicion,
                file_name=f"listado_transicion_{str(carrera_sel).replace(' ', '_')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key=f"download_transicion_{str(carrera_sel)}"
            )
# -------------------------------------------------
# RENDER 3 · INFORMACIÓN INDIVIDUAL
# -------------------------------------------------
def render_info_individual():
    st.title("📘 Información particular del estudiantado – CHASIDE")
    st.caption(
        "Seleccione una carrera y un estudiante para consultar su ubicación dentro del análisis general, "
        "la recomendación individual y descargar el reporte en PDF."
    )

    carreras = sorted(df[columna_carrera].dropna().astype(str).unique())
    if not carreras:
        st.warning("No hay carreras disponibles.")
        return

    carrera_sel = st.selectbox("Carrera a evaluar:", carreras, index=0, key="ind_carrera")
    d_carrera = df[df[columna_carrera] == carrera_sel].copy()

    if d_carrera.empty:
        st.warning("No hay estudiantes para esta carrera.")
        return

    nombres = sorted(d_carrera[columna_nombre].astype(str).unique())
    est_sel = st.selectbox("Estudiante:", nombres, index=0, key="ind_estudiante")

    alumno_mask = (df[columna_carrera] == carrera_sel) & (df[columna_nombre].astype(str) == est_sel)
    alumno = df[alumno_mask].copy()
    if alumno.empty:
        st.warning("No se encontró el estudiante seleccionado.")
        return

    al = alumno.iloc[0]

    nivel_alumno = None
    if not df_intensidad.empty and alumno.index[0] in df_intensidad.index:
        nivel_alumno = df_intensidad.loc[alumno.index[0], 'Nivel_Intensidad']

    categoria_larga = CAT_MAP_LARGO.get(al['Semáforo Vocacional'], al['Semáforo Vocacional'])

    conteo_global = df['Semáforo Vocacional'].value_counts()
    n_global_cat = int(conteo_global.get(al['Semáforo Vocacional'], 0))
    pct_global_cat = (n_global_cat / len(df) * 100) if len(df) else 0

    conteo_carrera = d_carrera['Semáforo Vocacional'].value_counts()
    n_carrera_cat = int(conteo_carrera.get(al['Semáforo Vocacional'], 0))
    pct_carrera_cat = (n_carrera_cat / len(d_carrera) * 100) if len(d_carrera) else 0

    destino_compatible = al['Destino_Compatible']
    if destino_compatible == carrera_sel:
        texto_transicion = "El perfil del estudiante se mantiene dentro de la carrera elegida."
    else:
        texto_transicion = f"El perfil del estudiante presenta mejor ajuste hacia la carrera {destino_compatible}."

    if pd.notna(nivel_alumno):
        texto_intensidad = DESC_INTENSIDAD.get(nivel_alumno, str(nivel_alumno))
    else:
        texto_intensidad = "No fue posible determinar el nivel de intensidad vocacional para este estudiante."

    st.markdown("## 📍 Ubicación del estudiante dentro del análisis general")
    st.markdown(
        f"""
- **Distribución general del estudiantado:** el estudiante pertenece a la categoría **{categoria_larga}**, la cual concentra **{n_global_cat} estudiantes ({pct_global_cat:.1f}%)** del total evaluado.

- **Distribución por carrera y categoría:** dentro de **{carrera_sel}**, el estudiante se ubica en la categoría **{categoria_larga}**, grupo conformado por **{n_carrera_cat} estudiantes ({pct_carrera_cat:.1f}%)** de su carrera.

- **Intensidad del perfil vocacional por carrera:** el estudiante fue clasificado como **{nivel_alumno if pd.notna(nivel_alumno) else 'No disponible'}**.  
  {texto_intensidad}

- **Transición vocacional compatible por carrera:** {texto_transicion}
"""
    )

    st.markdown("## 📝 Conclusión y recomendación")
    texto_conclusion = construir_conclusion_recomendacion(
        al=al,
        carrera_sel=carrera_sel,
        destino_compatible=destino_compatible,
        nivel_alumno=nivel_alumno
    )
    st.markdown(texto_conclusion)

    texto_ubicacion_pdf = (
        f"Distribución general del estudiantado: el estudiante pertenece a la categoría {categoria_larga}, "
        f"la cual concentra {n_global_cat} estudiantes ({pct_global_cat:.1f}%) del total evaluado.\n"
        f"Distribución por carrera y categoría: dentro de {carrera_sel}, el estudiante se ubica en la categoría "
        f"{categoria_larga}, grupo conformado por {n_carrera_cat} estudiantes ({pct_carrera_cat:.1f}%) de su carrera.\n"
        f"Intensidad del perfil vocacional por carrera: el estudiante fue clasificado como "
        f"{nivel_alumno if pd.notna(nivel_alumno) else 'No disponible'}. {texto_intensidad}\n"
        f"Transición vocacional compatible por carrera: {texto_transicion}"
    )

    pdf_bytes = build_pdf_report(
        estudiante=est_sel,
        carrera=carrera_sel,
        categoria=categoria_larga,
        intensidad=nivel_alumno if pd.notna(nivel_alumno) else "No disponible",
        texto_ubicacion=texto_ubicacion_pdf,
        conclusion_txt=texto_conclusion
    )

    st.download_button(
        label="⬇️ Descargar perfil identificado en PDF",
        data=pdf_bytes,
        file_name=f"perfil_CHASIDE_{str(est_sel).replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )

# -------------------------------------------------
# APP
# -------------------------------------------------
if seccion == "Presentación":
    render_presentacion()
elif seccion == "Análisis general":
    render_analisis_general()
else:
    render_info_individual()
