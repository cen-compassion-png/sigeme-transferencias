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
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    try:
        if not os.path.exists("credenciales.json"):
            st.error("Error: No se encontró el archivo 'credenciales.json'.")
            return None
        
        creds = Credentials.from_service_account_file("credenciales.json", scopes=scopes)
        client = gspread.authorize(creds)
        
        # IMPORTANTE: El nombre debe coincidir exactamente con tu archivo en Drive
        spreadsheet = client.open("transferencias")
        
        return {
            "mes": spreadsheet.worksheet("MES"),
            "proveedor": spreadsheet.worksheet("PROVEEDOR"),
            "transferencia": spreadsheet.worksheet("Transferencia"),
            "partidas": spreadsheet.worksheet("PARTIDAS")
        }
    except Exception as e:
        st.error(f"Error al conectar con Google Sheets: {e}")
        return None

def obtener_dataframe(worksheet):
    data = worksheet.get_all_values()
    if not data: return pd.DataFrame()
    return pd.DataFrame(data[1:], columns=data[0])

# --- GENERADOR DEL REPORTE (HTML PARA IMPRESIÓN) ---
def generar_html_impresion(mes_row, df_detalles):
    """Simula el formato <<Start: [Related Transferencias]>> de AppSheet"""
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

# --- APLICACIÓN PRINCIPAL ---
def main():
    st.markdown('<div class="main-header"><h1>Gestión de Transferencias</h1><p>Emisión Instantánea de Órdenes Bancarias</p></div>', unsafe_allow_html=True)

    sheets = conectar_google_sheets()
    if not sheets:
        st.info("Asegúrate de configurar el archivo 'credenciales.json' y compartir el Excel.")
        return

    with st.spinner("Cargando información..."):
        df_mes = obtener_dataframe(sheets["mes"])
        df_trans = obtener_dataframe(sheets["transferencia"])

    if df_mes.empty:
        st.warning("La pestaña MES está vacía.")
        return

    st.sidebar.header("Menú de Control")
    mes_sel = st.sidebar.selectbox("Seleccione el Periodo", df_mes["MES"].unique().tolist())
    
    # Lógica de relación: ID de MES -> ID_MES en Transferencia
    mes_row = df_mes[df_mes["MES"] == mes_sel].iloc[0]
    trans_del_mes = df_trans[df_trans["ID_MES"] == mes_row["ID"]]

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(f"""
        <div class="card">
            <h3>📅 Periodo: {mes_sel}</h3>
            <p><strong>ID:</strong> {mes_row.get('ID', 'N/A')}</p>
            <h2 style='color:#059669; margin:0;'>Monto Ajuste: ${mes_row.get('TOTALAJUSTE', '0')}</h2>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("### 🖨️ Generar Documento")
        if not trans_del_mes.empty:
            html_reporte = generar_html_impresion(mes_row, trans_del_mes)
            b64 = base64.b64encode(html_reporte.encode('utf-8')).decode()
            st.markdown(f'<a href="data:text/html;base64,{b64}" target="_blank" class="print-btn">🖨️ ABRIR VISTA DE IMPRESIÓN</a>', unsafe_allow_html=True)
        else:
            st.error("No hay transferencias para este mes.")

    st.markdown("---")
    st.subheader("📋 Lista de Transferencias")
    if not trans_del_mes.empty:
        st.dataframe(trans_del_mes[['PROVEEDOR', 'BANCO', 'CUENTA', 'TRANSFERIR', 'ESTADO']], use_container_width=True, hide_index=True)
        
        m1, m2, m3 = st.columns(3)
        total_pago = pd.to_numeric(trans_del_mes['TRANSFERIR'], errors='coerce').sum()
        m1.metric("Cant. Pagos", len(trans_del_mes))
        m2.metric("Total a Dispersar", f"${total_pago:,.2f}")
        m3.metric("Sincronización", "OK")
    else:
        st.info("Sin datos para mostrar.")

if __name__ == "__main__":
    main()