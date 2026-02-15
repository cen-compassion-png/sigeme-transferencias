import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import base64
import os

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="SIGEME - Gestión de Transferencias",
    page_icon="💸",
    layout="wide"
)

# --- ESTILOS VISUALES (CSS) ---
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

# --- FUNCIÓN DE CONEXIÓN A GOOGLE SHEETS ---
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

# --- GENERADOR DEL REPORTE HTML ---
def generar_html_impresion(mes_row, df_detalles):
    detalles_html = ""
    for _, row in df_detalles.iterrows():
        monto = row.get('TRANSFERIR', '0')
        detalles_html += f"""
        <div style="border: 1px solid #eee; padding: 20px; margin-bottom: 15px; border-radius: 10px; page-break-inside: avoid; background-color: #fff; font-size: 14px;">
            <div style="display: flex; justify-content: space-between; border-bottom: 1px dashed #ccc; padding-bottom: 10px; margin-bottom: 10px;">
                <span style="font-weight: 800; color: #111;">PROVEEDOR: {row.get('NOMBRE_REAL', 'N/A')}</span>
                <span style="color: #059669; font-weight: bold;">TRANSFERIR: ${monto}</span>
            </div>
            <table style="width: 100%; border-collapse: collapse;">
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
    return f"<html><body style='font-family:sans-serif;padding:40px;'>{detalles_html}</body></html>"

# --- APP PRINCIPAL ---
def main():
    st.markdown('<div class="main-header"><h1>Gestión de Transferencias</h1><p>Sistema SIGEME</p></div>', unsafe_allow_html=True)

    sheets = conectar_google_sheets()
    if not sheets: return

    with st.spinner("Cargando información de proveedores y transferencias..."):
        df_mes = obtener_dataframe(sheets["mes"])
        df_trans = obtener_dataframe(sheets["transferencia"])
        df_prov = obtener_dataframe(sheets["proveedores"])

    if df_mes.empty or df_trans.empty or df_prov.empty:
        st.warning("Verifique que las pestañas MES, Transferencias y PROVEEDOR tengan datos.")
        return

    # --- LÓGICA DE CRUCE: TRADUCIR ID A NOMBRE REAL ---
    # En la pestaña PROVEEDOR, buscamos 'ID' y 'PROVEEDOR' (Nombre)
    df_prov_lookup = df_prov[['ID', 'PROVEEDOR']].rename(columns={'PROVEEDOR': 'NOMBRE_REAL'})
    
    # En Transferencias, usamos la columna 'PROVEEDOR' (que contiene el ID) para el cruce
    df_trans = df_trans.merge(
        df_prov_lookup, 
        left_on='PROVEEDOR', 
        right_on='ID', 
        how='left',
        suffixes=('', '_lookup')
    )

    # --- PANEL DE CONTROL (SUPERIOR) ---
    st.markdown("### ⚙️ Panel de Control")
    col_sel, col_btn = st.columns([2, 1])
    
    with col_sel:
        lista_meses = df_mes["MES"].dropna().unique().tolist()
        lista_meses.reverse() # Más reciente a antiguo
        mes_sel = st.selectbox("Seleccione el Mes de Ofrenda", lista_meses)
    
    mes_row = df_mes[df_mes["MES"] == mes_sel].iloc[0]
    id_actual = str(mes_row.get('ID', ''))
    trans_del_mes = df_trans[df_trans["ID_MES"].astype(str) == id_actual].copy()

    with col_btn:
        if not trans_del_mes.empty:
            html_reporte = generar_html_impresion(mes_row, trans_del_mes)
            b64 = base64.b64encode(html_reporte.encode('utf-8')).decode()
            st.markdown(f'<a href="data:text/html;base64,{b64}" target="_blank" class="print-btn">📥 GENERAR PDF DE PAGOS</a>', unsafe_allow_html=True)

    st.markdown("---")

    # --- LISTA DE TRANSFERENCIAS ---
    st.subheader("📋 Lista de Transferencias")
    
    if not trans_del_mes.empty:
        # Definimos el orden solicitado incluyendo RFC e insertando el nombre real
        # Orden: PROVEEDOR (Nombre Real), RFC, BANCO, CUENTA, CLAVE, PARTIDA, ACTIVIDAD, TOTAL, TRANSFERIR
        columnas_orden = ['NOMBRE_REAL', 'RFC', 'BANCO', 'CUENTA', 'CLAVE', 'PARTIDA', 'ACTIVIDAD', 'TOTAL', 'TRANSFERIR']
        cols_finales = [c for c in columnas_orden if c in trans_del_mes.columns]
        
        df_final = trans_del_mes[cols_finales].copy()
        
        # Renombramos visualmente para el usuario
        df_final = df_final.rename(columns={'NOMBRE_REAL': 'PROVEEDOR'})

        # Función para resaltar la columna TRANSFERIR en color naranja
        def highlight_transferir(s):
            return ['background-color: #fb923c; color: white; font-weight: bold' if s.name == 'TRANSFERIR' else '' for _ in s]

        st.dataframe(
            df_final.style.apply(highlight_transferir, axis=0),
            use_container_width=True, 
            hide_index=True
        )
        
        # Resumen monetario al final
        montos_num = pd.to_numeric(df_final['TRANSFERIR'].astype(str).str.replace('$','').str.replace(',',''), errors='coerce')
        total_acumulado = montos_num.sum()
        st.markdown(f"""
            <div class="highlight-box">
                <span style="color: #9a3412; font-size: 1.3rem;"><b>Total Real a Transferir en {mes_sel}:</b> ${total_acumulado:,.2f}</span>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No hay transferencias registradas para este periodo.")

if __name__ == "__main__":
    main()