# ============================================
# APP CHASIDE · 3 pestañas laterales
# Presentación | Análisis general | Información individual
# Ajustes del algoritmo en sidebar
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

# -------------------------------------------------
# UTILIDADES
# -------------------------------------------------
def col_item(columnas_items, i: int) -> str:
    return columnas_items[i - 1]

@st.cache_data(show_spinner=False)
def load_data(url: str) -> pd.DataFrame:
    url = url.strip()

    # Si ya es export CSV, usar tal cual
    if "export?format=csv" in url:
        final_url = url

    # Si es link de edición/visualización de Google Sheets, convertirlo
    elif "docs.google.com/spreadsheets" in url:
        try:
            file_id = url.split("/d/")[1].split("/")[0]

            gid = "0"
            if "gid=" in url:
                gid = url.split("gid=")[-1].split("&")[0].split("#")[0]

            final_url = f"https://docs.google.com/spreadsheets/d/{file_id}/export?format=csv&gid={gid}"
        except Exception:
            raise ValueError(
                "No se pudo transformar automáticamente el enlace de Google Sheets. "
                "Pega el vínculo en formato /edit o directamente en formato /export?format=csv."
            )
    else:
        final_url = url

    return pd.read_csv(final_url)
def process_data(df: pd.DataFrame, perfil_carreras: dict, peso_intereses: float, peso_aptitudes: float):
    df = df.copy()
    df.columns = df.columns.str.strip()

    # Columnas fijas
    columna_nombre = 'Ingrese su nombre completo'
    columna_carrera = '¿A qué carrera desea ingresar?'

    # Validación de columnas clave
    faltantes = [c for c in [columna_nombre, columna_carrera] if c not in df.columns]
    if faltantes:
        raise ValueError(
            f"Faltan columnas requeridas: {faltantes}. "
            f"Columnas detectadas: {list(df.columns)}"
        )

    # Reactivos CHASIDE (después de las 6 columnas iniciales)
    columnas_items = df.columns[6:104]

    if len(columnas_items) != 98:
        raise ValueError(
            f"Se esperaban 98 reactivos CHASIDE, pero se detectaron {len(columnas_items)}."
        )

    # -------------------------
    # Limpieza de datos
    # -------------------------
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

    # -------------------------
    # Calidad de respuesta
    # -------------------------
    df['Desv_Intrapersona'] = df[columnas_items].std(axis=1)
    umbral_intrapersonal = df['Desv_Intrapersona'].quantile(0.10)
    df['Respondio_Siempre_Igual'] = df['Desv_Intrapersona'] <= umbral_intrapersonal

    # -------------------------
    # Cálculo CHASIDE
    # -------------------------
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

    # -------------------------
    # Evaluación vocacional
    # -------------------------
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
        if isinstance(diag, str) and diag.startswith('Sugerencia:'):
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

    # -------------------------
    # Intensidad
    # -------------------------
    df_intensidad = df[df['Semáforo Vocacional'].isin(['Verde', 'Amarillo'])].copy()

    # -------------------------
    # Destino compatible
    # -------------------------
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

print("Estoy dentro de la función")    
# ✅ ESTE RETURN YA ESTÁ BIEN INDENTADO
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

    if usar_predeterminados and widget_key not in st.session_state:
        st.session_state[widget_key] = letras_default
    elif usar_predeterminados:
        st.session_state[widget_key] = letras_default

    perfil_config[carrera] = st.sidebar.multiselect(
        carrera,
        AREAS,
        default=st.session_state[widget_key],
        key=widget_key
    )

