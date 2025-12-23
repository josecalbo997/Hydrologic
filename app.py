import streamlit as st
from fpdf import FPDF
import base64
import plotly.express as px
import pandas as pd

# ==============================================================================
# 0. CONFIGURACIÓN VISUAL (TECH EDITION)
# ==============================================================================
st.set_page_config(
    page_title="AimyWater Tech",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS mínimos para tarjetas "Glassmorphism" (Efecto cristal oscuro)
st.markdown("""
<style>
    /* Estilo de Tarjetas Oscuras */
    div[data-testid="stMetric"] {
        background-color: #1f2937 !important; /* Gris Oscuro */
        border: 1px solid #374151 !important;
        border-radius: 10px !important;
        padding: 15px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
    }
    
    /* Textos de métricas */
    div[data-testid="stMetricLabel"] { color: #9ca3af !important; font-size: 0.9rem !important; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; font-weight: 700 !important; }
    
    /* Botones Neón */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        box-shadow: 0 0 15px rgba(0, 114, 255, 0.5) !important;
    }
    
    /* Depósitos Custom */
    .tank-card {
        background-color: #1f2937;
        border: 1px solid #374151;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 20px;
    }
    .tank-title { color: #00e5ff; font-weight: bold; text-transform: uppercase; font-size: 0.9em; letter-spacing: 1px; }
    .tank-val { color: white; font-size: 2em; font-weight: bold; margin: 10px 0; }
    .tank-sub { color: #9ca3af; font-size: 0.8em; }
    
    /* Alertas */
    .stAlert { background-color: #262730 !important; color: white !important; border: 1px solid #374151 !important;}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. SEGURIDAD
# ==============================================================================
def check_auth():
    if "auth" not in st.session_state: st.session_state["auth"] = False
    if st.session_state["auth"]: return True
    
    c1,c2,c3 = st.columns([1,2,1])
    with c2:
        st.markdown("### 🔐 AimyWater Engineering")
        pwd = st.text_input("Access Key", type="password")
        if st.button("LOGIN"):
            # Fallback seguro si no hay secrets
            users = st.secrets.get("users", {"admin": "aimywater2025"})
            if "admin" in users and pwd == users["admin"]:
                st.session_state["auth"] = True
                st.rerun()
            else: st.error("Acceso denegado")
    return False

if not check_auth(): st.stop()

# ==============================================================================
# 2. LÓGICA DE NEGOCIO (MOTORES V25)
# ==============================================================================

class EquipoRO:
    def __init__(self, n, prod, ppm, ef, kw):
        self.nombre = n
        self.produccion_nominal = prod
        self.max_ppm = ppm
        self.eficiencia = ef
        self.potencia_kw = kw

class Descal:
    def __init__(self, n, botella, caudal, cap, sal):
        self.nombre = n
        self.medida_botella = botella
        self.caudal_max = caudal
        self.capacidad = cap
        self.sal_kg = sal

# --- CATÁLOGOS SIMPLIFICADOS ---
ro_db = [
    EquipoRO("PURHOME PLUS", 300, 3000, 0.5, 0.03),
    EquipoRO("DF 800 UV-LED", 3000, 1500, 0.71, 0.08),
    EquipoRO("Direct Flow 1200", 4500, 1500, 0.66, 0.10),
    EquipoRO("ALFA 140", 5000, 2000, 0.5, 0.75),
    EquipoRO("ALFA 240", 10000, 2000, 0.5, 1.1),
    EquipoRO("ALFA 440", 20000, 2000, 0.6, 1.1),
    EquipoRO("ALFA 640", 30000, 2000, 0.6, 2.2),
    EquipoRO("AP-6000 LUXE", 18000, 6000, 0.6, 2.2),
]

descal_db = [
    Descal("BI BLOC 30L", "10x35", 1.8, 192, 4.5),
    Descal("BI BLOC 60L", "12x48", 3.6, 384, 9.0),
    Descal("BI BLOC 100L", "14x65", 6.0, 640, 15.0),
    Descal("TWIN 40L DF", "10x44", 2.4, 256, 6.0),
    Descal("TWIN 100L DF", "14x65", 6.0, 640, 15.0),
    Descal("TWIN 140L DF", "16x65", 6.0, 896, 25.0),
    Descal("DUPLEX 300L", "24x69", 6.5, 1800, 45.0),
]

# --- CÁLCULOS ---
def calcular(modo, consumo, ppm, dureza, temp, horas, costes, buffer_on, descal_on, vol_man_fin, vol_man_buf):
    res = {}
    
    # 1. DEPÓSITOS
    res['v_final'] = vol_man_fin if vol_man_fin > 0 else consumo * 0.75
    res['v_buffer'] = 0
    
    # 2. MODO DESCALCIFICADOR
    if modo == "Solo Descalcificación":
        q_target = consumo / horas
        cands = [d for d in descal_db if (d.caudal_max * 1000) >= q_target]
        if cands:
            # Filtro 5 días
            carga = (consumo/1000)*dureza
            validos = [d for d in cands if (d.capacidad/carga if carga>0 else 99) >= 5]
            res['descal'] = validos[0] if validos else cands[-1] # Fallback al más grande
            res['dias_regen'] = res['descal'].capacidad / carga if carga > 0 else 99
            res['sal_anual'] = (365/res['dias_regen']) * res['descal'].sal_kg
            res['opex'] = res['sal_anual'] * costes['sal']
        else:
            res['descal'] = None
            
    # 3. MODO RO
    else:
        tcf = 1.0 if temp >= 25 else max(1.0 - ((25 - temp) * 0.03), 0.1)
        # Selección RO (Producción diaria en X horas)
        q_day_target = consumo # Asumimos blending 0 para simplificar selección inicial
        ro_cands = [r for r in ro_db if ppm <= r.max_ppm and ((r.produccion_nominal * tcf / 24) * horas) >= q_day_target]
        
        if ro_cands:
            # Prioridad Industrial > Doméstico
            ro_best = next((r for r in ro_cands if "ALFA" in r.nombre or "AP" in r.nombre), ro_cands[-1]) if q_day_target > 600 else ro_cands[0]
            res['ro'] = ro_best
            
            # Balance
            agua_entrada = consumo / ro_best.eficiencia
            q_bomba_ro = (ro_best.produccion_nominal / 24 / ro_best.eficiencia) * 1.5
            
            if buffer_on:
                q_filtros = agua_entrada / 20
                if vol_man_buf > 0: res['v_buffer'] = vol_man_buf
                else: res['v_buffer'] = q_bomba_ro * 2
            else:
                q_filtros = q_bomba_ro
            
            res['q_filtros'] = q_filtros
            
            # Descal (Opcional)
            if descal_on and dureza > 5:
                carga = (agua_entrada/1000)*dureza
                ds = [d for d in descal_db if (d.caudal_max*1000) >= q_filtros]
                if ds:
                    valids = [d for d in ds if (d.capacidad/carga if carga>0 else 99) >= 5]
                    res['descal'] = valids[0] if valids else ds[-1]
                    res['dias_regen'] = res['descal'].capacidad / carga if carga > 0 else 99
                    res['sal_anual'] = (365/res['dias_regen']) * res['descal'].sal_kg
                else: res['descal'] = None
            
            # Opex
            kwh = (consumo / ((ro_best.produccion_nominal * tcf)/24)) * ro_best.potencia_kw * 365
            sal = res.get('sal_anual', 0)
            m3_agua = (agua_entrada/1000)*365
            res['opex'] = (kwh*costes['luz']) + (sal*costes['sal']) + (m3_agua*costes['agua'])
            res['opex_breakdown'] = {'luz': kwh*costes['luz'], 'sal': sal*costes['sal'], 'agua': m3_agua*costes['agua']}
            
        else: res['ro'] = None

    return res

# ==============================================================================
# 3. GENERADOR PDF (Standard)
# ==============================================================================
def create_pdf(res, inputs):
    pdf = FPDF()
    pdf.add_page()
    try: pdf.image('logo.png', 10, 8, 33)
    except: pass
    pdf.ln(20)
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "INFORME TÉCNICO", 0, 1, 'C')
    pdf.ln(10)
    
    # Datos
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. PARAMETROS", 0, 1)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, f"Consumo Objetivo: {inputs['consumo']} L/dia", 0, 1)
    pdf.cell(0, 8, f"Horas Produccion: {inputs['horas']} h", 0, 1)
    pdf.ln(5)
    
    # Equipos
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. EQUIPOS SELECCIONADOS", 0, 1)
    pdf.set_font("Arial", '', 10)
    
    if 'ro' in res and res['ro']:
        pdf.cell(0, 8, f"OSMOSIS: {res['ro'].nombre} ({res['ro'].produccion_nominal} L/d)", 0, 1)
    if 'descal' in res and res['descal']:
        pdf.cell(0, 8, f"DESCALCIFICADOR: {res['descal'].nombre} ({res['descal'].medida_botella})", 0, 1)
    
    # Depósitos
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "3. ACUMULACION", 0, 1)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, f"DEPOSITO FINAL: {int(res['v_final'])} Litros", 0, 1)
    if res['v_buffer'] > 0:
        pdf.cell(0, 8, f"BUFFER INTERMEDIO: {int(res['v_buffer'])} Litros", 0, 1)
        
    return pdf.output(dest='S').encode('latin-1')

# ==============================================================================
# 4. INTERFAZ (DASHBOARD LAYOUT)
# ==============================================================================

# Header
c1, c2 = st.columns([1,5])
with c1:
    try: st.image("logo.png", width=120)
    except: st.warning("Logo?")
with c2:
    st.title("AimyWater Engineering")
    st.caption("v40.0 Stable Release | Dark Tech Edition")

st.divider()

# Layout Principal
col_sidebar, col_main = st.columns([1, 2.5])

# --- SIDEBAR (INPUTS PRECISOS) ---
with col_sidebar:
    st.subheader("🎛️ Panel de Control")
    
    modo = st.selectbox("Modo de Operación", ["Planta Completa (RO)", "Solo Descalcificación"])
    
    with st.expander("1. Hidráulica", expanded=True):
        consumo = st.number_input("Consumo Diario (Litros)", value=2000, step=100)
        horas = st.number_input("Horas de Producción", value=20, min_value=1, max_value=24)
        
        buffer_on = False
        descal_on = True
        if modo == "Planta Completa (RO)":
            buffer_on = st.checkbox("Buffer Intermedio", value=True)
            descal_on = st.checkbox("Descalcificador", value=True)

    with st.expander("2. Calidad Agua", expanded=True):
        dureza = st.number_input("Dureza (ºHf)", value=35)
        ppm = 0
        temp = 25
        if modo == "Planta Completa (RO)":
            ppm = st.number_input("TDS Entrada (ppm)", value=800)
            temp = st.number_input("Temperatura (ºC)", value=15)

    with st.expander("3. Depósitos (Manual)", expanded=False):
        man_fin = st.number_input("Depósito Final (L)", value=0)
        man_buf = st.number_input("Buffer Intermedio (L)", value=0)

    with st.expander("4. Costes (€)", expanded=False):
        c_agua = st.number_input("Agua (€/m3)", value=1.5)
        c_sal = st.number_input("Sal (€/kg)", value=0.45)
        c_luz = st.number_input("Luz (€/kWh)", value=0.20)
    
    costes = {'agua': c_agua, 'sal': c_sal, 'luz': c_luz}
    
    if st.button("CALCULAR SISTEMA", type="primary", use_container_width=True):
        st.session_state['run'] = True

# --- MAIN DASHBOARD ---
if st.session_state.get('run'):
    res = calcular(modo, consumo, ppm, dureza, temp, horas, costes, buffer_on, descal_on, man_fin, man_buf)
    
    # 1. DEPÓSITOS (Visualización destacada)
    c_tank1, c_tank2 = col_main.columns(2)
    
    if res['v_buffer'] > 0:
        c_tank1.markdown(f"""
        <div class="tank-card">
            <div class="tank-title">🛡️ Buffer Intermedio</div>
            <div class="tank-val">{int(res['v_buffer'])} L</div>
            <div class="tank-sub">Alimentación RO</div>
        </div>
        """, unsafe_allow_html=True)
    
    with c_tank2 if res['v_buffer'] > 0 else c_tank1:
        c_tank2.markdown(f"""
        <div class="tank-card" style="border-color: #00e5ff;">
            <div class="tank-title">🛢️ Depósito Final</div>
            <div class="tank-val">{int(res['v_final'])} L</div>
            <div class="tank-sub">Suministro Vivienda</div>
        </div>
        """, unsafe_allow_html=True)

    # 2. EQUIPOS
    if modo == "Planta Completa (RO)":
        if res['ro']:
            col_main.subheader("⚡ Tren de Tratamiento")
            k1, k2, k3 = col_main.columns(3)
            k1.metric("Ósmosis Inversa", res['ro'].nombre)
            if res.get('descal'): k2.metric("Descalcificador", res['descal'].nombre, f"{res['dias_regen']:.1f} días")
            else: k2.metric("Descalcificador", "No incluido")
            k3.metric("Caudal Filtros", f"{int(res['q_filtros'])} L/h")
            
            # Gráfico OPEX
            col_main.subheader("💸 Análisis de Costes")
            co1, co2 = col_main.columns([2,1])
            with co1:
                df = pd.DataFrame(list(res['opex_breakdown'].items()), columns=['Item', 'Coste'])
                fig = px.pie(df, values='Coste', names='Item', hole=0.6, color_discrete_sequence=px.colors.sequential.Teal)
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", showlegend=True)
                st.plotly_chart(fig, use_container_width=True)
            with co2:
                st.metric("Coste Diario", f"{(res['opex']/365):.2f} €")
                st.metric("Sal Anual", f"{int(res.get('sal_anual',0))} Kg")
        else:
            col_main.error("No hay equipo RO viable para estos parámetros.")
            
    else:
        # Solo Descal
        if res['descal']:
            col_main.success(f"✅ Equipo Seleccionado: **{res['descal'].nombre}**")
            col_main.info(f"Configuración: Botella {res['descal'].medida_botella} | Sal: {int(res['sal_anual'])} Kg/año")
        else:
            col_main.error("Caudal demasiado alto para descalcificadores estándar.")

    # 3. DESCARGA
    col_main.markdown("---")
    try:
        pdf_data = create_pdf(res, {'consumo': consumo, 'horas': horas})
        b64 = base64.b64encode(pdf_data).decode()
        col_main.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="informe_aimywater.pdf"><button style="background:#00e5ff;color:black;width:100%;padding:15px;border:none;border-radius:10px;font-weight:bold;">📥 DESCARGAR INFORME TÉCNICO PDF</button></a>', unsafe_allow_html=True)
    except: pass

else:
    col_main.info("👈 Introduce los datos y pulsa CALCULAR.")
