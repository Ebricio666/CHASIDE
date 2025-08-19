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
columnas_items = df.columns[5:103]  # F a CV

columna_carrera = '¿A qué carrera desea ingresar?'
columna_nombre  = 'Ingrese su nombre completo'

st.write("Columnas detectadas:", df.columns.tolist())

if columna_carrera not in df.columns or columna_nombre not in df.columns:
    st.error("❌ Revisa que 'Carrera a ingresar' y 'Nombre del estudiante' existan en tu archivo.")
    st.stop()

# ============================================
# 📌 CONVERSIÓN Sí/No a 1/0
# ============================================
df[columnas_items] = df[columnas_items].replace({'Sí':1,'Si':1,'si':1,'No':0,'no':0})
df[columnas_items] = (
    df[columnas_items]
    .apply(pd.to_numeric, errors='coerce')
    .fillna(0)
    .astype(int)
)

# Coincidencia sospechosa (vectorizado)
suma_si = df[columnas_items].sum(axis=1)
total_resp = df[columnas_items].notna().sum(axis=1)
porcentaje_si = np.where(total_resp == 0, 0, suma_si / total_resp)
porcentaje_no = 1 - porcentaje_si
df['Coincidencia'] = np.maximum(porcentaje_si, porcentaje_no)

# ============================================
# 📌 SUMA INTERESES Y APTITUDES
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

def col_item(num): return columnas_items[num-1]

for a, items in intereses_items.items():
    df[f'INTERES_{a}'] = df[[col_item(i) for i in items]].sum(axis=1)
for a, items in aptitudes_items.items():
    df[f'APTITUD_{a}'] = df[[col_item(i) for i in items]].sum(axis=1)

# ============================================
# 📌 ÁREAS FUERTES Y PONDERADAS
# ============================================
df['Area_Fuerte_Intereses'] = df.apply(lambda r: max(areas, key=lambda a: r[f'INTERES_{a}']), axis=1)
df['Area_Fuerte_Aptitudes'] = df.apply(lambda r: max(areas, key=lambda a: r[f'APTITUD_{a}']), axis=1)
df['Area_Fuerte_Total']     = df.apply(lambda r: max(areas, key=lambda a: r[f'INTERES_{a}'] + r[f'APTITUD_{a}']), axis=1)

peso_intereses, peso_aptitudes = 0.8, 0.2
for a in areas:
    df[f'PUNTAJE_COMBINADO_{a}'] = df[f'INTERES_{a}'] * peso_intereses + df[f'APTITUD_{a}'] * peso_aptitudes

df['Area_Fuerte_Ponderada'] = df.apply(lambda r: max(areas, key=lambda a: r[f'PUNTAJE_COMBINADO_{a}']), axis=1)

# Top-2 áreas (para afinidad)
def top2_areas_row(r):
    pts = {a: r[f'PUNTAJE_COMBINADO_{a}'] for a in areas}
    orden = sorted(pts.items(), key=lambda kv: kv[1], reverse=True)
    return [orden[0][0], orden[1][0]]
df['Top2_Areas'] = df.apply(top2_areas_row, axis=1)

# ============================================
# 🧩 CHASIDE por letra (de la tabla que compartiste)
# ============================================
perfil_chaside = {
    'C': {'Intereses':['Organizativo','Supervisión','Orden','Análisis y síntesis','Colaboración','Cálculo'],
          'Aptitudes':['Persuasivo','Objetivo','Práctico','Tolerante','Responsable','Ambicioso']},
    'H': {'Intereses':['Precisión Verbal','Organización','Relación de Hechos','Lingüística','Orden','Justicia'],
          'Aptitudes':['Responsable','Justo','Conciliador','Persuasivo','Sagaz','Imaginativo']},
    'A': {'Intereses':['Estético','Armónico','Manual','Visual','Auditive','Auditivo'],
          'Aptitudes':['Sensible','Imaginativo','Creativo','Detallista','Innovador','Intuitivo']},
    'S': {'Intereses':['Asistir','Investigativo','Precisión','Senso-Perceptivo','Analítico','Ayudar'],
          'Aptitudes':['Altruista','Solidario','Paciente','Comprensivo','Respetuoso','Persuasivo']},
    'I': {'Intereses':['Cálculo','Científico','Manual','Exacto','Planificar'],
          'Aptitudes':['Preciso','Práctico','Crítico','Analítico','Rígido']},
    'D': {'Intereses':['Justicia','Equidad','Colaboración','Espíritu de Equipo','Liderazgo'],
          'Aptitudes':['Arriesgado','Solidario','Valiente','Agresivo','Persuasivo']},
    'E': {'Intereses':['Investigación','Orden','Organización','Análisis y Síntesis','Numérico','Clasificar'],
          'Aptitudes':['Metódico','Analítico','Observador','Introvertido','Paciente','Seguro']}
}

