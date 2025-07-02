import streamlit as st
import pandas as pd
import numpy as np
import re
from io import BytesIO

st.set_page_config(layout="wide")

st.title("Diagnóstico Vocacional - Escala CHASIDE")

st.markdown("""
**Tecnológico Nacional de México, Instituto Tecnológico de Colima**  
**Elaborado por:** Dra. Elena Elsa Bricio Barrios, Dr. Santiago Arceo-Díaz y Psicóloga Martha Cecilia Ramírez Guzmán
""")

# 1️⃣ Subir archivo
uploaded_file = st.file_uploader("Sube tu archivo Excel (.xlsx) del test CHASIDE", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.success("Archivo cargado correctamente.")

    # 2️⃣ Convertir Sí/No a 1/0
    columnas_items = [col for col in df.columns if re.match(r'i\d+', col)]
    df[columnas_items] = df[columnas_items].replace(
        {'Sí': 1, 'Si': 1, 'si': 1, 'No': 0, 'no': 0}
    )

    # 3️⃣ Coincidencia sospechosa
    def calcular_coincidencia(fila):
        valores = fila[columnas_items].values
        suma = valores.sum()
        total = len(valores)
        porcentaje_si = suma / total
        porcentaje_no = 1 - porcentaje_si
        return max(porcentaje_si, porcentaje_no)

    df['Coincidencia'] = df.apply(calcular_coincidencia, axis=1)

    # 4️⃣ Suma intereses y aptitudes
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

    for area, items in intereses_items.items():
        df[f'INTERES_{area}'] = df[[f'i{num}' for num in items]].sum(axis=1)
    for area, items in aptitudes_items.items():
        df[f'APTITUD_{area}'] = df[[f'i{num}' for num in items]].sum(axis=1)

    # 5️⃣ Áreas fuertes y ponderadas
    df['Area_Fuerte_Intereses'] = df.apply(
        lambda fila: max(areas, key=lambda a: fila[f'INTERES_{a}']), axis=1
    )
    df['Area_Fuerte_Aptitudes'] = df.apply(
        lambda fila: max(areas, key=lambda a: fila[f'APTITUD_{a}']), axis=1
    )
    df['Area_Fuerte_Total'] = df.apply(
        lambda fila: max(areas, key=lambda a: fila[f'INTERES_{a}'] + fila[f'APTITUD_{a}']), axis=1
    )

    peso_intereses = 0.8
    peso_aptitudes = 0.2

    for area in areas:
        df[f'PUNTAJE_COMBINADO_{area}'] = (
            df[f'INTERES_{area}'] * peso_intereses + df[f'APTITUD_{area}'] * peso_aptitudes
        )

    df['Area_Fuerte_Ponderada'] = df.apply(
        lambda fila: max(areas, key=lambda a: fila[f'PUNTAJE_COMBINADO_{a}']), axis=1
    )

    # 6️⃣ Evaluación de coherencia
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
        carrera_str = str(carrera).strip()
        perfil = perfil_carreras.get(carrera_str)
        if perfil:
            if area in perfil['Fuerte']:
                return 'Coherente'
            elif area in perfil['Baja']:
                return 'Requiere Orientación'
            else:
                return 'Neutral'
        return 'Sin perfil definido'

    df['Coincidencia_Intereses'] = df.apply(
        lambda r: evaluar(r['Area_Fuerte_Intereses'], r['Carrera a ingresar']), axis=1
    )
    df['Coincidencia_Aptitudes'] = df.apply(
        lambda r: evaluar(r['Area_Fuerte_Aptitudes'], r['Carrera a ingresar']), axis=1
    )
    df['Coincidencia_Ambos'] = df.apply(
        lambda r: evaluar(r['Area_Fuerte_Total'], r['Carrera a ingresar']), axis=1
    )
    df['Coincidencia_Ponderada'] = df.apply(
        lambda r: evaluar(r['Area_Fuerte_Ponderada'], r['Carrera a ingresar']), axis=1
    )

    def carrera_mejor(r):
        if r['Coincidencia'] >= 0.75:
            return 'Información no aceptable'
        a = r['Area_Fuerte_Ponderada']
        c_actual = str(r['Carrera a ingresar']).strip()
        s = [c for c, p in perfil_carreras.items() if a in p['Fuerte']]
        return c_actual if c_actual in s else ', '.join(s) if s else 'Sin sugerencia clara'

    def diagnostico(r):
        if r['Carrera_Mejor_Perfilada'] == 'Información no aceptable':
            return 'Información no aceptable'
        if str(r['Carrera a ingresar']).strip() == str(r['Carrera_Mejor_Perfilada']).strip():
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

    # Orden y exportar multi-hoja
    orden = {'Verde': 1, 'Amarillo': 2, 'Rojo': 3, 'Sin sugerencia': 4, 'No aceptable': 5}
    df['Orden_Semaforo'] = df['Semáforo Vocacional'].map(orden).fillna(6)
    df = df.sort_values(by=['Orden_Semaforo']).reset_index(drop=True)

    cols_final = [
        'Nombre del estudiante', 'Carrera a ingresar',
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
        label="Descargar Diagnóstico Vocacional",
        data=output,
        file_name="Diagnostico_Vocacional.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    st.subheader("Tabla resumida")
    st.dataframe(df_final)
