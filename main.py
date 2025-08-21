# ============================================
# 📌 IMPORTS
# ============================================
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import plotly.express as px

# ============================================
# 📌 CONFIGURACIÓN INICIAL
# ============================================
st.set_page_config(layout="wide")

st.title("Diagnóstico Vocacional - Escala CHASIDE")

st.markdown("""
**Tecnológico Nacional de México, Instituto Tecnológico de Colima**  
**Elaborado por:** Dra. Elena Elsa Bricio Barrios, Dr. Santiago Arceo-Díaz y Psicóloga Martha Cecilia Ramírez Guzmán
""")

st.caption(
    "Esta herramienta procesa respuestas de la escala CHASIDE, calcula puntajes por área (Intereses/Aptitudes), "
    "aplica una ponderación configurable (por defecto 80% Intereses, 20% Aptitudes), "
    "y genera un semáforo de coherencia con la carrera deseada."
)

# ============================================
# 📌 LECTURA DESDE GOOGLE SHEETS (como CSV)
# ============================================
url = "https://docs.google.com/spreadsheets/d/1BNAeOSj2F378vcJE5-T8iJ8hvoseOleOHr-I7mVfYu4/export?format=csv"
df = pd.read_csv(url)
st.success("✅ Datos cargados correctamente desde Google Sheets")
st.dataframe(df.head())

# ============================================
# 📌 SELECCIÓN DE COLUMNAS
# ============================================
# Posiciones: F a CV = columnas 5 a 103 en base 0 → 98 ítems
columnas_items = df.columns[5:103]

# Nombres exactos esperados (alineados con el formulario)
columna_carrera = '¿A qué carrera desea ingresar?'
columna_nombre = 'Ingrese su nombre completo'

# Validación de columnas
st.write("Columnas detectadas:", df.columns.tolist())
faltantes = [c for c in [columna_carrera, columna_nombre] if c not in df.columns]
if faltantes:
    st.error(
        f"❌ Faltan columnas requeridas en tu archivo: {faltantes}. "
        f"Verifica que existan exactamente '{columna_carrera}' y '{columna_nombre}'."
    )
    st.stop()

# ============================================
# 📌 CONVERSIÓN Sí/No → 1/0 (robusta)
# ============================================
df_items = (
    df[columnas_items]
      .astype(str).apply(lambda col: col.str.strip().str.lower())
      .replace({
          'sí': 1, 'si': 1, 's': 1, '1': 1, 'true': 1, 'verdadero': 1, 'x': 1,
          'no': 0, 'n': 0, '0': 0, 'false': 0, 'falso': 0, '': 0, 'nan': 0
      })
      .apply(pd.to_numeric, errors='coerce')
      .fillna(0)
      .astype(int)
)
df[columnas_items] = df_items

# ============================================
# 📌 COINCIDENCIA SOSPECHOSA (vectorizado)
# ============================================
suma_si = df[columnas_items].sum(axis=1)
total_items = len(columnas_items)  # 98
porcentaje_si = np.where(total_items == 0, 0, suma_si / total_items)
porcentaje_no = 1 - porcentaje_si
df['Coincidencia'] = np.maximum(porcentaje_si, porcentaje_no)  # [0.5, 1.0]

# ============================================
# 📌 MAPEO DE ÍTEMS A ÁREAS (Intereses/Aptitudes)
# ============================================
areas = ['C', 'H', 'A', 'S', 'I', 'D', 'E']

intereses_items = {
    'C': [1, 12, 20, 53, 64, 71, 78, 85, 91, 98],
    'H': [9, 25, 34, 41, 56, 67, 74, 80, 89, 95],
    'A': [3, 11, 21, 28, 36, 45, 50, 57, 81, 96],
    'S': [8, 16, 23, 33, 44, 52, 62, 70, 87, 92],
    'I': [6, 19, 27, 38, 47, 54, 60, 75, 83, 97],
    'D': [5, 14, 24, 31, 37, 48, 58, 65, 73, 84],
    'E': [17, 32, 35, 42, 49, 61, 68, 77, 88, 93]
}

