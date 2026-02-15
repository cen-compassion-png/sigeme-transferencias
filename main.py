Entiendo perfectamente. Mil disculpas por las vueltas, voy a pegar el código como texto plano directamente aquí abajo para que no se oculte en ninguna ventana y puedas copiarlo de inmediato.

Aquí tienes el código de main.py:

import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import base64
import os

--- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
page_title="SIGEME - Gestión de Transferencias",
page_icon="💸",
layout="wide"
)

--- ESTILOS VISUALES (CSS) ---
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

.main-header {
    background: linear-gradient(135deg, #065f46 0%, #059669 100%);
    padding: 2rem;
    border-radius: 20px;
    color: white;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
}

.print-btn {
    background-color: #059669;
    color: white !important;
    padding: 12px 24px;
    border-radius: 10px;
    text-decoration: none;
    font-weight: bold;
    display: inline-block;
    text-align: center;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    width: 100%;
    margin-top: 28px;
    cursor: pointer;
    border: none;
}

.highlight-box {
    background-color: #fff7ed;
    padding: 15px;
    border-radius: 10px;
    border: 2px solid #fb923c;
    margin-top: 10px;
}
</style>
""", unsafe_allow_html=True)
--- FUNCIÓN DE CONEXIÓN A GOOGLE SHEETS ---
def conectar_google_sheets():
nombre_excel = "trasnsferencias"
scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]

try:
    creds = None
    if "gcp_service_account" in st.secrets:
        creds_info = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_info:
            creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
        creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    elif os.path.exists("credenciales.json"):
        creds = Credentials.from_service_account_file("credenciales.json", scopes=scopes)
    
    if not creds: return None
    client = gspread.authorize(creds)
    spreadsheet = client.open(nombre_excel)
    
    return {
        "mes": spreadsheet.worksheet("MES"),
        "transferencia": spreadsheet.worksheet("Transferencias"),
        "proveedores": spreadsheet.worksheet("PROVEEDOR")
    }
except Exception as e:
    st.error(f"❌ Error de conexión: {str(e)}")
    return None
def obtener_dataframe(worksheet):
try:
data = worksheet.get_all_values()
if not data: return pd.DataFrame()
return pd.DataFrame(data[1:], columns=data[0])
except:
return pd.DataFrame()

--- GENERADOR DEL REPORTE HTML PARA PDF ---
def generar_html_impresion(mes_row, df_detalles):
detalles_html = ""
for _, row in df_detalles.iterrows():
monto = row.get('TRANSFERIR', '0')
detalles_html += f"""
<div style="border: 1px solid #eee; padding: 20px; margin-bottom: 15px; border-radius: 10px; page-break-inside: avoid; background-color: #fff; font-size: 14px;">
<div style="display: flex; justify-content: space-between; border-bottom: 1px dashed #ccc; padding-bottom: 10px; margin-bottom: 10px;">
<span style="font-weight: 800; color: #111; font-size: 16px;">PROVEEDOR: {row.get('NOMBRE_REAL', 'N/A')}</span>
<span style="color: #059669; font-weight: bold; font-size: 16px;">TRANSFERIR: ${monto}</span>
</div>
<table style="width: 100%; border-collapse: collapse; line-height: 1.6;">
<tr>
<td style="width: 50%;"><strong>RFC:</strong> {row.get('RFC', 'N/A')}</td>
<td><strong>BANCO:</strong> {row.get('BANCO', 'N/A')}</td>
</tr>
<tr>
<td><strong>CUENTA:</strong> {row.get('CUENTA', 'N/A')}</td>
<td><strong>CLAVE:</strong> {row.get('CLAVE', 'N/A')}</td>
</tr>
<tr>
<td><strong>PARTIDA:</strong> {row.get('PARTIDA', 'N/A')}</td>
<td><strong>ACTIVIDAD:</strong> {row.get('ACTIVIDAD', 'N/A')}</td>
</tr>
</table>
</div>
"""

full_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: sans-serif; padding: 30px; color: #333; }}
        .btn-print {{ background: #059669; color: white; padding: 15px 30px; border-radius: 8px; cursor: pointer; border: none; font-weight: bold; width: 100%; margin-bottom: 20px; }}
        .header-info {{ border-bottom: 3px solid #059669; margin-bottom: 20px; padding-bottom: 10px; }}
        @media print {{ .btn-print {{ display: none; }} body {{ padding: 0; }} }}
    </style>
</head>
<body>
    <button class="btn-print" onclick="window.print()">🖨️ CLIC AQUÍ PARA IMPRIMIR O GUARDAR PDF</button>
    <div class="header-info">
        <h2 style="margin:0; color:#065f46;">Orden de Dispersión - SIGEME</h2>
        <p><strong>Periodo:</strong> {mes_row.get('MES', 'N/A')} | <strong>ID Folio:</strong> {mes_row.get('ID', 'N/A')}</p>
    </div>
    {detalles_html}
</body>
</html>
"""
return full_html
--- APP PRINCIPAL ---
def main():
st.markdown('<div class="main-header"><h1>Gestión de Transferencias</h1><p>Sistema SIGEME</p></div>', unsafe_allow_html=True)

sheets = conectar_google_sheets()
if not sheets: return

with st.spinner("Sincronizando información..."):
    df_mes = obtener_dataframe(sheets["mes"])
    df_trans = obtener_dataframe(sheets["transferencia"])
    df_prov = obtener_dataframe(sheets["proveedores"])

if df_mes.empty or df_trans.empty or df_prov.empty:
    st.warning("Verifique las pestañas MES, Transferencias y PROVEEDOR.")
    return

# --- CRUCE DE DATOS: ID -> NOMBRE REAL ---
df_prov_map = df_prov[['ID', 'PROVEEDOR']].rename(columns={'PROVEEDOR': 'NOMBRE_REAL'})
df_trans = df_trans.merge(df_prov_map, left_on='PROVEEDOR', right_on='ID', how='left')

# --- PANEL DE CONTROL ---
st.markdown("### ⚙️ Panel de Control")
col_sel, col_btn = st.columns([2, 1])

with col_sel:
    lista_meses = df_mes["MES"].dropna().unique().tolist()
    lista_meses.reverse()
    mes_sel = st.selectbox("Seleccione el Mes de Ofrenda", lista_meses)

mes_row = df_mes[df_mes["MES"] == mes_sel].iloc[0]
id_actual = str(mes_row.get('ID', ''))
trans_del_mes = df_trans[df_trans["ID_MES"].astype(str) == id_actual].copy()

with col_btn:
    if not trans_del_mes.empty:
        html_content = generar_html_impresion(mes_row, trans_del_mes)
        b64_html = base64.b64encode(html_content.encode('utf-8')).decode()
        href = f'<a href="data:text/html;base64,{b64_html}" target="_blank" class="print-btn">📂 GENERAR PDF DE PAGOS</a>'
        st.markdown(href, unsafe_allow_html=True)

st.markdown("---")

# --- TABLA DE RESULTADOS ---
st.subheader("📋 Lista de Transferencias")

if not trans_del_mes.empty:
    columnas_orden = ['NOMBRE_REAL', 'RFC', 'BANCO', 'CUENTA', 'CLAVE', 'PARTIDA', 'ACTIVIDAD', 'TOTAL', 'TRANSFERIR']
    cols_finales = [c for c in columnas_orden if c in trans_del_mes.columns]
    
    df_final = trans_del_mes[cols_finales].copy().rename(columns={'NOMBRE_REAL': 'PROVEEDOR'})

    def highlight_transferir(s):
        return ['background-color: #fb923c; color: white; font-weight: bold' if s.name == 'TRANSFERIR' else '' for _ in s]

    st.dataframe(df_final.style.apply(highlight_transferir, axis=0), use_container_width=True, hide_index=True)
    
    # Resumen de total
    montos = pd.to_numeric(df_final['TRANSFERIR'].astype(str).str.replace('$','').str.replace(',',''), errors='coerce')
    st.markdown(f"""
        <div class="highlight-box">
            <span style="color: #9a3412; font-size: 1.3rem;"><b>Total a Transferir ({mes_sel}):</b> ${montos.sum():,.2f}</span>
        </div>
    """, unsafe_allow_html=True)
else:
    st.info("No hay datos registrados para este periodo.")
if name == "main":
main()