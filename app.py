import streamlit as st
from fpdf import FPDF
import base64
import plotly.express as px
import pandas as pd

# ==============================================================================
# 0. CONFIGURACIÓN VISUAL (TECH MODE)
# ==============================================================================
st.set_page_config(
    page_title="AimyWater V48",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: 'Outfit', sans-serif !important;
        background-color: #0e1117 !important;
        color: #e2e8f0 !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d;
    }

    input, .stNumberInput input, .stSelectbox, .stSlider {
        color: #ffffff !important;
        background-color: #0d1117 !important;
    }
    label { color: #00e5ff !important; font-weight: 600 !important; }

    div[data-testid="stMetric"] {
        background-color: #1f2937 !important;
        border: 1px solid #374151 !important;
        border-radius: 10px !important;
        padding: 15px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3) !important;
    }
    div[data-testid="stMetricLabel"] { color: #9ca3af !important; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }

    div.stButton > button:first-child {
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
    }

    .tech-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-left: 4px solid #00e5ff;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .tech-title { color: #00e5ff; font-size: 0.8rem; text-transform: uppercase; font-weight: 700; }
    .tech-value { color: white; font-size: 1.2rem; font-weight: 700; }
    .tech-sub { color: #8b949e; font-size: 0.8rem; }
    
    .alert-box {
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
        font-size: 0.9rem;
        background-color: #422006; 
        border: 1px solid #a16207; 
        color: #fde047;
    }
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
        user = st.text_input("Usuario")
        pwd = st.text_input("Access Key", type="password")
        if st.button("LOGIN", type="primary"):
            if user == "admin" and pwd == "aimywater2025":
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("Acceso denegado")
    return False

if not check_auth(): st.stop()

# ==============================================================================
# 2. LOGICA Y BASE DE DATOS
# ==============================================================================

class EquipoRO:
    def __init__(self, n, prod, ppm, ef, kw):
        self.nombre = n
        self.produccion_nominal = prod
        self.max_ppm = ppm
        self.eficiencia = ef
        self.potencia_kw = kw

class Filtro:
    def __init__(self, tipo, n, bot, caud, wash, sal=0, cap=0):
        self.tipo = tipo
        self.nombre = n
        self.medida_botella = bot
        self.caudal_max = caud
        self.caudal_wash = wash
        self.sal_kg = sal
        self.capacidad = cap

# BASES DE DATOS
ro_db = [
    EquipoRO("PURHOME PLUS", 300, 3000, 0.5, 0.03),
    EquipoRO("DF 800 UV-LED", 3000, 1500, 0.71, 0.08),
    EquipoRO("Direct Flow 1200", 4500, 1500, 0.66, 0.10),
    EquipoRO("ALFA 140", 5000, 2000, 0.5, 0.75),
    EquipoRO("ALFA 240", 10000, 2000, 0.5, 1.1),
    EquipoRO("ALFA 440", 20000, 2000, 0.6, 1.1),
    EquipoRO("AP-6000 LUXE", 18000, 6000, 0.6, 2.2),
]

silex_db = [
    Filtro("Silex", "SIL 10x35", "10x35", 0.8, 2.0),
    Filtro("Silex", "SIL 10x44", "10x44", 0.8, 2.0),
    Filtro("Silex", "SIL 12x48", "12x48", 1.1, 3.0),
    Filtro("Silex", "SIL 18x65", "18x65", 2.6, 6.0),
    Filtro("Silex", "SIL 21x60", "21x60", 3.6, 9.0),
    Filtro("Silex", "SIL 24x69", "24x69", 4.4, 12.0),
    Filtro("Silex", "SIL 30x72", "30x72", 7.0, 18.0),
    Filtro("Silex", "SIL 36x72", "36x72", 10.0, 25.0),
]

carbon_db = [
    Filtro("Carbon", "DEC 30L", "10x35", 0.38, 1.5),
    Filtro("Carbon", "DEC 45L", "10x54", 0.72, 2.0),
    Filtro("Carbon", "DEC 60L", "12x48", 0.80, 2.5),
    Filtro("Carbon", "DEC 75L", "13x54", 1.10, 3.5),
    Filtro("Carbon", "DEC 90KG", "18x65", 2.68, 6.0),
]

descal_db = [
    Filtro("Descal", "BI BLOC 30L", "10x35", 1.8, 2.0, 4.5, 192),
    Filtro("Descal", "BI BLOC 60L", "12x48", 3.6, 3.5, 9.0, 384),
    Filtro("Descal", "TWIN 40L", "10x44", 2.4, 2.5, 6.0, 256),
    Filtro("Descal", "TWIN 100L", "14x65", 6.0, 5.0, 15.0, 640),
    Filtro("Descal", "DUPLEX 300L", "24x69", 6.5, 9.0, 45.0, 1800),
]

def calcular_tuberia(caudal_lh):
    if caudal_lh < 1500: return '3/4"'
    elif caudal_lh < 3000: return '1"'
    elif caudal_lh < 5000: return '1 1/4"'
    elif caudal_lh < 9000: return '1 1/2"'
    else: return '2"'

# --- FUNCIÓN DE CÁLCULO CORREGIDA (ARGUMENTO 'CAUDAL_PUNTA' AÑADIDO) ---
def calcular(origen, modo, consumo, caudal_punta, ppm, dureza, temp, horas, costes, buffer_on, descal_on, man_fin, man_buf):
    res = {}
    msgs = []
    
    fs = 1.2 if origen == "Pozo" else 1.0
    
    # Depósito Final (Usamos caudal punta para cálculo si no es manual, o 75% consumo)
    # Si hay caudal punta alto, el depósito debe ser capaz de amortiguarlo.
    res['v_final'] = man_fin if man_fin > 0 else max(consumo * 0.75, caudal_punta * 60) # Min 1 hora de punta
    
    if modo == "Solo Descalcificación":
        q_target = (consumo / horas) * fs
        cands = [d for d in descal_db if (d.caudal_max * 1000) >= q_target]
        if cands:
            carga = (consumo/1000)*dureza
            validos = [d for d in cands if (d.capacidad/carga if carga>0 else 99) >= 5]
            res['descal'] = validos[0] if validos else cands[-1]
            res['dias'] = res['descal'].capacidad / carga if carga > 0 else 99
            res['sal_anual'] = (365/res['dias']) * res['descal'].sal_kg
            res['opex'] = res['sal_anual'] * costes['sal']
            res['wash'] = res['descal'].caudal_wash * 1000
            res['q_filtros'] = q_target
        else: res['descal'] = None
            
    else: # MODO RO
        tcf = 1.0 if temp >= 25 else max(1.0 - ((25 - temp) * 0.03), 0.1)
        factor_recuperacion = 0.8 if ppm > 2500 else 1.0
        if ppm > 2500: msgs.append("Nota: Eficiencia reducida por alta salinidad.")
        
        # Caudal de producción objetivo (Llenado lento en 'horas')
        q_prod_target = consumo
        
        # Selección RO
        ro_cands = [r for r in ro_db if ppm <= r.max_ppm and ((r.produccion_nominal * tcf / 24) * horas) >= q_prod_target]
        
        if ro_cands:
            res['ro'] = next((r for r in ro_cands if "ALFA" in r.nombre or "AP" in r.nombre), ro_cands[-1]) if consumo > 600 else ro_cands[0]
            res['efi_real'] = res['ro'].eficiencia * factor_recuperacion
            
            # Caudal Producción Real por Hora
            res['q_prod_hora'] = (res['ro'].produccion_nominal * tcf) / 24
            
            # Agua Bruta Necesaria (Diaria)
            agua_in_diaria = consumo / res['efi_real']
            
            # Caudal instantáneo bomba RO
            q_bomba = (res['ro'].produccion_nominal / 24 / res['ro'].eficiencia) * 1.5
            
            if buffer_on:
                q_filtros = (agua_in_diaria / horas) * fs 
                res['v_buffer'] = man_buf if man_buf > 0 else q_bomba * 2
            else:
                q_filtros = q_bomba * fs
                res['v_buffer'] = 0
            
            res['q_filtros'] = q_filtros
            
            # SELECCIÓN EQUIPOS
            sx_cands = [s for s in silex_db if (s.caudal_max * 1000) >= q_filtros]
            res['silex'] = sx_cands[0] if sx_cands else None
            
            cb_cands = [c for c in carbon_db if (c.caudal_max * 1000) >= q_filtros]
            res['carbon'] = cb_cands[0] if cb_cands else None

            if descal_on and dureza > 5:
                ds = [d for d in descal_db if (d.caudal_max*1000) >= q_filtros]
                if ds:
                    carga = (agua_in_diaria/1000)*dureza
                    v = [d for d in ds if (d.capacidad/carga if carga>0 else 99) >= 5]
                    res['descal'] = v[0] if v else ds[-1]
                    res['dias'] = res['descal'].capacidad / carga if carga > 0 else 99
                    res['sal_anual'] = (365/res['dias']) * res['descal'].sal_kg
                    res['wash'] = res['descal'].caudal_wash * 1000
                else: res['descal'] = None
            
            # OPEX
            kwh = (consumo / res['q_prod_hora']) * res['ro'].potencia_kw * 365
            sal = res.get('sal_anual', 0)
            m3 = (agua_in_diaria/1000)*365
            res['opex'] = (kwh*costes['luz']) + (sal*costes['sal']) + (m3*costes['agua'])
            res['breakdown'] = {'Agua': m3*costes['agua'], 'Sal': sal*costes['sal'], 'Luz': kwh*costes['luz']}
            
            w1 = res['silex'].caudal_wash if res.get('silex') else 0
            w2 = res['carbon'].caudal_wash if res.get('carbon') else 0
            w3 = res['descal'].caudal_wash if res.get('descal') else 0
            res['wash'] = max(w1, w2, w3) * 1000
            
        else: res['ro'] = None

    max_flow = max(res.get('q_filtros', 0), res.get('wash', 0))
    res['tuberia'] = calcular_tuberia(max_flow)
    res['msgs'] = msgs
    
    return res

# ==============================================================================
# 3. GENERADOR PDF
# ==============================================================================
def create_pdf(res, inputs, modo):
    pdf = FPDF()
    pdf.add_page()
    try: pdf.image('logo.png', 10, 8, 33)
    except: pass
    pdf.ln(20)
    
    def clean(text):
        if text is None: return "N/A"
        return str(text).encode('latin-1', 'replace').decode('latin-1')
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, clean("INFORME TÉCNICO - AIMYWATER"), 0, 1, 'C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, clean("1. PARAMETROS DE DISEÑO"), 0, 1)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, clean(f"Consumo Objetivo: {inputs['consumo']} L/dia"), 0, 1)
    pdf.cell(0, 8, clean(f"Caudal Punta (Demanda): {inputs['punta']} L/min"), 0, 1)
    if modo == "Planta Completa (RO)":
        pdf.cell(0, 8, clean(f"Salinidad: {inputs['ppm']} ppm | Dureza: {inputs['dureza']} Hf"), 0, 1)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(0, 8, "2. REQUISITOS INSTALACIÓN", 0, 1)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 6, f"ACOMETIDA REQUERIDA: {int(res.get('wash', 0))} L/h a 2.5 bar (Lavado Filtros)")
    pdf.cell(0, 8, clean(f"TUBERIA COLECTOR: {res['tuberia']}"), 0, 1)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, clean("3. EQUIPOS SELECCIONADOS"), 0, 1)
    pdf.set_font("Arial", '', 10)
    
    if modo == "Solo Descalcificación":
        if res.get('descal'):
            pdf.cell(0, 8, clean(f"DESCAL: {res['descal'].nombre} ({res['descal'].medida_botella})"), 0, 1)
    else: 
        if res.get('silex'): pdf.cell(0, 8, clean(f"A. SILEX: {res['silex'].nombre} ({res['silex'].medida_botella})"), 0, 1)
        if res.get('carbon'): pdf.cell(0, 8, clean(f"B. CARBON: {res['carbon'].nombre} ({res['carbon'].medida_botella})"), 0, 1)
        if res.get('v_buffer', 0) > 0: pdf.cell(0, 8, clean(f"C. BUFFER: {int(res['v_buffer'])} Litros"), 0, 1)
        if res.get('descal'): pdf.cell(0, 8, clean(f"D. DESCAL: {res['descal'].nombre} ({res['descal'].medida_botella})"), 0, 1)
        if res.get('ro'): pdf.cell(0, 8, clean(f"E. OSMOSIS: {res['ro'].nombre} ({res['ro'].produccion_nominal} L/dia)"), 0, 1)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, clean("4. ACUMULACIÓN"), 0, 1)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, clean(f"DEPOSITO PRODUCTO FINAL: {int(res['v_final'])} Litros"), 0, 1)
    
    return pdf.output(dest='S').encode('latin-1')