# ============================================
# 🧭 Documento de la psicóloga (perfil enriquecido por carrera)
# ============================================
perfil_carreras_doc = {
    'Licenciatura en Administración': {
        'Personalidad': ['Emprendimiento','Convencional'],
        'Aptitudes':   ['Persuasivo','Objetivo','Práctico','Tolerante','Responsable','Ambicioso'],
        'Intereses':   ['Organizativo','Supervisión','Orden','Análisis','Síntesis','Colaboración','Cálculo','Justicia','Liderazgo']
    },
    'Contador Público': {
        'Personalidad': ['Emprendimiento','Convencional'],
        'Aptitudes':   ['Persuasivo','Objetivo','Práctico','Tolerante','Responsable','Ambicioso'],
        'Intereses':   ['Organizativo','Supervisión','Orden','Análisis','Síntesis','Colaboración','Cálculo','Justicia','Liderazgo']
    },
    'Arquitectura': {
        'Personalidad': ['Artística'],
        'Aptitudes':   ['Sensible','Imaginativo','Creativo','Detallista','Innovador','Intuitivo','Analítico','Precisión','Senso-perceptivo'],
        'Intereses':   ['Estético','Armónico','Manual','Visual','Auditivo']
    },
    'Ingeniería Mecatrónica': {
        'Personalidad': ['Realista','Investigativa'],
        'Aptitudes':   ['Preciso','Práctico','Crítico','Analítico','Metódico','Observador','Introvertido','Paciente','Seguro'],
        'Intereses':   ['Cálculo','Exactitud','Planificación','Clasificación','Numérico','Análisis','Síntesis','Organización','Orden','Investigación']
    },
    'Ingeniería en Sistemas Computacionales': {
        'Personalidad': ['Realista','Investigativa'],
        'Aptitudes':   ['Preciso','Práctico','Crítico','Analítico','Metódico','Observador','Introvertido','Paciente','Seguro'],
        'Intereses':   ['Cálculo','Exactitud','Planificación','Clasificación','Numérico','Análisis','Síntesis','Organización','Orden','Investigación']
    },
    'Ingeniería en Inteligencia Artificial': {
        'Personalidad': ['Realista','Investigativa'],
        'Aptitudes':   ['Preciso','Práctico','Crítico','Analítico','Metódico','Observador','Introvertido','Paciente','Seguro'],
        'Intereses':   ['Cálculo','Exactitud','Planificación','Clasificación','Numérico','Análisis','Síntesis','Organización','Orden','Investigación']
    },
    'Ingeniería Bioquímica': {
        'Personalidad': ['Realista','Investigativa','Convencional'],
        'Aptitudes':   ['Preciso','Práctico','Crítico','Analítico','Metódico','Observador','Responsable','Ambicioso'],
        'Intereses':   ['Investigación','Organización','Supervisión','Colaboración','Cálculo','Clasificación','Orden']
    },
    'Ingeniería Ambiental': {
        'Personalidad': ['Realista','Investigativa','Convencional'],
        'Aptitudes':   ['Preciso','Práctico','Crítico','Analítico','Metódico','Observador','Responsable','Ambicioso'],
        'Intereses':   ['Investigación','Organización','Supervisión','Colaboración','Cálculo','Clasificación','Orden']
    },
    'Ingeniería en Gestión Empresarial': {
        'Personalidad': ['Emprendimiento','Convencional','Social'],
        'Aptitudes':   ['Responsable','Justo','Conciliador','Persuasivo','Sagaz','Imaginativo'],
        'Intereses':   ['Liderazgo','Organización','Colaboración','Justicia','Precisión verbal','Relaciones de hechos','Lingüística','Orden']
    },
    'Ingeniería Industrial': {
        'Personalidad': ['Emprendimiento','Convencional','Social'],
        'Aptitudes':   ['Responsable','Justo','Conciliador','Persuasivo','Sagaz','Imaginativo'],
        'Intereses':   ['Liderazgo','Organización','Colaboración','Justicia','Precisión verbal','Relaciones de hechos','Lingüística','Orden']
    }
}

