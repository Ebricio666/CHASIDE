# ============================================
# 📌 IMPORTS
# ============================================
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import unicodedata, re

# ============================================
# 📌 CONFIGURACIÓN INICIAL
# ============================================
st.set_page_config(layout="wide")

st.title("Diagnóstico Vocacional - Escala CHASIDE")

st.markdown("""
**Tecnológico Nacional de México, Instituto Tecnológico de Colima**  
**Elaborado por:** Dra. Elena Elsa Bricio Barrios, Dr. Santiago Arceo-Díaz y Psicóloga Martha Cecilia Ramírez Guzmán
""")

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

# Posiciones: F a CV = columnas 5 a 103 en base 0
columnas_items = df.columns[5:103]

# Asegúrate de que las columnas clave existan
columna_carrera = '¿A qué carrera desea ingresar?'
columna_nombre = 'Ingrese su nombre completo'

# Validación de columnas
st.write("Columnas detectadas:", df.columns.tolist())

if columna_carrera not in df.columns or columna_nombre not in df.columns:
    st.error("❌ Revisa que 'Carrera a ingresar' y 'Nombre del estudiante' existan en tu archivo.")
    st.stop()

# ============================================
# 📌 CONVERSIÓN Sí/No a 1/0
# ============================================
df[columnas_items] = df[columnas_items].replace({
    'Sí': 1, 'Si': 1, 'si': 1, 'No': 0, 'no': 0
})

# Forzar numérico en los ítems y manejar valores raros
df[columnas_items] = (
    df[columnas_items]
    .apply(pd.to_numeric, errors='coerce')   # convierte "1", "0", vacíos, etc. a números o NaN
    .fillna(0)                               # cualquier cosa no convertible → 0
    .astype(int)                             # enteros 0/1
)

# === Vectorizar coincidencia sospechosa (sin apply) ===
suma_si = df[columnas_items].sum(axis=1)                      # cuántos "Sí"
total_resp = df[columnas_items].notna().sum(axis=1)           # cuántos ítems válidos
porcentaje_si = np.where(total_resp == 0, 0, suma_si / total_resp)
porcentaje_no = 1 - porcentaje_si
df['Coincidencia'] = np.maximum(porcentaje_si, porcentaje_no)

# ============================================
# 📌 SUMA INTERESES Y APTITUDES
# ============================================
areas = ['C', 'H', 'A', 'S', 'I', 'D', 'E']

# Mapear ítems a columnas por posición F a CV
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

# Función para mapear número de ítem a columna real
def col_item(num):
    return columnas_items[num - 1]

for area, items in intereses_items.items():
    df[f'INTERES_{area}'] = df[[col_item(i) for i in items]].sum(axis=1)

for area, items in aptitudes_items.items():
    df[f'APTITUD_{area}'] = df[[col_item(i) for i in items]].sum(axis=1)

# ============================================
# 📌 ÁREAS FUERTES Y PONDERADAS
# ============================================
df['Area_Fuerte_Intereses'] = df.apply(lambda fila: max(areas, key=lambda a: fila[f'INTERES_{a}']), axis=1)
df['Area_Fuerte_Aptitudes'] = df.apply(lambda fila: max(areas, key=lambda a: fila[f'APTITUD_{a}']), axis=1)
df['Area_Fuerte_Total'] = df.apply(lambda fila: max(areas, key=lambda a: fila[f'INTERES_{a}'] + fila[f'APTITUD_{a}']), axis=1)

peso_intereses = 0.8
peso_aptitudes = 0.2

for area in areas:
    df[f'PUNTAJE_COMBINADO_{area}'] = (
        df[f'INTERES_{area}'] * peso_intereses + df[f'APTITUD_{area}'] * peso_aptitudes
    )

df['Area_Fuerte_Ponderada'] = df.apply(lambda fila: max(areas, key=lambda a: fila[f'PUNTAJE_COMBINADO_{a}']), axis=1)

