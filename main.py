Entiendo perfectamente, aquí tienes el código completo para que lo puedas copiar y pegar directamente desde este chat. He aplicado los cambios solicitados: eliminé la columna ESTADO y agregué TOTAL, PARTIDA, ACTIVIDAD y CLAVE en la tabla de detalles.

Python
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
        transition: transform 0.2s;
    }
    .print-btn:hover { transform: scale(1.02); }
    .card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .stMetric {
        background: #f8fafc;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #059669;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNCIÓN DE CONEXIÓN A GOOGLE SHEETS ---
def conectar_google_sheets():
    nombre_excel = "trasnsferencias"
    
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    try:
        creds = None
        if "gcp_service_account" in st.secrets:
            creds_info = dict(st.secrets["gcp_service_account"])
            if "private_key" in creds_info:
                creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")
            creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
        elif os.path.exists("credenciales.json"):
            creds = Credentials.from_service_account_file("credenciales.json", scopes=scopes)
        
        if not creds:
            st.error("No se detectaron credenciales de acceso.")
            return None

        client = gspread.authorize(creds)
        spreadsheet = client.open(nombre_excel)
        
        return {
            "mes": spreadsheet.worksheet("MES"),
            "transferencia": spreadsheet.worksheet("Transferencias")
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
        monto = row.get('TRANSFERIR', '0').replace('$', '').replace(',', '')
        
        detalles_html += f"""
        <div style="border: 1px solid #eee; padding: 20px; margin-bottom: 15px; border-radius: 10px; page-break-inside: avoid; background-color: #fff; font-size: 14px;">
            <div style="display: flex; justify-content: space-between; border-bottom: 1px dashed #ccc; padding-bottom: 10px; margin-bottom: 10px;">
                <span style="font-weight: 800; color: #111;">PROVEEDOR: {row.get('PROVEEDOR', 'N/A')}</span>
                <span style="color: #059669; font-weight: bold;">CANTIDAD: ${monto}</span>
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

    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
            body {{ font-family: 'Inter', sans-serif; padding: 40px; color: #333; }}
            .header {{ text-align: center; margin-bottom: 30px; border-bottom: 3px solid #059669; padding-bottom: 10px; }}
            .info-box {{ background: #f3f4f6; padding: 20px; border-radius: 12px; margin-bottom: 30px; display: flex; justify-content: space-between; }}
            h1 {{ color: #065f46; margin: 0; font-size: 24px; text-transform: uppercase; }}
            @media print {{ .no-print {{ display: none; }} body {{ padding: 0; }} }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Orden de Dispersión Bancaria</h1>
            <p>Distrito Sur Fronterizo - SIGEME</p>
        </div>
        <div class="info-box">
            <div><strong>PERIODO:</strong> {mes_row.get('MES', 'N/A')}</div>
            <div><strong>FOLIO:</strong> {mes_row.get('ID', 'N/A')}</div>
            <div><strong>AJUSTE TOTAL:</strong> ${mes_row.get('TOTALAJUSTE', '0')}</div>
        </div>
        {detalles_html}
        <script>
            window.onload = function() {{ 
                setTimeout(function() {{ window.print(); }}, 800); 
            }}
        </script>
    </body>
    </html>
    """
    return html

# --- APP PRINCIPAL ---
def main():
    st.markdown('<div class="main-header"><h1>Gestión de Transferencias</h1><p>Control de Pagos y Dispersión de Fondos</p></div>', unsafe_allow_html=True)

    sheets = conectar_google_sheets()
    if not sheets: return

    with st.spinner("Sincronizando con la nube..."):
        df_mes = obtener_dataframe(sheets["mes"])
        df_trans = obtener_dataframe(sheets["transferencia"])

    if df_mes.empty:
        st.warning("No se encontraron datos en la hoja 'MES'.")
        return

    # Sidebar
    st.sidebar.title("Panel de Control")
    lista_meses = df_mes["MES"].dropna().unique().tolist()
    mes_sel = st.sidebar.selectbox("Seleccione el Mes de Pago", lista_meses)
    
    mes_row = df_mes[df_mes["MES"] == mes_sel].iloc[0]
    id_actual = str(mes_row.get('ID', ''))
    
    # Filtrar transferencias
    trans_del_mes = df_trans[df_trans["ID_MES"].astype(str) == id_actual]

    # Layout superior
    c1, c2 = st.columns([1, 1])
    with c1:
        st.markdown(f"""
        <div class="card">
            <h4 style="margin-top:0; color:#666;">Resumen del Periodo</h4>
            <h2 style="color:#059669; margin:0;">{mes_sel}</h2>
            <p style="margin-bottom:0;">ID de Referencia: <b>{id_actual}</b></p>
        </div>
        """, unsafe_allow_html=True)

    with c2:
        st.markdown("### Reporte de Impresión")
        if not trans_del_mes.empty:
            html_reporte = generar_html_impresion(mes_row, trans_del_mes)
            b64 = base64.b64encode(html_reporte.encode('utf-8')).decode()
            st.markdown(f'<a href="data:text/html;base64,{b64}" target="_blank" class="print-btn">📥 GENERAR PDF DE PAGOS</a>', unsafe_allow_html=True)
        else:
            st.info("No hay registros para este folio.")

    st.markdown("---")
    
    # Tabla y Métricas
    if not trans_del_mes.empty:
        st.subheader(f"Lista de Proveedores - {mes_sel}")
        
        # Selección de columnas según tu solicitud
        columnas_ver = ['PROVEEDOR', 'TOTAL', 'TRANSFERIR', 'PARTIDA', 'ACTIVIDAD', 'BANCO', 'CUENTA', 'CLAVE']
        # Filtramos solo las que existan en el DataFrame para evitar errores
        cols_finales = [c for c in columnas_ver if c in trans_del_mes.columns]
        
        st.dataframe(trans_del_mes[cols_finales], use_container_width=True, hide_index=True)
        
        # Métricas inferiores
        m1, m2, m3 = st.columns(3)
        
        # Limpieza de montos para cálculos
        montos_num = pd.to_numeric(trans_del_mes['TRANSFERIR'].astype(str).str.replace('$','').str.replace(',',''), errors='coerce')
        total_pago = montos_num.sum()
        
        m1.metric("Total de Pagos", len(trans_del_mes))
        m2.metric("Total a Dispersar", f"${total_pago:,.2f}")
        
        # Formatear el ajuste del mes
        ajuste_valor = str(mes_row.get('TOTALAJUSTE','0')).replace(',','')
        try:
            m3.metric("Ajuste Mes", f"${float(ajuste_valor):,.2f}")
        except:
            m3.metric("Ajuste Mes", f"${ajuste_valor}")
    else:
        st.info("No se encontraron transferencias vinculadas a este ID de mes.")

if __name__ == "__main__":
    main()