# Letras CHASIDE esperadas por carrera (puente CHASIDE ↔ documento)
letras_por_carrera = {
    'Arquitectura': ['A','I'],
    'Contador Público': ['C','H'],
    'Licenciatura en Administración': ['C','H'],
    'Ingeniería Ambiental': ['E','I','C'],
    'Ingeniería Bioquímica': ['E','I','C'],
    'Ingeniería en Gestión Empresarial': ['C','I','H'],
    'Ingeniería Industrial': ['I','C','H'],
    'Ingeniería en Inteligencia Artificial': ['I','E'],
    'Ingeniería Mecatrónica': ['I','E'],
    'Ingeniería en Sistemas Computacionales': ['I','E'],
}

# Normalizador
def _norm(s: str):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii","ignore").decode("ascii")
    return re.sub(r"\s+"," ", s.strip().lower())

# Perfil fusionado por carrera (CHASIDE + documento psicóloga)
def perfil_carrera_fusionado(nombre):
    # encontrar clave normalizada
    key = None
    for k in letras_por_carrera.keys():
        if _norm(k) == _norm(nombre):
            key = k
            break
    if key is None:
        return {'Letras':[], 'Intereses':[], 'Aptitudes':[], 'Personalidad':[]}

    letras = letras_por_carrera[key]
    intereses = []
    aptitudes = []
    for l in letras:
        intereses += perfil_chaside[l]['Intereses']
        aptitudes += perfil_chaside[l]['Aptitudes']

    doc = perfil_carreras_doc.get(key, {})
    intereses += doc.get('Intereses', [])
    aptitudes += doc.get('Aptitudes', [])
    personalidad = doc.get('Personalidad', [])

    # quita duplicados conservando orden
    def _uniq(seq):
        seen=set(); out=[]
        for x in seq:
            if x not in seen:
                seen.add(x); out.append(x)
        return out

    return {
        'Letras': letras,
        'Intereses': _uniq(intereses),
        'Aptitudes': _uniq(aptitudes),
        'Personalidad': personalidad
    }

# Coherencia (como referencia para semáforo)
def evaluar_coherencia_por_area(area, carrera):
    letras = perfil_carrera_fusionado(carrera)['Letras']
    if not letras: return 'Sin perfil definido'
    if area in letras: return 'Coherente'
    # si está "cerca": consideramos neutral
    return 'Neutral'

df['Coincidencia_Ponderada'] = df.apply(
    lambda r: evaluar_coherencia_por_area(r['Area_Fuerte_Ponderada'], r[columna_carrera]),
    axis=1
)

# Score de afinidad por carrera (por estudiante)
def score_afinidad(row, carrera):
    fusion = perfil_carrera_fusionado(carrera)
    letras = set(fusion['Letras'])
    if not letras: 
        return -999  # penaliza carreras no mapeadas

    a1, a2 = row['Top2_Areas'][0], row['Top2_Areas'][1]
    score = 0
    # match con top areas
    if a1 in letras: score += 3
    if a2 in letras: score += 2
    # bonus por coherencia ponderada
    coher = evaluar_coherencia_por_area(row['Area_Fuerte_Ponderada'], carrera)
    score += {'Coherente':1, 'Neutral':0}.get(coher, 0)
    # penalización por respuestas sospechosas
    if row['Coincidencia'] >= 0.75: score -= 5
    return score

# Mejor carrera perfilada (fusión CHASIDE + documento)
oferta = list(letras_por_carrera.keys())
def mejor_carrera_row(row):
    ranking = sorted([(c, score_afinidad(row, c)) for c in oferta], key=lambda x: x[1], reverse=True)
    top = ranking[0]
    if top[1] < 0:  # todo negativo -> sin sugerencia útil
        return "Sin sugerencia clara"
    # si la carrera elegida es coherente y empata con el top, respetar elección
    elegida = str(row[columna_carrera]).strip()
    if evaluar_coherencia_por_area(row['Area_Fuerte_Ponderada'], elegida) == 'Coherente':
        return elegida
    return top[0]

df['Carrera_Mejor_Perfilada'] = df.apply(mejor_carrera_row, axis=1)

