# =============================================
# 🚫 NO uses file_uploader()
# =============================================

# 🔗 Leer directamente Google Sheets
url = "https://docs.google.com/spreadsheets/d/1BNAeOSj2F378vcJE5-T8iJ8hvoseOleOHr-I7mVfYu4/export?format=csv"
df = pd.read_csv(url)

st.success("✅ Datos cargados correctamente desde Google Sheets")
st.dataframe(df.head())

# Luego ya sigues con el procesamiento:
# ... convertir Sí/No, cálculos, diagnóstico, exportar ...