aptitudes_items = {
    'C': [2, 15, 46, 51],
    'H': [30, 63, 72, 86],
    'A': [22, 39, 76, 82],
    'S': [4, 29, 40, 69],
    'I': [10, 26, 59, 90],
    'D': [13, 18, 43, 66],
    'E': [7, 55, 79, 94]
}

def col_item(num: int) -> str:
    return columnas_items[num - 1]

for area in areas:
    df[f'INTERES_{area}'] = df[[col_item(i) for i in intereses_items[area]]].sum(axis=1)
    df[f'APTITUD_{area}'] = df[[col_item(i) for i in aptitudes_items[area]]].sum(axis=1)

# ============================================
# 📌 PONDERACIÓN (ajustable desde la UI)
# ============================================
st.subheader("⚖️ Ponderación de Intereses vs Aptitudes")
peso_intereses = st.slider("Peso de Intereses", min_value=0.0, max_value=1.0, value=0.8, step=0.05)
peso_aptitudes = 1.0 - peso_intereses
st.caption(f"Ponderación actual → Intereses: **{peso_intereses:.2f}**, Aptitudes: **{peso_aptitudes:.2f}**")

df['Area_Fuerte_Intereses'] = df.apply(lambda fila: max(areas, key=lambda a: fila[f'INTERES_{a}']), axis=1)
df['Area_Fuerte_Aptitudes'] = df.apply(lambda fila: max(areas, key=lambda a: fila[f'APTITUD_{a}']), axis=1)
df['Area_Fuerte_Total'] = df.apply(lambda fila: max(areas, key=lambda a: fila[f'INTERES_{a}'] + fila[f'APTITUD_{a}']), axis=1)

for area in areas:
    df[f'PUNTAJE_COMBINADO_{area}'] = df[f'INTERES_{area}'] * peso_intereses + df[f'APTITUD_{area}'] * peso_aptitudes

df['Area_Fuerte_Ponderada'] = df.apply(lambda fila: max(areas, key=lambda a: fila[f'PUNTAJE_COMBINADO_{a}']), axis=1)

# ============================================
# 📌 PERFILES DE CARRERAS
# ============================================
perfil_carreras = {
    'Arquitectura': {'Fuerte': ['A', 'I', 'C']},
    'Contador Público': {'Fuerte': ['C', 'D']},
    'Licenciatura en Administración': {'Fuerte': ['C', 'D']},
    'Ingeniería Ambiental': {'Fuerte': ['I', 'C', 'E']},
    'Ingeniería Bioquímica': {'Fuerte': ['I', 'C', 'E']},
    'Ingeniería en Gestión Empresarial': {'Fuerte': ['C', 'D', 'H']},
    'Ingeniería Industrial': {'Fuerte': ['I', 'C', 'D', 'H']},
    'Ingeniería en Inteligencia Artificial': {'Fuerte': ['I', 'E']},
    'Ingeniería Mecatrónica': {'Fuerte': ['I', 'E']},
    'Ingeniería en Sistemas Computacionales': {'Fuerte': ['I', 'E']}
}

def evaluar(area_chaside: str, carrera: str) -> str:
    carrera = str(carrera).strip()
    perfil = perfil_carreras.get(carrera)
    if not perfil:
        return 'Sin perfil definido'
    fuertes = perfil.get('Fuerte', [])
    bajas = perfil.get('Baja', [])  # opcional
    if area_chaside in fuertes:
        return 'Coherente'
    if area_chaside in bajas:
        return 'Requiere Orientación'
    return 'Neutral'

df['Coincidencia_Intereses'] = df.apply(lambda r: evaluar(r['Area_Fuerte_Intereses'], r[columna_carrera]), axis=1)
df['Coincidencia_Aptitudes'] = df.apply(lambda r: evaluar(r['Area_Fuerte_Aptitudes'], r[columna_carrera]), axis=1)
df['Coincidencia_Ambos'] = df.apply(lambda r: evaluar(r['Area_Fuerte_Total'], r[columna_carrera]), axis=1)
df['Coincidencia_Ponderada'] = df.apply(lambda r: evaluar(r['Area_Fuerte_Ponderada'], r[columna_carrera]), axis=1)