# ============================================
# 🆕 PERFIL ENRIQUECIDO (Personalidad/Aptitudes/Intereses) — fuente: doc de la psicóloga
# ============================================
perfil_carreras_enriquecido = {
    'Licenciatura en Administración': {
        'Personalidad': ['Emprendimiento', 'Convencional'],
        'Aptitudes': ['Persuasivo', 'Objetivo', 'Práctico', 'Tolerante', 'Responsable', 'Ambicioso'],
        'Intereses': ['Organizativo', 'Supervisión', 'Orden', 'Análisis', 'Síntesis', 'Colaboración', 'Cálculo', 'Justicia', 'Liderazgo']
    },
    'Contador Público': {
        'Personalidad': ['Emprendimiento', 'Convencional'],
        'Aptitudes': ['Persuasivo', 'Objetivo', 'Práctico', 'Tolerante', 'Responsable', 'Ambicioso'],
        'Intereses': ['Organizativo', 'Supervisión', 'Orden', 'Análisis', 'Síntesis', 'Colaboración', 'Cálculo', 'Justicia', 'Liderazgo']
    },
    'Arquitectura': {
        'Personalidad': ['Artística'],
        'Aptitudes': ['Sensible', 'Imaginativo', 'Creativo', 'Detallista', 'Innovador', 'Intuitivo', 'Analítico', 'Precisión', 'Senso-perceptivo'],
        'Intereses': ['Estético', 'Armónico', 'Manual', 'Visual', 'Auditivo']
    },
    'Ingeniería Mecatrónica': {
        'Personalidad': ['Realista', 'Investigativa'],
        'Aptitudes': ['Preciso', 'Práctico', 'Crítico', 'Analítico', 'Metódico', 'Observador', 'Introvertido', 'Paciente', 'Seguro'],
        'Intereses': ['Cálculo', 'Exactitud', 'Planificación', 'Clasificación', 'Numérico', 'Análisis', 'Síntesis', 'Organización', 'Orden', 'Investigación']
    },
    'Ingeniería en Sistemas Computacionales': {
        'Personalidad': ['Realista', 'Investigativa'],
        'Aptitudes': ['Preciso', 'Práctico', 'Crítico', 'Analítico', 'Metódico', 'Observador', 'Introvertido', 'Paciente', 'Seguro'],
        'Intereses': ['Cálculo', 'Exactitud', 'Planificación', 'Clasificación', 'Numérico', 'Análisis', 'Síntesis', 'Organización', 'Orden', 'Investigación']
    },
    'Ingeniería en Inteligencia Artificial': {
        'Personalidad': ['Realista', 'Investigativa'],
        'Aptitudes': ['Preciso', 'Práctico', 'Crítico', 'Analítico', 'Metódico', 'Observador', 'Introvertido', 'Paciente', 'Seguro'],
        'Intereses': ['Cálculo', 'Exactitud', 'Planificación', 'Clasificación', 'Numérico', 'Análisis', 'Síntesis', 'Organización', 'Orden', 'Investigación']
    },
    'Ingeniería Bioquímica': {
        'Personalidad': ['Realista', 'Investigativa', 'Convencional'],
        'Aptitudes': ['Preciso', 'Práctico', 'Crítico', 'Analítico', 'Metódico', 'Observador', 'Responsable', 'Ambicioso'],
        'Intereses': ['Investigación', 'Organización', 'Supervisión', 'Colaboración', 'Cálculo', 'Clasificación', 'Orden']
    },
    'Ingeniería Ambiental': {
        'Personalidad': ['Realista', 'Investigativa', 'Convencional'],
        'Aptitudes': ['Preciso', 'Práctico', 'Crítico', 'Analítico', 'Metódico', 'Observador', 'Responsable', 'Ambicioso'],
        'Intereses': ['Investigación', 'Organización', 'Supervisión', 'Colaboración', 'Cálculo', 'Clasificación', 'Orden']
    },
    'Ingeniería en Gestión Empresarial': {
        'Personalidad': ['Emprendimiento', 'Convencional', 'Social'],
        'Aptitudes': ['Responsable', 'Justo', 'Conciliador', 'Persuasivo', 'Sagaz', 'Imaginativo'],
        'Intereses': ['Liderazgo', 'Organización', 'Colaboración', 'Justicia', 'Precisión verbal', 'Relaciones de hechos', 'Lingüística', 'Orden']
    },
    'Ingeniería Industrial': {
        'Personalidad': ['Emprendimiento', 'Convencional', 'Social'],
        'Aptitudes': ['Responsable', 'Justo', 'Conciliador', 'Persuasivo', 'Sagaz', 'Imaginativo'],
        'Intereses': ['Liderazgo', 'Organización', 'Colaboración', 'Justicia', 'Precisión verbal', 'Relaciones de hechos', 'Lingüística', 'Orden']
    }
}

# ============================================
# 🆕 Normalizador de nombre de carrera + índice auxiliar
# ============================================
def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode("ascii")
    s = re.sub(r"\s+", " ", s.strip().lower())
    return s

perfil_carreras_norm = { _norm(k): v for k, v in perfil_carreras_enriquecido.items() }