# Cargar datos una vez
try:
    df_raw = load_data(url)
    df, df_intensidad, columnas_items, columna_carrera, columna_nombre, umbral_intrapersonal = (
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

    st.markdown("---")
    st.markdown("## Equipo de trabajo")

    autores = [
        {
            "Nombre completo": "Elena Elsa Bricio-Barrios",
            "Correo": "elena.bricio@colima.tecnm.mx",
            "Nacionalidad": "Mexicana",
            "Grado": "Doctorado, Universidad de Guanajuato, México",
            "Adscripción": "Tecnológico Nacional de México/Instituto Tecnológico de Colima. Profesora de asignatura y Presidenta de academia del departamento de Ciencias Básicas.",
            "Temas": "Minería de datos cualitativos, Investigación educativa y simulación numérica basado en modelo matemático.",
            "ORCID": "https://orcid.org/0000-0002-1260-9740"
        },
        {
            "Nombre completo": "Santiago Arceo Diaz",
            "Correo": "santiago.arceo@colima.tecnm.mx",
            "Nacionalidad": "Mexicano",
            "Grado": "Doctorado, Universidad de Guanajuato, México",
            "Adscripción": "Tecnológico Nacional de México/Instituto Tecnológico de Colima. Profesor de asignatura y miembro del Núcleo académico del Posgrado en Sistemas Computacionales.",
            "Temas": "Minería de datos cuantitativos, Ciencia de datos, modelado estocástico.",
            "ORCID": "https://orcid.org/0000-0002-7085-3653"
        },
        {
            "Nombre completo": "Martha Cecilia Ramírez Guzmán",
            "Correo": "cecilia.ramirez@colima.tecnm.mx",
            "Nacionalidad": "Mexicana",
            "Grado": "Licenciada en Psicología, Universidad de Colima",
            "Adscripción": "Tecnológico Nacional de México/Instituto Tecnológico de Colima. Jefa del departamento de Desarrollo Académico.",
            "Temas": "Pruebas diagnósticas en el apoyo del estudiantado para aplicar técnicas de afrontamiento para mejorar su bienestar emocional.",
            "ORCID": "https://orcid.org/0009-0007-3834-0640"
        }
    ]

    for autor in autores:
        with st.expander(autor["Nombre completo"]):
            st.markdown(f"**Correo:** {autor['Correo']}")
            st.markdown(f"**Nacionalidad:** {autor['Nacionalidad']}")
            st.markdown(f"**Grado:** {autor['Grado']}")
            st.markdown(f"**Adscripción laboral:** {autor['Adscripción']}")
            st.markdown(f"**Principales temas de investigación:** {autor['Temas']}")
            st.markdown(f"**ORCID:** {autor['ORCID']}")

# -------------------------------------------------
# RENDER 2 · ANÁLISIS GENERAL
# -------------------------------------------------
def render_analisis_general():
    st.title("Diagnóstico Vocacional - Escala CHASIDE")
    st.caption(
        f"Criterio de calidad de respuesta: el 10% inferior de la desviación intrapersona "
        f"se clasifica como 'Respondió siempre igual'. Umbral actual = {umbral_intrapersonal:.4f}"
    )

    # Pastel
    st.subheader("📊 Distribución de respuestas del estudiantado")

    df_pastel = df.copy()
    df_pastel['Categoría_Pastel'] = df_pastel['Semáforo Vocacional'].replace(CAT_MAP_LARGO)

    resumen = (
        df_pastel['Categoría_Pastel']
        .value_counts()
        .reset_index()
    )
    resumen.columns = ['Categoría', 'N']

    orden_pastel = [
        'El perfil coincide con la carrera elegida',
        'El perfil NO va acorde con la carrera elegida',
        'No se observa un perfil prioritario',
        'Respondió siempre igual'
    ]

    resumen['Categoría'] = pd.Categorical(resumen['Categoría'], categories=orden_pastel, ordered=True)
    resumen = resumen.sort_values('Categoría')

    total_estudiantes = int(resumen['N'].sum())
    resumen['Porcentaje'] = np.where(total_estudiantes == 0, 0, resumen['N'] / total_estudiantes * 100)

    fig = px.pie(
        resumen,
        names='Categoría',
        values='N',
        hole=0.35,
        color='Categoría',
        color_discrete_map={
            'El perfil coincide con la carrera elegida': '#22c55e',
            'El perfil NO va acorde con la carrera elegida': '#f59e0b',
            'No se observa un perfil prioritario': '#6b7280',
            'Respondió siempre igual': '#ef4444'
        }
    )
    fig.update_traces(
        textposition='inside',
        texttemplate='%{percent:.1%}',
        hovertemplate='<b>%{label}</b><br>Porcentaje: %{percent}<br>N: %{value}<extra></extra>'
    )
    fig.update_layout(
        legend_title_text="Categoría",
        legend=dict(orientation="h", y=-0.15, yanchor="top", x=0.5, xanchor="center"),
        margin=dict(t=40, b=120)
    )
    st.plotly_chart(fig, use_container_width=True)

    conteos = resumen.set_index('Categoría')['N'].to_dict()
    porcentajes = resumen.set_index('Categoría')['Porcentaje'].to_dict()

    st.markdown("### 📝 Reporte del diagnóstico general")
    st.markdown(
        f"""
Esta escala tuvo una participación de **{total_estudiantes} estudiantes**. 
De ellos, **{conteos.get('El perfil coincide con la carrera elegida', 0)} ({porcentajes.get('El perfil coincide con la carrera elegida', 0):.1f}%)** muestran que el perfil CHASIDE **coincide con la carrera elegida**.

Por otro lado, **{conteos.get('El perfil NO va acorde con la carrera elegida', 0)} ({porcentajes.get('El perfil NO va acorde con la carrera elegida', 0):.1f}%)** presentan un perfil que **no va acorde con la carrera seleccionada**.

Asimismo, **{conteos.get('No se observa un perfil prioritario', 0)} ({porcentajes.get('No se observa un perfil prioritario', 0):.1f}%)** no muestran un **perfil prioritario claramente definido**.

Finalmente, **{conteos.get('Respondió siempre igual', 0)} ({porcentajes.get('Respondió siempre igual', 0):.1f}%)** fueron clasificados como **respondió siempre igual**.
"""
    )

    # Barras por carrera
    st.header("📊 Distribución por carrera y categoría")
    st.caption(
        "Se realizó un filtro por carrera para observar cómo respondieron los estudiantes "
        "de cada programa educativo respecto a su ajuste vocacional."
    )

    df_barras = df.copy()
    df_barras['Categoría_Barras'] = df_barras['Semáforo Vocacional'].replace(CAT_MAP_LARGO)

    cats_order_largo = [
        'El perfil coincide con la carrera elegida',
        'El perfil NO va acorde con la carrera elegida',
        'No se observa un perfil prioritario',
        'Respondió siempre igual'
    ]

    color_map_largo = {
        'El perfil coincide con la carrera elegida': '#22c55e',
        'El perfil NO va acorde con la carrera elegida': '#f59e0b',
        'No se observa un perfil prioritario': '#6b7280',
        'Respondió siempre igual': '#ef4444'
    }

    stacked = (
        df_barras[df_barras['Categoría_Barras'].isin(cats_order_largo)]
        .groupby(['Carrera_Corta', 'Categoría_Barras'], dropna=False)
        .size()
        .reset_index(name='N')
        .rename(columns={'Categoría_Barras': 'Categoría'})
    )

    stacked['Categoría'] = pd.Categorical(stacked['Categoría'], categories=cats_order_largo, ordered=True)

    modo = st.radio(
        "Modo de visualización",
        options=["Proporción (100% apilado)", "Valores absolutos"],
        horizontal=True,
        index=0,
        key="modo_barras_carrera"
    )

    if modo == "Proporción (100% apilado)":
        stacked['%'] = (
            stacked.groupby('Carrera_Corta')['N']
            .transform(lambda x: 0 if x.sum() == 0 else (x / x.sum() * 100))
        )

        fig_stacked = px.bar(
            stacked,
            x='Carrera_Corta',
            y='%',
            color='Categoría',
            category_orders={'Categoría': cats_order_largo},
            color_discrete_map=color_map_largo,
            barmode='stack',
            text=stacked['%'].round(1).astype(str) + '%',
            title="Proporción (%) de estudiantes por carrera y categoría"
        )

        fig_stacked.update_layout(
            yaxis_title="Proporción (%)",
            xaxis_title="Carrera",
            xaxis_tickangle=-30,
            height=680,
            legend_title_text="Categoría",
            legend=dict(orientation="h", y=-0.22, yanchor="top", x=0.5, xanchor="center"),
            margin=dict(t=60, b=140)
        )
    else:
        fig_stacked = px.bar(
            stacked,
            x='Carrera_Corta',
            y='N',
            color='Categoría',
            category_orders={'Categoría': cats_order_largo},
            color_discrete_map=color_map_largo,
            barmode='stack',
            text='N',
            title="Estudiantes por carrera y categoría (valores absolutos)"
        )

        fig_stacked.update_layout(
            yaxis_title="Número de estudiantes",
            xaxis_title="Carrera",
            xaxis_tickangle=-30,
            height=680,
            legend_title_text="Categoría",
            legend=dict(orientation="h", y=-0.22, yanchor="top", x=0.5, xanchor="center"),
            margin=dict(t=60, b=140)
        )
        fig_stacked.update_traces(textposition='inside', cliponaxis=False)

    st.plotly_chart(fig_stacked, use_container_width=True)

    st.markdown("### 📝 Reporte por carrera")
    resumen_carreras = (
        df_barras.groupby(['Carrera_Corta', 'Categoría_Barras'])
        .size()
        .unstack(fill_value=0)
    )

    for c in cats_order_largo:
        if c not in resumen_carreras.columns:
            resumen_carreras[c] = 0

    resumen_carreras = resumen_carreras[cats_order_largo].copy()
    resumen_carreras['Total'] = resumen_carreras.sum(axis=1)

    for c in cats_order_largo:
        resumen_carreras[f'%_{c}'] = np.where(
            resumen_carreras['Total'] == 0,
            0,
            resumen_carreras[c] / resumen_carreras['Total'] * 100
        )

    top_verde = resumen_carreras.sort_values(
        by='El perfil coincide con la carrera elegida',
        ascending=False
    ).head(2)

    top_amarillo = resumen_carreras.sort_values(
        by='El perfil NO va acorde con la carrera elegida',
        ascending=False
    ).head(2)

    top_rojo = resumen_carreras.sort_values(
        by='No se observa un perfil prioritario',
        ascending=False
    ).head(2)

    st.markdown("**Carreras con mayor proporción de ajuste vocacional (verde):**")
    for carrera, row in top_verde.iterrows():
        st.markdown(
            f"- **{carrera}**: {int(row['El perfil coincide con la carrera elegida'])} estudiantes "
            f"({row['%_El perfil coincide con la carrera elegida']:.1f}%)."
        )

    st.markdown("**Carreras con mayor proporción de perfil no acorde (amarillo):**")
    for carrera, row in top_amarillo.iterrows():
        st.markdown(
            f"- **{carrera}**: {int(row['El perfil NO va acorde con la carrera elegida'])} estudiantes "
            f"({row['%_El perfil NO va acorde con la carrera elegida']:.1f}%)."
        )

    st.markdown("**Carreras con mayor proporción de perfil no prioritario:**")
    for carrera, row in top_rojo.iterrows():
        st.markdown(
            f"- **{carrera}**: {int(row['No se observa un perfil prioritario'])} estudiantes "
            f"({row['%_No se observa un perfil prioritario']:.1f}%)."
        )

    # Intensidad
    st.header("📊 Intensidad del perfil vocacional por carrera")
    st.caption(
        "Se construyeron dos distribuciones conceptuales: la primera corresponde a los estudiantes "
        "cuyo perfil vocacional coincide con su elección de carrera, y la segunda agrupa a aquellos "
        "estudiantes cuya elección de carrera no coincide con su perfil vocacional."
    )

    if df_intensidad.empty:
        st.info("No hay estudiantes en categorías Verde o Amarillo para construir la barra de intensidad.")
    else:
        resumen_intensidad = (
            df_intensidad
            .groupby(['Carrera_Corta', 'Nivel_Intensidad'], dropna=False)
            .agg(
                N=(columna_nombre, 'count'),
                Estudiantes=(columna_nombre, lambda x: "<br>".join(sorted(x.astype(str).tolist())))
            )
            .reset_index()
        )

        orden_niveles = ['Sin perfil', 'Perfil en riesgo', 'Perfil en transición', 'Jóven promesa']
        colores_niveles = {
            'Sin perfil': '#dc2626',
            'Perfil en riesgo': '#f59e0b',
            'Perfil en transición': '#84cc16',
            'Jóven promesa': '#16a34a'
        }

        resumen_intensidad['Nivel_Intensidad'] = pd.Categorical(
            resumen_intensidad['Nivel_Intensidad'],
            categories=orden_niveles,
            ordered=True
        )

        resumen_intensidad = resumen_intensidad.sort_values(['Carrera_Corta', 'Nivel_Intensidad'])
        resumen_intensidad['%'] = (
            resumen_intensidad.groupby('Carrera_Corta')['N']
            .transform(lambda x: 0 if x.sum() == 0 else (x / x.sum() * 100))
        )

        fig_intensidad = px.bar(
            resumen_intensidad,
            x='Carrera_Corta',
            y='%',
            color='Nivel_Intensidad',
            category_orders={'Nivel_Intensidad': orden_niveles},
            color_discrete_map=colores_niveles,
            barmode='stack',
            text=resumen_intensidad['%'].round(1).astype(str) + '%',
            title="Escala de intensidad vocacional por carrera"
        )

        fig_intensidad.update_layout(
            yaxis_title="Proporción (%)",
            xaxis_title="Carrera",
            xaxis_tickangle=-30,
            height=720,
            legend_title_text="Nivel",
            legend=dict(orientation="h", y=-0.25, yanchor="top", x=0.5, xanchor="center"),
            margin=dict(t=60, b=150)
        )

        fig_intensidad.update_traces(
            customdata=np.stack(
                [
                    resumen_intensidad['Nivel_Intensidad'],
                    resumen_intensidad['N'],
                    resumen_intensidad['Estudiantes']
                ],
                axis=-1
            ),
            hovertemplate=(
                "<b>Carrera:</b> %{x}<br>"
                "<b>Nivel:</b> %{customdata[0]}<br>"
                "<b>Porcentaje:</b> %{y:.1f}%<br>"
                "<b>Número de estudiantes:</b> %{customdata[1]}<br>"
                "<b>Estudiantes:</b><br>%{customdata[2]}"
                "<extra></extra>"
            )
        )

        st.plotly_chart(fig_intensidad, use_container_width=True)

        st.markdown("### Lectura sugerida de la escala")
        st.markdown(
            """
- **Sin perfil**: estudiantes cuya elección de carrera no muestra correspondencia con su perfil vocacional.  
- **Perfil en riesgo**: estudiantes cuyo perfil vocacional presenta una coincidencia mínima con la carrera elegida.  
- **Perfil en transición**: estudiantes cuya elección profesional y perfil vocacional presentan congruencia, aunque aún en proceso de consolidación.  
- **Jóven promesa**: estudiantes con alta congruencia entre su perfil vocacional y la carrera elegida.
"""
        )

    # Sankey
    st.header("🌊 Transición vocacional compatible por carrera")
    st.caption(
        "Seleccione una carrera para analizar si sus estudiantes presentan mejor ajuste "
        "hacia otra carrera con perfil CHASIDE compatible."
    )

    df_sankey = df.copy()
    df_sankey = df_sankey[~df_sankey['Semáforo Vocacional'].isin(['Respondió siempre igual'])].copy()
    df_sankey[columna_carrera] = df_sankey[columna_carrera].astype(str).str.strip()

    carreras_disp = sorted(df_sankey[columna_carrera].dropna().unique())

    if carreras_disp:
        carrera_sel = st.selectbox("Seleccione la carrera de origen:", carreras_disp, key="sankey_carrera_origen")

        sub = df_sankey[df_sankey[columna_carrera] == carrera_sel].copy()

        if sub.empty:
            st.warning("No hay estudiantes para esta carrera.")
        else:
            sub['Destino_Compatible'] = sub.apply(lambda row: df.loc[row.name, 'Destino_Compatible'], axis=1)

            flujos = (
                sub.groupby('Destino_Compatible')
                .size()
                .reset_index(name='N')
                .sort_values('N', ascending=False)
            )

            n_total = len(sub)

            def letras_txt(c):
                return ", ".join(perfil_config.get(c, []))

            label_origen = [f"{carrera_sel}<br>Perfil esperado: {letras_txt(carrera_sel)}<br>Total: {n_total}"]
            label_destinos = [
                f"{row['Destino_Compatible']}<br>Perfil: {letras_txt(row['Destino_Compatible'])}<br>Final: {row['N']}"
                for _, row in flujos.iterrows()
            ]

            labels = label_origen + label_destinos
            source = [0] * len(flujos)
            target = list(range(1, len(flujos) + 1))
            value = flujos['N'].tolist()

            palette = px.colors.qualitative.Bold + px.colors.qualitative.Dark24
            destinos_unicos = flujos['Destino_Compatible'].tolist()
            color_map_destino = {c: palette[i % len(palette)] for i, c in enumerate(destinos_unicos)}
            color_map_destino[carrera_sel] = '#22c55e'

            node_colors = ['#60a5fa'] + [color_map_destino[d] for d in flujos['Destino_Compatible']]
            link_colors = [color_map_destino[d] for d in flujos['Destino_Compatible']]

            porcentajes = (flujos['N'] / n_total * 100).round(1)
            customdata = np.stack(
                [
                    [carrera_sel] * len(flujos),
                    flujos['Destino_Compatible'],
                    flujos['N'],
                    porcentajes
                ],
                axis=-1
            )

            fig_sankey = go.Figure(data=[go.Sankey(
                arrangement="snap",
                node=dict(
                    pad=20,
                    thickness=24,
                    line=dict(color="black", width=0.3),
                    label=labels,
                    color=node_colors,
                    hoverlabel=dict(font=dict(color="black", size=13))
                ),
                link=dict(
                    source=source,
                    target=target,
                    value=value,
                    color=link_colors,
                    customdata=customdata,
                    hovertemplate=(
                        "Carrera elegida: %{customdata[0]}<br>"
                        "Carrera sugerida compatible: %{customdata[1]}<br>"
                        "Estudiantes: %{customdata[2]}<br>"
                        "Porcentaje del total: %{customdata[3]}%<extra></extra>"
                    )
                )
            )])

            fig_sankey.update_layout(
                title=f"Transición vocacional compatible desde {carrera_sel}",
                font=dict(size=14, color="black", family="Arial"),
                plot_bgcolor="white",
                paper_bgcolor="white",
                height=760
            )

            st.plotly_chart(fig_sankey, use_container_width=True)

    # Pareto
    st.header("📊 Prioridades CHASIDE por carrera")
    st.caption(
        "Seleccione una carrera para comparar el promedio del grupo 'Perfil en riesgo' "
        "contra el promedio del grupo 'Jóven promesa'."
    )

    df_pareto = df.copy()
    for a in AREAS:
        df_pareto[a] = df[f'INTERES_{a}'] + df[f'APTITUD_{a}']

    df_pareto = df_pareto.loc[df_intensidad.index].copy()
    df_pareto['Nivel_Intensidad'] = df_intensidad['Nivel_Intensidad'].values
    df_pareto['Carrera'] = df.loc[df_pareto.index, columna_carrera].values
    df_pareto['Carrera_Corta'] = (
        df_pareto['Carrera']
        .astype(str)
        .str.replace('Ingeniería', 'Ing.', regex=False)
    )

    carreras_disp_p = sorted(df_pareto['Carrera_Corta'].dropna().unique())
    carrera_sel_corta = st.selectbox("Seleccione una carrera:", carreras_disp_p, key="select_pareto_fusion")

    sub = df_pareto[df_pareto['Carrera_Corta'] == carrera_sel_corta].copy()
    riesgo = sub[sub['Nivel_Intensidad'] == 'Perfil en riesgo'].copy()
    promesa = sub[sub['Nivel_Intensidad'] == 'Jóven promesa'].copy()

    if riesgo.empty or promesa.empty:
        st.warning("No hay suficientes estudiantes en 'Perfil en riesgo' y 'Jóven promesa' para esta carrera.")
    else:
        prom_riesgo = riesgo[AREAS].mean()
        prom_promesa = promesa[AREAS].mean()

        resultados = []
        for a in AREAS:
            meta = prom_promesa[a]
            medido = prom_riesgo[a]
            error_pct = 0.0 if meta == 0 else max(((meta - medido) / meta) * 100, 0.0)

            resultados.append({
                'Letra': a,
                'Área': AREAS_LONG[a],
                'Meta': float(meta),
                'Medido': float(medido),
                'Error_Porcentual': float(error_pct)
            })

        df_plot = pd.DataFrame(resultados).sort_values('Error_Porcentual', ascending=False).reset_index(drop=True)

        total_error = df_plot['Error_Porcentual'].sum()
        if total_error == 0:
            df_plot['Porcentaje_Relativo'] = 0.0
            df_plot['Acumulado'] = 0.0
        else:
            df_plot['Porcentaje_Relativo'] = df_plot['Error_Porcentual'] / total_error * 100
            df_plot['Acumulado'] = df_plot['Porcentaje_Relativo'].cumsum()

        df_plot['Dentro_80'] = False
        acumulado_tmp = 0.0
        for idx in df_plot.index:
            if acumulado_tmp < 80:
                df_plot.at[idx, 'Dentro_80'] = True
                acumulado_tmp = df_plot.at[idx, 'Acumulado']

        colores_barras = []
        for _, row in df_plot.iterrows():
            if row['Dentro_80']:
                if row['Error_Porcentual'] >= 25:
                    colores_barras.append('#b91c1c')
                elif row['Error_Porcentual'] >= 15:
                    colores_barras.append('#ea580c')
                else:
                    colores_barras.append('#f59e0b')
            else:
                colores_barras.append('#94a3b8')

        fig_pareto = go.Figure()
        fig_pareto.add_bar(
            x=df_plot['Letra'],
            y=df_plot['Error_Porcentual'],
            name='Error porcentual de estudiantes en rezago respecto a alto desempeño',
            marker_color=colores_barras,
            customdata=np.stack(
                [
                    df_plot['Área'],
                    df_plot['Meta'],
                    df_plot['Medido'],
                    df_plot['Porcentaje_Relativo'],
                    df_plot['Acumulado']
                ],
                axis=-1
            ),
            hovertemplate=(
                "<b>Letra:</b> %{x}<br>"
                "<b>Área:</b> %{customdata[0]}<br>"
                "<b>Valor meta (Jóven promesa):</b> %{customdata[1]:.2f}<br>"
                "<b>Valor medido (Perfil en riesgo):</b> %{customdata[2]:.2f}<br>"
                "<b>Error porcentual:</b> %{y:.2f}%<br>"
                "<b>Peso relativo:</b> %{customdata[3]:.2f}%<br>"
                "<b>Error acumulado:</b> %{customdata[4]:.2f}%<extra></extra>"
            )
        )

        fig_pareto.add_scatter(
            x=df_plot['Letra'],
            y=df_plot['Acumulado'],
            name='Error porcentual acumulado',
            mode='lines+markers',
            yaxis='y2',
            line=dict(color='#16a34a', width=3),
            marker=dict(size=8, color='#16a34a')
        )

        fig_pareto.add_hline(y=80, line_dash='dash', line_color='#7c3aed', yref='y2')

        fig_pareto.update_layout(
            title=f"Pareto de prioridades CHASIDE – {carrera_sel_corta}",
            xaxis_title="Letra CHASIDE",
            yaxis_title="Error porcentual (%)",
            yaxis2=dict(
                title="Porcentaje acumulado (%)",
                overlaying='y',
                side='right',
                range=[0, 110]
            ),
            legend=dict(orientation='h', y=-0.18, x=0.5, xanchor='center'),
            height=680,
            margin=dict(t=70, b=120)
        )

        st.plotly_chart(fig_pareto, use_container_width=True)

        st.markdown("### 📝 Resumen ejecutivo de prioridades")

        if total_error == 0:
            st.success(
                "No se observaron brechas entre 'Perfil en riesgo' y 'Jóven promesa' en esta carrera."
            )
        else:
            criticas = df_plot[df_plot['Dentro_80']].copy()
            letras_criticas = criticas['Letra'].tolist()
            acumulado_final = criticas['Acumulado'].iloc[-1] if not criticas.empty else 0

            st.markdown(
                f"En **{carrera_sel_corta}**, las letras CHASIDE que concentran aproximadamente el "
                f"**80% de la brecha acumulada** son: **{', '.join(letras_criticas)}**."
            )

            st.markdown(
                f"Estas letras explican en conjunto **{acumulado_final:.1f}%** del problema detectado "
                f"entre el grupo **Perfil en riesgo** y el grupo **Jóven promesa**."
            )

            st.markdown("**Áreas prioritarias de intervención y estrategia sugerida:**")
            for _, row in criticas.iterrows():
                letra = row['Letra']
                estrategia = ESTRATEGIAS_CHASIDE.get(letra, {}).get("estrategia", "Sin estrategia definida.")
                area_nombre = ESTRATEGIAS_CHASIDE.get(letra, {}).get("area", row['Área'])

                st.markdown(
                    f"""
- **{letra} ({area_nombre})**  
  **Brecha detectada:** error porcentual de **{row['Error_Porcentual']:.2f}%** y peso relativo de **{row['Porcentaje_Relativo']:.2f}%**.  
  **Estrategia sugerida para {carrera_sel_corta}:** {estrategia}
"""
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

    st.markdown("### 🧭 Selección de carrera y estudiante")

    carreras = sorted(df[columna_carrera].dropna().astype(str).unique())
    if not carreras:
        st.warning("No hay carreras disponibles en el archivo.")
        return

    carrera_sel = st.selectbox("Carrera a evaluar:", carreras, index=0)
    d_carrera = df[df[columna_carrera] == carrera_sel].copy()

    if d_carrera.empty:
        st.warning("No hay estudiantes para esta carrera.")
        return

    nombres = sorted(d_carrera[columna_nombre].astype(str).unique())
    est_sel = st.selectbox("Estudiante:", nombres, index=0)

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
        texto_transicion = f"El perfil del estudiante presenta mejor ajuste hacia la carrera **{destino_compatible}**."

    if pd.notna(nivel_alumno):
        texto_intensidad = DESC_INTENSIDAD.get(nivel_alumno, nivel_alumno)
    else:
        texto_intensidad = "No fue posible determinar el nivel de intensidad vocacional para este estudiante."

    st.markdown("## 📍 Ubicación del estudiante dentro del análisis general")
    st.markdown(
        f"""
- **Distribución general del estudiantado:** el estudiante pertenece a la categoría **{categoria_larga}**, 
la cual concentra **{n_global_cat} estudiantes ({pct_global_cat:.1f}%)** del total evaluado.

- **Distribución por carrera y categoría:** dentro de **{carrera_sel}**, el estudiante se ubica en la categoría 
**{categoria_larga}**, grupo conformado por **{n_carrera_cat} estudiantes ({pct_carrera_cat:.1f}%)** de su carrera.

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
        f"Transición vocacional compatible por carrera: "
        f"{'El perfil del estudiante se mantiene dentro de la carrera elegida.' if destino_compatible == carrera_sel else f'El perfil del estudiante presenta mejor ajuste hacia {destino_compatible}.'}"
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
        file_name=f"perfil_CHASIDE_{est_sel.replace(' ', '_')}.pdf",
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