# ==============================================================================
# 4. INTERFAZ
# ==============================================================================

c1, c2 = st.columns([1,5])
with c1:
    try: st.image("logo.png", width=120)
    except: st.warning("Logo?")
with c2:
    st.title("AimyWater Master")
    st.caption("v48.0 Bugfix Edition")

st.divider()

col_sb, col_main = st.columns([1, 2.5])

with col_sb:
    st.subheader("Configuración")
    origen = st.selectbox("Origen", ["Red Pública", "Pozo"])
    modo = st.selectbox("Modo", ["Planta Completa (RO)", "Solo Descalcificación"])
    
    consumo = st.number_input("Consumo Diario (L)", value=2000, step=100)
    # CAUDAL PUNTA (Input necesario para la función corregida)
    caudal_punta = st.number_input("Caudal Punta (L/min)", value=40)
    horas = st.number_input("Horas Prod (Max 22)", value=20, max_value=22)
    
    buffer, descal = False, True
    if modo == "Planta Completa (RO)":
        buffer = st.checkbox("Buffer Intermedio", value=True)
        descal = st.checkbox("Descalcificador", value=True)
    
    ppm = st.number_input("TDS (ppm)", value=800) if "RO" in modo else 0
    dureza = st.number_input("Dureza (Hf)", value=35)
    temp = st.number_input("Temp (C)", value=15) if "RO" in modo else 25
    
    with st.expander("Costes / Manual"):
        ca = st.number_input("Agua €", value=1.5)
        cs = st.number_input("Sal €", value=0.45)
        cl = st.number_input("Luz €", value=0.20)
        mf = st.number_input("Dep Final (L)", value=0)
        mb = st.number_input("Buffer (L)", value=0)
    
    costes = {'agua': ca, 'sal': cs, 'luz': cl}
    
    if st.button("CALCULAR", type="primary", use_container_width=True):
        st.session_state['run'] = True