# ============================================
# 🆕 Top-2 áreas por puntaje ponderado y ranking de sugerencias
# ============================================
def top2_areas_row(row, areas=('C','H','A','S','I','D','E')):
    pts = {a: row[f'PUNTAJE_COMBINADO_{a}'] for a in areas}
    orden = sorted(pts.items(), key=lambda kv: kv[1], reverse=True)
    return [orden[0][0], orden[1][0]]

def rankear_carreras_por_areas(areas_top2, perfil_dict):
    a1, a2 = areas_top2
    ranking = []
    for carrera, perfil in perfil_dict.items():
        fuertes = set()  # inferimos 'Fuerte' desde Personalidad+Intereses si quisieras; aquí usamos afinidad por letras
        bajas   = set()  # no tenemos 'Baja' explícita en el doc; lo tratamos como neutral

        # 🎯 Heurística simple: mapear letras CHASIDE a categorías del perfil
        # Para mantener tu lógica original de "Fuerte/Baja", conservamos la afinidad por top-2 áreas:
        def puntaje(area):
            # bonus si las carreras son naturalmente afines a I/E/C/A/H/S/D según tu catálogo previo
            # supondremos:
            afinidades = {
                'Arquitectura':        ['A','I'],
                'Contador Público':    ['C','H'],
                'Licenciatura en Administración': ['C','H'],
                'Ingeniería Ambiental': ['E','I'],
                'Ingeniería Bioquímica':['E','I'],
                'Ingeniería en Gestión Empresarial':['C','I'],
                'Ingeniería Industrial':['I','C'],
                'Ingeniería en Inteligencia Artificial':['I','E'],
                'Ingeniería Mecatrónica':['I','E'],
                'Ingeniería en Sistemas Computacionales':['I','E'],
            }
            af = afinidades.get(carrera, [])
            if area in af: return 2
            return 1  # neutral por defecto

        score = puntaje(a1) + puntaje(a2)
        if all(a in ['A','C','D','E','H','I','S'] for a in [a1,a2]):
            if carrera in ['Arquitectura'] and set([a1,a2]) <= set(['A','I']):
                score += 1
        ranking.append((carrera, score))
    ranking.sort(key=lambda x: x[1], reverse=True)
    return ranking

def evaluar_coherencia_por_area(area, carrera_str):
    # usa el mapeo de afinidad simple (como el original) para coherencia
    afinidades_fuerte = {
        'Arquitectura': ['A','I'],
        'Contador Público': ['C','H'],
        'Licenciatura en Administración': ['C','H'],
        'Ingeniería Ambiental': ['E','I'],
        'Ingeniería Bioquímica': ['E','I'],
        'Ingeniería en Gestión Empresarial': ['C','I'],
        'Ingeniería Industrial': ['I','C'],
        'Ingeniería en Inteligencia Artificial': ['I','E'],
        'Ingeniería Mecatrónica': ['I','E'],
        'Ingeniería en Sistemas Computacionales': ['I','E'],
    }
    afinidades_baja = {
        'Arquitectura': ['E'],
        'Contador Público': ['D'],
        'Licenciatura en Administración': ['D'],
        'Ingeniería Ambiental': ['A'],
        'Ingeniería Bioquímica': ['A','S'],
        'Ingeniería en Gestión Empresarial': ['A'],
        'Ingeniería Industrial': ['A'],
        'Ingeniería en Inteligencia Artificial': ['H'],
        'Ingeniería Mecatrónica': ['H'],
        'Ingeniería en Sistemas Computacionales': ['H'],
    }

    carr = None
    # intentar matching tolerante
    cnorm = _norm(carrera_str)
    for k in afinidades_fuerte.keys():
        if _norm(k) == cnorm:
            carr = k
            break
    if carr is None:
        return 'Sin perfil definido'

    if area in afinidades_fuerte.get(carr, []):
        return 'Coherente'
    if area in afinidades_baja.get(carr, []):
        return 'Requiere Orientación'
    return 'Neutral'

# ============================================
# 📌 EVALUACIÓN DE COHERENCIA (usando funciones nuevas)
# ============================================
df['Top2_Areas'] = df.apply(lambda r: top2_areas_row(r), axis=1)

df['Coincidencia_Intereses'] = df.apply(
    lambda r: evaluar_coherencia_por_area(r['Area_Fuerte_Intereses'], r[columna_carrera]),
    axis=1
)
df['Coincidencia_Aptitudes'] = df.apply(
    lambda r: evaluar_coherencia_por_area(r['Area_Fuerte_Aptitudes'], r[columna_carrera]),
    axis=1
)
df['Coincidencia_Ambos'] = df.apply(
    lambda r: evaluar_coherencia_por_area(r['Area_Fuerte_Total'], r[columna_carrera]),
    axis=1
)
df['Coincidencia_Ponderada'] = df.apply(
    lambda r: evaluar_coherencia_por_area(r['Area_Fuerte_Ponderada'], r[columna_carrera]),
    axis=1
)