def diagnostico_v2(r):
    if r['Carrera_Mejor_Perfilada'] == 'Sin sugerencia clara':
        return 'Sin sugerencia'
    if str(r[columna_carrera]).strip() == str(r['Carrera_Mejor_Perfilada']).strip():
        return 'Perfil adecuado'
    return f"Sugerencia: {r['Carrera_Mejor_Perfilada']}"

def semaforo(r):
    diag = r['Diagnóstico Primario Vocacional']
    if r['Coincidencia'] >= 0.75:
        return 'No aceptable'
    if 'Sin sugerencia' in diag:
        return 'Sin sugerencia'
    if diag == 'Perfil adecuado':
        return 'Verde' if r['Coincidencia_Ponderada']=='Coherente' else 'Amarillo'
    if 'Sugerencia:' in diag:
        return 'Verde' if r['Coincidencia_Ponderada']=='Coherente' else 'Amarillo'
    return 'Sin sugerencia'

df['Diagnóstico Primario Vocacional'] = df.apply(diagnostico_v2, axis=1)
df['Semáforo Vocacional']            = df.apply(semaforo, axis=1)

# ============================================
# 🧭 Tarjeta de perfil fusionado por carrera
# ============================================
with st.expander("🧭 Perfil esperado por carrera (fusión CHASIDE + documento)"):
    sel_nombre = st.selectbox("Selecciona un estudiante:", options=df[columna_nombre].tolist())
    fila = df[df[columna_nombre] == sel_nombre].iloc[0]
    carrera_elegida = str(fila[columna_carrera]).strip()
    fusion = perfil_carrera_fusionado(carrera_elegida)

    st.markdown(f"**Estudiante:** {sel_nombre}")
    st.markdown(f"**Carrera elegida:** {carrera_elegida}")
    st.markdown(f"**Áreas Top (ponderado):** {', '.join(fila['Top2_Areas'])}")
    st.markdown(f"**Diagnóstico:** {fila['Diagnóstico Primario Vocacional']}  |  **Semáforo:** {fila['Semáforo Vocacional']}")

    if fusion['Letras']:
        c1,c2,c3 = st.columns(3)
        with c1:
            st.markdown("**Letras CHASIDE esperadas**")
            st.write(", ".join(fusion['Letras']))
        with c2:
            st.markdown("**Aptitudes esperadas (fusionadas)**")
            st.write(", ".join(fusion['Aptitudes']))
        with c3:
            st.markdown("**Intereses esperados (fusionados)**")
            st.write(", ".join(fusion['Intereses']))
        if fusion['Personalidad']:
            st.markdown("**Personalidad asociada (documento)**")
            st.write(", ".join(fusion['Personalidad']))
    else:
        st.info("No tengo mapeo para esta carrera (aún).")

# ============================================
# 📌 EXPORTAR MULTI-HOJA
# ============================================
orden = {'Verde':1,'Amarillo':2,'Rojo':3,'Sin sugerencia':4,'No aceptable':5}
df['Orden_Semaforo'] = df['Semáforo Vocacional'].map(orden).fillna(6)
df = df.sort_values(by=['Orden_Semaforo']).reset_index(drop=True)

cols_final = [
    columna_nombre, columna_carrera,
    'Area_Fuerte_Intereses','Area_Fuerte_Aptitudes','Area_Fuerte_Total',
    'Area_Fuerte_Ponderada','Top2_Areas',
    'Coincidencia_Ponderada','Carrera_Mejor_Perfilada',
    'Diagnóstico Primario Vocacional','Semáforo Vocacional'
]

df_final = df[cols_final]

output = BytesIO()
with pd.ExcelWriter(output, engine='openpyxl') as writer:
    df_final[df['Semáforo Vocacional']=='Verde'].to_excel(writer, sheet_name='Verde', index=False)
    df_final[df['Semáforo Vocacional']=='Amarillo'].to_excel(writer, sheet_name='Amarillo', index=False)
    df_final[df['Semáforo Vocacional']=='Rojo'].to_excel(writer, sheet_name='Rojo', index=False)
    df_final[df['Semáforo Vocacional']=='Sin sugerencia'].to_excel(writer, sheet_name='Sin sugerencia', index=False)
    df_final[df['Semáforo Vocacional']=='No aceptable'].to_excel(writer, sheet_name='No aceptable', index=False)
output.seek(0)

st.download_button(
    label="📥 Descargar Diagnóstico Vocacional",
    data=output,
    file_name="Diagnostico_Vocacional.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

st.subheader("🔍 Vista previa")
st.dataframe(df_final)