# ============================================
# 📌 DIAGNÓSTICO Y SEMÁFORO
# ============================================
def carrera_mejor(r):
    if r['Coincidencia'] >= 0.75:
        return 'Información no aceptable'
    a = r['Area_Fuerte_Ponderada']
    c_actual = str(r[columna_carrera]).strip()
    sugeridas = [c for c, p in perfil_carreras.items() if a in p.get('Fuerte', [])]
    if c_actual in sugeridas:
        return c_actual
    return ', '.join(sugeridas) if sugeridas else 'Sin sugerencia clara'

def diagnostico(r):
    if r['Carrera_Mejor_Perfilada'] == 'Información no aceptable':
        return 'Información no aceptable'
    if str(r[columna_carrera]).strip() == str(r['Carrera_Mejor_Perfilada']).strip():
        return 'Perfil adecuado'
    if r['Carrera_Mejor_Perfilada'] == 'Sin sugerencia clara':
        return 'Sin sugerencia clara'
    return f"Sugerencia: {r['Carrera_Mejor_Perfilada']}"

def semaforo(r):
    diag = r['Diagnóstico Primario Vocacional']
    if diag == 'Información no aceptable':
        return 'No aceptable'
    if diag == 'Sin sugerencia clara':
        return 'Sin sugerencia'
    match = r['Coincidencia_Ponderada']
    if diag == 'Perfil adecuado':
        if match == 'Coherente':
            return 'Verde'
        if match == 'Neutral':
            return 'Amarillo'
        if match == 'Requiere Orientación':
            return 'Rojo'
    if diag.startswith('Sugerencia:'):
        if match == 'Coherente':
            return 'Verde'
        if match == 'Neutral':
            return 'Amarillo'
        if match == 'Requiere Orientación':
            return 'Rojo'
    return 'Sin sugerencia'

df['Carrera_Mejor_Perfilada'] = df.apply(carrera_mejor, axis=1)
df['Diagnóstico Primario Vocacional'] = df.apply(diagnostico, axis=1)
df['Semáforo Vocacional'] = df.apply(semaforo, axis=1)

# ============================================
# 📌 EXPORTAR MULTI-HOJA
# ============================================
orden = {'Verde': 1, 'Amarillo': 2, 'Rojo': 3, 'Sin sugerencia': 4, 'No aceptable': 5}
df['Orden_Semaforo'] = df['Semáforo Vocacional'].map(orden).fillna(6)
df = df.sort_values(by=['Orden_Semaforo']).reset_index(drop=True)

cols_final = [
    columna_nombre, columna_carrera,
    'Area_Fuerte_Intereses', 'Coincidencia_Intereses',
    'Area_Fuerte_Aptitudes', 'Coincidencia_Aptitudes',
    'Area_Fuerte_Total', 'Coincidencia_Ambos',
    'Area_Fuerte_Ponderada', 'Coincidencia_Ponderada',
    'Carrera_Mejor_Perfilada', 'Diagnóstico Primario Vocacional',
    'Semáforo Vocacional'
]

df_final = df[cols_final]

output = BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    df_final[df['Semáforo Vocacional'] == 'Verde'].to_excel(writer, sheet_name='Verde', index=False)
    df_final[df['Semáforo Vocacional'] == 'Amarillo'].to_excel(writer, sheet_name='Amarillo', index=False)
    df_final[df['Semáforo Vocacional'] == 'Rojo'].to_excel(writer, sheet_name='Requiere atención', index=False)
    df_final[df['Semáforo Vocacional'] == 'Sin sugerencia'].to_excel(writer, sheet_name='Sin sugerencia', index=False)
    df_final[df['Semáforo Vocacional'] == 'No aceptable'].to_excel(writer, sheet_name='No aceptable', index=False)
output.seek(0)