# carrera mejor perfilada = si la carrera actual no es coherente con el ponderado, ofrece alternativas (Top-3)
def sugerencias_top3(row):
    ranking = rankear_carreras_por_areas(row['Top2_Areas'], perfil_carreras_enriquecido)
    ranking_pos = [c for c, s in ranking if s > 0]
    return ", ".join(ranking_pos[:3]) if ranking_pos else "Sin sugerencia clara"

def carrera_mejor_v2(r):
    if r['Coincidencia'] >= 0.75:
        return 'Información no aceptable'
    carr_actual = str(r[columna_carrera]).strip()
    coher = r['Coincidencia_Ponderada']
    if coher == 'Coherente':
        # Si es coherente, mantenemos la elección del estudiante
        return carr_actual
    # si no es coherente, sugiere top-3 por afinidad a las dos áreas dominantes
    return sugerencias_top3(r)

def diagnostico_v2(r):
    if r['Carrera_Mejor_Perfilada'] == 'Información no aceptable':
        return 'Información no aceptable'
    if str(r[columna_carrera]).strip() == str(r['Carrera_Mejor_Perfilada']).strip():
        return 'Perfil adecuado'
    if 'Sin sugerencia' in r['Carrera_Mejor_Perfilada']:
        return 'Sin sugerencia'
    return f"Sugerencia: {r['Carrera_Mejor_Perfilada']}"

def semaforo(r):
    diag = r['Diagnóstico Primario Vocacional']
    if 'Información no aceptable' in diag:
        return 'No aceptable'
    elif 'Sin sugerencia clara' in diag or 'Sin sugerencia' in diag:
        return 'Sin sugerencia'
    elif diag == 'Perfil adecuado':
        if r['Coincidencia_Ponderada'] == 'Coherente':
            return 'Verde'
        elif r['Coincidencia_Ponderada'] == 'Neutral':
            return 'Amarillo'
        elif r['Coincidencia_Ponderada'] == 'Requiere Orientación':
            return 'Rojo'
    elif 'Sugerencia:' in diag:
        if r['Coincidencia_Ponderada'] == 'Coherente':
            return 'Verde'
        elif r['Coincidencia_Ponderada'] == 'Neutral':
            return 'Amarillo'
        elif r['Coincidencia_Ponderada'] == 'Requiere Orientación':
            return 'Rojo'
    return 'Sin sugerencia'

df['Carrera_Mejor_Perfilada'] = df.apply(carrera_mejor_v2, axis=1)
df['Diagnóstico Primario Vocacional'] = df.apply(diagnostico_v2, axis=1)
df['Semáforo Vocacional'] = df.apply(semaforo, axis=1)

# ============================================
# 🆕 Tarjeta de perfil esperado por carrera (UI opcional)
# ============================================
with st.expander("🧭 Perfil esperado por carrera (según documento)"):
    sel_nombre = st.selectbox("Selecciona un estudiante para ver su perfil esperado y su resultado:", options=df[columna_nombre].tolist())
    fila = df[df[columna_nombre] == sel_nombre].iloc[0]
    carrera_elegida = str(fila[columna_carrera]).strip()
    key_norm = _norm(carrera_elegida)

    st.markdown(f"**Estudiante:** {sel_nombre}")
    st.markdown(f"**Carrera elegida:** {carrera_elegida}")
    st.markdown(f"**Áreas top (ponderado):** {', '.join(fila['Top2_Areas'])}")
    st.markdown(f"**Diagnóstico:** {fila['Diagnóstico Primario Vocacional']}  |  **Semáforo:** {fila['Semáforo Vocacional']}")

    # mostrar perfil esperado si lo tenemos
    perfil = perfil_carreras_norm.get(key_norm)
    if perfil:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("**Personalidad asociada**")
            st.write(", ".join(perfil.get('Personalidad', [])))
        with col2:
            st.markdown("**Aptitudes esperadas**")
            st.write(", ".join(perfil.get('Aptitudes', [])))
        with col3:
            st.markdown("**Intereses esperados**")
            st.write(", ".join(perfil.get('Intereses', [])))
    else:
        st.info("No tengo perfil enriquecido para esta carrera (aún).")

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
    df_final[df['Semáforo Vocacional'] == 'Rojo'].to_excel(writer, sheet_name='Rojo', index=False)
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
st.dataframe(df_final)
