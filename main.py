# ============================================
# 📌 IMPORTS
# ============================================
import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO

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

# ============================================
# 📌 COINCIDENCIA SOSPECHOSA
# ============================================
def calcular_coincidencia(fila):
    valores = fila[columnas_items].values
    suma = valores.sum()
    total = len(valores)
    if total == 0:
        return 0
    porcentaje_si = suma / total
    porcentaje_no = 1 - porcentaje_si
    return max(porcentaje_si, porcentaje_no)

df['Coincidencia'] = df.apply(calcular_coincidencia, axis=1)

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
# 📌 EVALUACIÓN DE COHERENCIA
# ============================================
perfil_carreras = {
    'Arquitectura': {'Fuerte': ['A', 'I'], 'Baja': ['E']},
    'Contador Público': {'Fuerte': ['C', 'H'], 'Baja': ['D']},
    'Licenciatura en Administración': {'Fuerte': ['C', 'H'], 'Baja': ['D']},
    'Ingeniería Ambiental': {'Fuerte': ['E', 'I'], 'Baja': ['A']},
    'Ingeniería Bioquímica': {'Fuerte': ['E', 'I'], 'Baja': ['A', 'S']},
    'Ingeniería en Gestión Empresarial': {'Fuerte': ['C', 'I'], 'Baja': ['A']},
    'Ingeniería Industrial': {'Fuerte': ['I', 'C'], 'Baja': ['A']},
    'Ingeniería en Inteligencia Artificial': {'Fuerte': ['I', 'E'], 'Baja': ['H']},
    'Ingeniería Mecatrónica': {'Fuerte': ['I', 'E'], 'Baja': ['H']},
    'Ingeniería en Sistemas Computacionales': {'Fuerte': ['I', 'E'], 'Baja': ['H']}
}

def evaluar(area, carrera):
    perfil = perfil_carreras.get(str(carrera).strip())
    if perfil:
        if area in perfil['Fuerte']:
            return 'Coherente'
        elif area in perfil['Baja']:
            return 'Requiere Orientación'
        else:
            return 'Neutral'
    return 'Sin perfil definido'

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
    s = [c for c, p in perfil_carreras.items() if a in p['Fuerte']]
    return c_actual if c_actual in s else ', '.join(s) if s else 'Sin sugerencia clara'

def diagnostico(r):
    if r['Carrera_Mejor_Perfilada'] == 'Información no aceptable':
        return 'Información no aceptable'
    if str(r[columna_carrera]).strip() == str(r['Carrera_Mejor_Perfilada']).strip():
        return 'Perfil adecuado'
    else:
        return f"Sugerencia: {r['Carrera_Mejor_Perfilada']}"

def semaforo(r):
    diag = r['Diagnóstico Primario Vocacional']
    if 'Información no aceptable' in diag:
        return 'No aceptable'
    elif 'Sin sugerencia clara' in diag:
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