st.download_button(
    label="📥 Descargar Diagnóstico Vocacional",
    data=output,
    file_name="Diagnostico_Vocacional.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.subheader("🔍 Vista previa")
st.dataframe(df_final, use_container_width=True)

# ============================================
# 📌 RESUMEN ESTADÍSTICO DESCRIPTIVO
# ============================================
st.header("📊 Resumen estadístico descriptivo")

# Mapeo para mostrar 'Rojo' como 'Requiere atención'
display_map = {
    'Verde': 'Verde',
    'Amarillo': 'Amarillo',
    'Rojo': 'Requiere atención',
    'Sin sugerencia': 'Sin sugerencia',
    'No aceptable': 'No aceptable'
}

df_display = df_final.copy()
df_display['Categoría'] = df_display['Semáforo Vocacional'].map(display_map).fillna(df_display['Semáforo Vocacional'])

# Orden deseado para mostrar
orden_cat = ['Verde', 'Amarillo', 'Requiere atención', 'Sin sugerencia', 'No aceptable']
df_display['Categoría'] = pd.Categorical(df_display['Categoría'], categories=orden_cat, ordered=True)

# 1) Totales por categoría
resumen_categoria = (
    df_display['Categoría']
    .value_counts()
    .reindex(orden_cat, fill_value=0)
    .reset_index()
)
resumen_categoria.columns = ['Categoría', 'N° de estudiantes']

st.subheader("Totales por categoría")
st.table(resumen_categoria)

# 2) Conteo por carrera dentro de cada categoría
resumen_carrera = (
    df_display
    .groupby(['Categoría', columna_carrera], dropna=False)
    .size()
    .reset_index(name='N° de estudiantes')
    .sort_values(by=['Categoría', 'N° de estudiantes'], ascending=[True, False])
)

st.subheader("Distribución por carrera dentro de cada categoría")
st.dataframe(resumen_carrera, use_container_width=True)

# Descargas de los resúmenes
csv_resumen_categoria = resumen_categoria.to_csv(index=False).encode('utf-8')
csv_resumen_carrera = resumen_carrera.to_csv(index=False).encode('utf-8')

colA, colB = st.columns(2)
with colA:
    st.download_button("⬇️ Descargar totales por categoría (CSV)", data=csv_resumen_categoria,
                       file_name="totales_por_categoria.csv", mime="text/csv")
with colB:
    st.download_button("⬇️ Descargar carreras por categoría (CSV)", data=csv_resumen_carrera,
                       file_name="carreras_por_categoria.csv", mime="text/csv")

# ============================================
# 📌 BARRAS APILADAS POR CARRERA (ABSOLUTO vs 100%)
# ============================================
st.header("📊 Distribución por carrera y categoría")

modo = st.radio(
    "Modo de visualización",
    options=["Valores absolutos", "Proporción (100% apilado)"],
    horizontal=True
)

stacked_data = (
    df_display
    .groupby([columna_carrera, 'Categoría'])
    .size()
    .reset_index(name='N° de estudiantes')
)

if modo == "Valores absolutos":
    y_col = 'N° de estudiantes'
    title = "Estudiantes por carrera y categoría (valores absolutos)"
    fig = px.bar(
        stacked_data,
        x=columna_carrera,
        y=y_col,
        color='Categoría',
        category_orders={'Categoría': orden_cat},
        barmode='stack',
        title=title,
        text='N° de estudiantes'
    )
    fig.update_traces(textposition='inside', cliponaxis=False)
    fig.update_layout(yaxis_title="Número de estudiantes", xaxis_title="Carrera", xaxis_tickangle=-30, height=620)

else:
    # Calcular porcentaje por carrera
    stacked_data['%'] = (
        stacked_data.groupby(columna_carrera)['N° de estudiantes']
        .transform(lambda x: np.where(x.sum()==0, 0, x / x.sum() * 100))
    )
    title = "Proporción (%) de estudiantes por carrera y categoría (100% apilado)"
    fig = px.bar(
        stacked_data,
        x=columna_carrera,
        y='%',
        color='Categoría',
        category_orders={'Categoría': orden_cat},
        barmode='stack',
        title=title,
        text=stacked_data['%'].round(1).astype(str) + "%"
    )
    fig.update_traces(textposition='inside', cliponaxis=False)
    fig.update_layout(yaxis_title="Proporción (%)", xaxis_title="Carrera", xaxis_tickangle=-30, height=620)

st.plotly_chart(fig, use_container_width=True)

# ============================================
# 📌 BOXPLOTS Y LISTADO DE ALUMNOS DESTACADOS
# ============================================
st.header("📦 Boxplots y detección de alumnos destacados")

# Score máximo ponderado (ya calculado antes)
score_cols = [f'PUNTAJE_COMBINADO_{a}' for a in areas]
df_scores = df.copy()
df_scores['Score'] = df_scores[score_cols].max(axis=1)

df_display_scores = df_display.copy()
df_display_scores['Score'] = df_scores['Score'].values
df_display_scores['Área fuerte'] = df['Area_Fuerte_Ponderada'].values

# --- Función auxiliar para obtener límites por carrera ---
def calcular_limites(df_sub):
    def bounds(g):
        q1 = g['Score'].quantile(0.25)
        q3 = g['Score'].quantile(0.75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        return pd.Series({'Q1': q1, 'Q3': q3, 'IQR': iqr, 'Lower': lower, 'Upper': upper})
    limites = df_sub.groupby(columna_carrera, dropna=False).apply(bounds).reset_index()
    return df_sub.merge(limites, on=columna_carrera, how='left')

# ============================================
# 🚀 ALTO POTENCIAL (Verde) – Outliers superiores y bigote superior
# ============================================
st.subheader("🚀 Alumnos de alto potencial (Categoría Verde)")

verde_df = df_display_scores[df_display_scores['Categoría'] == 'Verde'].copy()
if verde_df.empty:
    st.info("No hay alumnos en categoría Verde.")
else:
    verde_df = calcular_limites(verde_df)

    # Outliers superiores
    out_sup = verde_df[verde_df['Score'] > verde_df['Upper']]

    # Alumnos en el bigote superior (los que están justo en 'Upper')
    bigote_sup = verde_df[np.isclose(verde_df['Score'], verde_df['Upper'])]

    # Tabla consolidada
    altos_potencial = pd.concat([out_sup, bigote_sup]).drop_duplicates()
    cols_tabla = [columna_nombre, columna_carrera, 'Área fuerte', 'Score']
    st.dataframe(altos_potencial[cols_tabla].sort_values('Score', ascending=False),
                 use_container_width=True)

    # Boxplot
    fig_verde = px.box(
        verde_df,
        x=columna_carrera,
        y='Score',
        points='outliers',
        title="Boxplot por carrera – Categoría Verde"
    )
    st.plotly_chart(fig_verde, use_container_width=True)

# ============================================
# ⚠️ RED FLAGS (Amarillo) – Outliers inferiores y bigote inferior
# ============================================
st.subheader("⚠️ Alumnos Red Flags (Categoría Amarillo)")

amarillo_df = df_display_scores[df_display_scores['Categoría'] == 'Amarillo'].copy()
if amarillo_df.empty:
    st.info("No hay alumnos en categoría Amarillo.")
else:
    amarillo_df = calcular_limites(amarillo_df)

    # Outliers inferiores
    out_inf = amarillo_df[amarillo_df['Score'] < amarillo_df['Lower']]

    # Alumnos en el bigote inferior (los que están justo en 'Lower')
    bigote_inf = amarillo_df[np.isclose(amarillo_df['Score'], amarillo_df['Lower'])]

    # Tabla consolidada
    red_flags = pd.concat([out_inf, bigote_inf]).drop_duplicates()
    cols_tabla = [columna_nombre, columna_carrera, 'Área fuerte', 'Score']
    st.dataframe(red_flags[cols_tabla].sort_values('Score', ascending=True),
                 use_container_width=True)

    # Boxplot
    fig_amarillo = px.box(
        amarillo_df,
        x=columna_carrera,
        y='Score',
        points='outliers',
        title="Boxplot por carrera – Categoría Amarillo"
    )
    st.plotly_chart(fig_amarillo, use_container_width=True)
