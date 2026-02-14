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
        padding: 2.5rem;
        border-radius: 20px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .print-btn {
        background-color: #059669;
        color: white !important;
        padding: 14px 28px;
        border-radius: 10px;
        text-decoration: none;
        font-weight: bold;
        display: inline-block;
        margin: 10px 0;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN DE CONEXIÓN A GOOGLE SHEETS ---
def conectar_google_sheets():
    # NOMBRE DEL ARCHIVO CORREGIDO: trasnsferencias
    nombre_excel = "trasnsferencias"
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        creds = None
        
        # 1. Intentar cargar desde los Secrets de Streamlit
        if "gcp_service_account" in st.secrets:
            creds_info = dict(st.secrets["gcp_service_account"])
            if "private_key" in creds_info:
                creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
            creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        
        # 2. Intentar cargar desde archivo local
        elif os.path.exists("credenciales.json"):
            creds = Credentials.from_service_account_file("credenciales.json", scopes=scopes)
        
        if not creds:
            st.error("No se detectaron credenciales de acceso.")
            return None

        client = gspread.authorize(creds)
        spreadsheet = client.open(nombre_excel)
        
        return {
            "mes": spreadsheet.worksheet("MES"),
            "proveedor": spreadsheet.worksheet("PROVEEDOR"),
            "transferencia": spreadsheet.worksheet("Transferencia"),
            "partidas": spreadsheet.worksheet("PARTIDAS")
        }
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"⚠️ No se encontró el archivo: '{nombre_excel}'. Revisa el nombre en Google Drive.")
        return None
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
        detalles_html += f"""
        <div style="border: 1px solid #ddd; padding: 15px; margin-bottom: 15px; border-radius: 8px; page-break-inside: avoid; background-color: #fff;">
            <table style="width: 100%; font-size: 13px; border-collapse: collapse;">
                <tr><td colspan="2"><strong>PROVEEDOR:</strong> {row.get('PROVEEDOR', 'N/A')}</td></tr>
                <tr><td><strong>RFC:</strong> {row.get('RFC', 'N/A')}</td><td><strong>BANCO:</strong> {row.get('BANCO', 'N/A')}</td></tr>
                <tr><td><strong>CUENTA:</strong> {row.get('CUENTA', 'N/A')}</td><td><strong>CLAVE:</strong> {row.get('CLAVE', 'N/A')}</td></tr>
                <tr><td><strong>PARTIDA:</strong> {row.get('PARTIDA', 'N/A')}</td><td><strong>ACTIVIDAD:</strong> {row.get('ACTIVIDAD', 'N/A')}</td></tr>
                <tr>
                    <td style="color: #666; padding-top: 10px;">RETENCIÓN ISR: ${row.get('ISR_', '0')}</td>
                    <td style="font-size: 16px; color: #059669; padding-top: 10px;"><strong>TRANSFERIR: ${row.get('TRANSFERIR', '0')}</strong></td>
                </tr>
            </table>
        </div>
        """

    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ font-family: sans-serif; padding: 30px; line-height: 1.5; background-color: white; }}
            .header {{ text-align: center; border-bottom: 4px solid #059669; margin-bottom: 20px; padding-bottom: 10px; }}
            .info-box {{ background: #f9fafb; padding: 15px; border-radius: 8px; margin-bottom: 25px; display: flex; justify-content: space-between; border: 1px solid #eee; }}
            h1 {{ color: #065f46; margin: 0; }}
            @media print {{ .no-print {{ display: none; }} body {{ padding: 0; }} }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>ORDEN DE DISPERSIÓN DE FONDOS</h1>
            <p>Sistema SIGEME - Distrito Sur Fronterizo</p>
        </div>
        <div class="info-box">
            <span><strong>MES:</strong> {mes_row.get('MES', 'N/A')}</span>
            <span><strong>ID REGISTRO:</strong> {mes_row.get('ID', 'N/A')}</span>
            <span><strong>TOTAL AJUSTE:</strong> ${mes_row.get('TOTALAJUSTE', '0')}</span>
        </div>
        {detalles_html}
        <script>
            window.onload = function() {{ 
                setTimeout(function() {{ window.print(); }}, 700); 
            }}
        </script>
    </body>
    </html>
    """
    return html

# --- APP PRINCIPAL ---
def main():
    st.markdown('<div class="main-header"><h1>Gestión de Transferencias</h1><p>Emisión Instantánea de Órdenes Bancarias</p></div>', unsafe_allow_html=True)

    sheets = conectar_google_sheets()
    if not sheets:
        return

    with st.spinner("Sincronizando datos..."):
        df_mes = obtener_dataframe(sheets["mes"])
        df_trans = obtener_dataframe(sheets["transferencia"])

    if df_mes.empty:
        st.warning("No se encontraron registros en la hoja de cálculo.")
        return

    st.sidebar.header("Menú")
    meses = df_mes["MES"].dropna().unique().tolist()
    mes_sel = st.sidebar.selectbox("Seleccione el Periodo", meses)
    
    mes_row = df_mes[df_mes["MES"] == mes_sel].iloc[0]
    trans_del_mes = df_trans[df_trans["ID_MES"] == mes_row["ID"]]

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f"""
        <div class="card">
            <h3>📅 Periodo: {mes_sel}</h3>
            <p><strong>ID Control:</strong> {mes_row.get('ID', 'N/A')}</p>
            <h2 style='color:#059669; margin:0;'>Monto Ajuste: ${mes_row.get('TOTALAJUSTE', '0')}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("### 🖨️ Imprimir Reporte")
        if not trans_del_mes.empty:
            html_reporte = generar_html_impresion(mes_row, trans_del_mes)
            b64 = base64.b64encode(html_reporte.encode('utf-8')).decode()
            st.markdown(f'<a href="data:text/html;base64,{b64}" target="_blank" class="print-btn">🖨️ GENERAR ORDEN DE PAGO</a>', unsafe_allow_html=True)
        else:
            st.info("No hay datos para este periodo.")

    st.markdown("---")
    st.subheader("📋 Detalle de Transferencias")
    if not trans_del_mes.empty:
        columnas = [c for c in ['PROVEEDOR', 'BANCO', 'CUENTA', 'TRANSFERIR', 'ESTADO'] if c in trans_del_mes.columns]
        st.dataframe(trans_del_mes[columnas], use_container_width=True, hide_index=True)
        
        total_pago = pd.to_numeric(trans_del_mes['TRANSFERIR'], errors='coerce').sum()
        st.metric("Total a Dispersar", f"${total_pago:,.2f}")
    else:
        st.info("Tabla vacía para este periodo.")

if __name__ == "__main__":
    main()