if st.session_state.get('run'):
    # LLAMADA CORREGIDA: INCLUYE caudal_punta
    res = calcular(origen, modo, consumo, caudal_punta, ppm, dureza, temp, horas, costes, buffer, descal, mf, mb)
    
    if res['msgs']:
        for msg in res['msgs']:
            col_main.markdown(f"<div class='alert-box'>{msg}</div>", unsafe_allow_html=True)

    # VISUALIZACIÓN
    c_tank1, c_tank2 = col_main.columns(2)
    if res.get('v_buffer', 0) > 0:
        c_tank1.markdown(f"<div class='tech-card'><div class='tech-title'>🛡️ Buffer</div><div class='tech-value'>{int(res['v_buffer'])} L</div></div>", unsafe_allow_html=True)
    with c_tank2 if res.get('v_buffer', 0) > 0 else c_tank1:
        c_tank2.markdown(f"<div class='tech-card' style='border-left-color:#2563eb'><div class='tech-title'>🛢️ Depósito Final</div><div class='tech-value'>{int(res['v_final'])} L</div></div>", unsafe_allow_html=True)

    if (modo == "Planta Completa (RO)" and res.get('ro')) or (modo == "Solo Descalcificación" and res.get('descal')):
        col_main.subheader("⚡ Tren de Tratamiento")
        
        cols_eq = col_main.columns(4)
        if modo == "Planta Completa (RO)":
            with cols_eq[0]:
                if res.get('silex'): st.markdown(f"<div class='tech-card'><div class='tech-title'>🪨 Silex</div><div class='tech-sub'>{res['silex'].medida_botella}</div></div>", unsafe_allow_html=True)
            with cols_eq[1]:
                if res.get('carbon'): st.markdown(f"<div class='tech-card'><div class='tech-title'>⚫ Carbón</div><div class='tech-sub'>{res['carbon'].medida_botella}</div></div>", unsafe_allow_html=True)
            with cols_eq[2]:
                if res.get('descal'): st.markdown(f"<div class='tech-card'><div class='tech-title'>🧂 Descal</div><div class='tech-sub'>{res['descal'].medida_botella}</div></div>", unsafe_allow_html=True)
            with cols_eq[3]:
                st.markdown(f"<div class='tech-card' style='border-left-color:#00c6ff'><div class='tech-title'>💧 Ósmosis</div><div class='tech-sub'>{res['ro'].nombre}</div></div>", unsafe_allow_html=True)
        else:
            cols_eq[0].markdown(f"<div class='tech-card'><div class='tech-title'>🧂 Descal</div><div class='tech-value'>{res['descal'].nombre}</div><div class='tech-sub'>{res['descal'].medida_botella}</div></div>", unsafe_allow_html=True)

        col_main.subheader("📐 Datos Técnicos")
        c_tec, c_eco = col_main.columns(2)
        with c_tec:
            st.info(f"**Prod. Horaria:** {int(res.get('q_prod_hora', consumo/horas))} L/h")
            st.warning(f"**Acometida Mínima:** {int(res.get('wash', 0))} L/h")
            st.write(f"Tubería: **{res['tuberia']}**")
            
        with c_eco:
            if modo == "Planta Completa (RO)":
                df = pd.DataFrame(list(res['breakdown'].items()), columns=['Item', 'Coste'])
                fig = px.pie(df, values='Coste', names='Item', hole=0.6, color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", showlegend=False, margin=dict(t=0, b=0, l=0, r=0), height=150)
                st.plotly_chart(fig, use_container_width=True)
            st.metric("OPEX Diario", f"{(res['opex']/365):.2f} €")

        col_main.markdown("---")
        try:
            inputs_pdf = {'consumo': consumo, 'horas': horas, 'origen': origen, 'ppm': ppm, 'dureza': dureza, 'punta': caudal_punta}
            pdf_data = create_pdf(res, inputs_pdf, modo)
            b64 = base64.b64encode(pdf_data).decode()
            col_main.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="informe_aimywater.pdf"><button style="background:#00e5ff;color:black;width:100%;padding:15px;border:none;border-radius:10px;font-weight:bold;">📥 DESCARGAR INFORME PDF</button></a>', unsafe_allow_html=True)
        except Exception as e:
            col_main.error(f"Error PDF: {e}")
            
    else:
        col_main.error("No se encontró solución estándar.")

else:
    col_main.info("👈 Configura los parámetros.")
