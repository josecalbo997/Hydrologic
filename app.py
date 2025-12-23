import streamlit as st
from fpdf import FPDF
import base64
import plotly.express as px
import pandas as pd

# ==============================================================================
# 0. CONFIGURACIÓN VISUAL (DARK TECH MASTER)
# ==============================================================================
st.set_page_config(
    page_title="AimyWater Master V44",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección CSS para forzar Modo Oscuro Tecnológico
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    /* RESET GLOBAL A MODO OSCURO */
    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
        font-family: 'Outfit', sans-serif !important;
        background-color: #0e1117 !important;
        color: #e2e8f0 !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d;
    }

    /* INPUTS */
    input, .stNumberInput input, .stSelectbox, .stSlider {
        color: #ffffff !important;
        background-color: #0d1117 !important;
    }
    label {
        color: #00e5ff !important; /* Azul Neón */
        font-weight: 600 !important;
    }

    /* TARJETAS MÉTRICAS */
    div[data-testid="stMetric"] {
        background-color: #1f2937 !important;
        border: 1px solid #374151 !important;
        border-radius: 10px !important;
        padding: 15px !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
    }
    div[data-testid="stMetricLabel"] { color: #9ca3af !important; }
    div[data-testid="stMetricValue"] { color: #ffffff !important; }

    /* BOTONES */
    div.stButton > button:first-child {
        background: linear-gradient(90deg, #00c6ff 0%, #0072ff 100%) !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        box-shadow: 0 0 15px rgba(0, 114, 255, 0.3) !important;
    }

    /* CARDS PERSONALIZADAS */
    .tech-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-left: 4px solid #00e5ff;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .tech-title { color: #00e5ff; font-size: 0.8rem; text-transform: uppercase; font-weight: 700; }
    .tech-value { color: white; font-size: 1.5rem; font-weight: 700; }
    .tech-sub { color: #8b949e; font-size: 0.8rem; }
    
    /* AVISOS */
    .alert-box {
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
        font-size: 0.9rem;
    }
    .alert-red { background-color: #450a0a; border: 1px solid #991b1b; color: #fecaca; }
    .alert-yellow { background-color: #422006; border: 1px solid #a16207; color: #fde047; }

</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 1. SEGURIDAD (LOGIN DIRECTO)
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
            # Credenciales: admin / aimywater2025
            if user == "admin" and pwd == "aimywater2025":
                st.session_state["auth"] = True
                st.rerun()
            else:
                st.error("Acceso denegado")
    return False

if not check_auth(): st.stop()

# ==============================================================================
# 2. LOGICA
# ==============================================================================

class EquipoRO:
    def __init__(self, n, prod, ppm, ef, kw):
        self.nombre = n
        self.produccion_nominal = prod
        self.max_ppm = ppm
        self.eficiencia = ef
        self.potencia_kw = kw

class Descal:
    def __init__(self, n, bot, caud, cap, sal, wash):
        self.nombre = n
        self.medida_botella = bot
        self.caudal_max = caud
        self.capacidad = cap
        self.sal_kg = sal
        self.caudal_wash = wash # Caudal necesario para contralavado

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
    Descal("BI BLOC 30L", "10x35", 1.8, 2.0, 192, 4.5),
    Descal("BI BLOC 60L", "12x48", 3.6, 3.5, 384, 9.0),
    Descal("TWIN 40L", "10x44", 2.4, 2.5, 256, 6.0),
    Descal("TWIN 100L", "14x65", 6.0, 640, 15.0, 5.0),
    Descal("DUPLEX 300L", "24x69", 6.5, 1800, 45.0, 9.0),
]

def calcular_tuberia(caudal_lh):
    if caudal_lh < 1500: return '3/4"'
    elif caudal_lh < 3000: return '1"'
    elif caudal_lh < 5000: return '1 1/4"'
    elif caudal_lh < 9000: return '1 1/2"'
    elif caudal_lh < 15000: return '2"'
    else: return '2 1/2"'

def calcular(origen, modo, consumo, ppm, dureza, temp, horas, costes, buffer_on, descal_on, man_fin, man_buf):
    res = {}
    msgs = []
    
    factor_seguridad_filtros = 1.2 if origen == "Pozo" else 1.0
    factor_recuperacion = 0.8 if ppm > 2500 else 1.0
    if ppm > 2500: msgs.append("Nota: Eficiencia RO reducida por alta salinidad.")

    res['v_final'] = man_fin if man_fin > 0 else consumo * 0.75
    
    if modo == "Solo Descalcificación":
        q_target = (consumo / horas) * factor_seguridad_filtros
        cands = [d for d in descal_db if (d.caudal_max * 1000) >= q_target]
        if cands:
            carga = (consumo/1000)*dureza
            validos = [d for d in cands if (d.capacidad/carga if carga>0 else 99) >= 5]
            res['descal'] = validos[0] if validos else cands[-1]
            res['dias'] = res['descal'].capacidad / carga if carga > 0 else 99
            res['sal_anual'] = (365/res['dias']) * res['descal'].sal_kg
            res['opex'] = res['sal_anual'] * costes['sal']
            res['wash'] = res['descal'].caudal_wash * 1000
            res['q_filtros'] = q_target # Para cálculo tubería
        else:
            res['descal'] = None
            
    else: # RO
        tcf = 1.0 if temp >= 25 else max(1.0 - ((25 - temp) * 0.03), 0.1)
        q_target = consumo
        
        ro_cands = [r for r in ro_db if ppm <= r.max_ppm and ((r.produccion_nominal * tcf / 24) * horas) >= q_target]
        
        if ro_cands:
            ro_best = next((r for r in ro_cands if "ALFA" in r.nombre or "AP" in r.nombre), ro_cands[-1]) if q_target > 600 else ro_cands[0]
            res['ro'] = ro_best
            
            efi_real = ro_best.eficiencia * factor_recuperacion
            res['efi_real'] = efi_real
            
            agua_in = consumo / efi_real
            q_bomba = (ro_best.produccion_nominal / 24 / ro_best.eficiencia) * 1.5 # Caudal instantáneo bomba
            
            if buffer_on:
                q_filtros = (agua_in / 20) * factor_seguridad_filtros
                res['v_buffer'] = man_buf if man_buf > 0 else q_bomba * 2
            else:
                q_filtros = q_bomba * factor_seguridad_filtros
                res['v_buffer'] = 0
            
            res['q_filtros'] = q_filtros
            
            if descal_on and dureza > 5:
                carga = (agua_in/1000)*dureza
                ds = [d for d in descal_db if (d.caudal_max*1000) >= q_filtros]
                if ds:
                    v = [d for d in ds if (d.capacidad/carga if carga>0 else 99) >= 5]
                    res['descal'] = v[0] if v else ds[-1]
                    res['dias'] = res['descal'].capacidad / carga if carga > 0 else 99
                    res['sal_anual'] = (365/res['dias']) * res['descal'].sal_kg
                    res['wash'] = res['descal'].caudal_wash * 1000
                else: res['descal'] = None
            
            kwh = (consumo / ((ro_best.produccion_nominal * tcf)/24)) * ro_best.potencia_kw * 365
            sal = res.get('sal_anual', 0)
            m3 = (agua_in/1000)*365
            res['opex'] = (kwh*costes['luz']) + (sal*costes['sal']) + (m3*costes['agua'])
            res['breakdown'] = {'Agua': m3*costes['agua'], 'Sal': sal*costes['sal'], 'Luz': kwh*costes['luz']}
            
        else: res['ro'] = None

    max_flow = max(res.get('q_filtros', 0), res.get('wash', 0))
    res['tuberia'] = calcular_tuberia(max_flow)
    res['msgs'] = msgs
    
    return res

# ==============================================================================
# 3. GENERADOR PDF (BLINDADO)
# ==============================================================================
def create_pdf(res, inputs, modo):
    pdf = FPDF()
    pdf.add_page()
    
    # Intento de logo seguro
    try: pdf.image('logo.png', 10, 8, 33)
    except: pass
    pdf.ln(20)
    
    # Función para limpiar textos (Anti-Emojis y caracteres raros)
    def clean(text):
        if text is None: return "N/A"
        return str(text).encode('latin-1', 'replace').decode('latin-1')
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, clean("INFORME TÉCNICO - AIMYWATER"), 0, 1, 'C')
    pdf.ln(10)
    
    # 1. PARAMETROS
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, clean("1. PARÁMETROS DE DISEÑO"), 0, 1)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, clean(f"Consumo Objetivo: {inputs['consumo']} L/dia"), 0, 1)
    pdf.cell(0, 8, clean(f"Origen Agua: {inputs['origen']}"), 0, 1)
    pdf.cell(0, 8, clean(f"Dureza: {inputs['dureza']} Hf"), 0, 1) # Asegurar dureza se imprime
    
    if modo == "Planta Completa (RO)":
        pdf.cell(0, 8, clean(f"Salinidad Entrada: {inputs['ppm']} ppm"), 0, 1)
    pdf.ln(5)
    
    # 2. EQUIPOS
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, clean("2. SOLUCION PROPUESTA"), 0, 1)
    pdf.set_font("Arial", '', 10)
    
    if modo == "Solo Descalcificación":
        if res.get('descal'):
            pdf.cell(0, 8, clean(f"DESCALCIFICADOR: {res['descal'].nombre}"), 0, 1)
            pdf.cell(0, 8, clean(f"  Botella: {res['descal'].medida_botella}"), 0, 1)
            pdf.cell(0, 8, clean(f"  Regeneracion: Cada {res['dias']:.1f} dias"), 0, 1)
        else:
            pdf.cell(0, 8, clean("No se seleccionó descalcificador."), 0, 1)
    else: # Planta Completa (RO)
        if res.get('ro'):
            pdf.cell(0, 8, clean(f"OSMOSIS: {res['ro'].nombre} ({res['ro'].produccion_nominal} L/d)"), 0, 1)
            pdf.cell(0, 8, clean(f"  Eficiencia: {int(res['efi_real']*100)}%"), 0, 1)
            
        if res.get('descal'):
            pdf.cell(0, 8, clean(f"DESCALCIFICADOR: {res['descal'].nombre}"), 0, 1)
            pdf.cell(0, 8, clean(f"  Botella: {res['descal'].medida_botella}"), 0, 1)
            pdf.cell(0, 8, clean(f"  Regeneracion: Cada {res['dias']:.1f} dias"), 0, 1)
        else:
            pdf.cell(0, 8, clean("Descalcificador: No incluido/requerido."), 0, 1)
    
    # 3. INSTALACION
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, clean("3. REQUISITOS DE INSTALACIÓN Y ACUMULACIÓN"), 0, 1)
    pdf.set_font("Arial", '', 10)
    
    pdf.cell(0, 8, clean(f"DEPOSITO FINAL REQUERIDO: {int(res['v_final'])} Litros"), 0, 1)
    
    if res.get('v_buffer', 0) > 0:
        pdf.cell(0, 8, clean(f"BUFFER INTERMEDIO REQUERIDO: {int(res['v_buffer'])} Litros"), 0, 1)
        
    pdf.set_text_color(200, 0, 0)
    pdf.cell(0, 8, clean(f"ACOMETIDA MINIMA: {int(res.get('wash', 0))} L/h a 2.5 bar"), 0, 1)
    pdf.cell(0, 8, clean(f"TUBERIA COLECTORA RECOMENDADA: {res['tuberia']}"), 0, 1)
    pdf.set_text_color(0, 0, 0) # Volver a negro
        
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
    st.caption("v43.0 Final Release")

st.divider()

col_sb, col_main = st.columns([1, 2.5])

with col_sb:
    st.subheader("Configuración")
    
    origen = st.selectbox("Origen del Agua", ["Red Pública", "Pozo"])
    modo = st.selectbox("Modo de Diseño", ["Planta Completa (RO)", "Solo Descalcificación"])
    
    with st.expander("1. Hidráulica", expanded=True):
        consumo = st.number_input("Consumo Diario (L)", value=2000, step=100)
        horas = st.number_input("Horas Prod", value=20, min_value=1, max_value=24)
        
        buffer_on = False
        descal_on = True
        if modo == "Planta Completa (RO)":
            buffer_on = st.checkbox("Buffer Intermedio", value=True)
            descal_on = st.checkbox("Incluir Descalcificador", value=True)
        else: # Solo Descalcificación
            buffer_on = False # Desactivar siempre en este modo
            descal_on = True # Forzar siempre ON para descalcificación

    with st.expander("2. Calidad Agua"):
        dureza = st.number_input("Dureza (ºHf)", value=35)
        ppm = st.number_input("TDS (ppm)", value=800) if "RO" in modo else 0
        temp = st.number_input("Temp (C)", value=15) if "RO" in modo else 25

    with st.expander("3. Depósitos (Personalizar)"):
        st.caption("Deja en 0 para cálculo automático.")
        mf = st.number_input("Depósito Final (L)", value=0)
        mb = st.number_input("Buffer Intermedio (L)", value=0) if buffer_on else 0 # Solo si buffer ON

    with st.expander("4. Costes Unitarios"):
        ca = st.number_input("Agua €/m3", value=1.5)
        cs = st.number_input("Sal €/kg", value=0.45)
        cl = st.number_input("Luz €/kWh", value=0.20)
        costes = {'agua': ca, 'sal': cs, 'luz': cl}
        
    if st.button("CALCULAR SISTEMA", type="primary", use_container_width=True):
        st.session_state['run'] = True

# Dashboard
if st.session_state.get('run'):
    res = calcular(origen, modo, consumo, ppm, dureza, temp, horas, costes, buffer_on, descal_on, mf, mb)
    
    if res['msgs']:
        for msg in res['msgs']:
            col_main.markdown(f"<div class='alert-box alert-yellow'>{msg}</div>", unsafe_allow_html=True)
    
    # 1. DEPÓSITOS
    c_tank1, c_tank2 = col_main.columns(2)
    if res.get('v_buffer', 0) > 0:
        c_tank1.markdown(f"<div class='tech-card'><div class='tech-title'>🛡️ Buffer</div><div class='tech-value'>{int(res['v_buffer'])} L</div></div>", unsafe_allow_html=True)
    with c_tank2 if res.get('v_buffer', 0) > 0 else c_tank1:
        c_tank2.markdown(f"<div class='tech-card' style='border-left-color:#2563eb'><div class='tech-title'>🛢️ Depósito Final</div><div class='tech-value'>{int(res['v_final'])} L</div></div>", unsafe_allow_html=True)

    # 2. EQUIPOS
    if (modo == "Planta Completa (RO)" and res.get('ro')) or (modo == "Solo Descalcificación" and res.get('descal')):
        col_main.subheader("⚡ Equipos Seleccionados")
        k1, k2, k3 = col_main.columns(3)
        
        if res.get('ro'): k1.metric("Ósmosis", res['ro'].nombre)
        elif res.get('descal'): k1.metric("Equipo Principal", res['descal'].nombre)
        
        if res.get('descal'): k2.metric("Descalcificador", f"{res['descal'].medida_botella}", f"{res['dias']:.1f} días")
        else: k2.metric("Descalcificador", "No incluido")
        
        k3.metric("Tubería Mínima", res['tuberia'])
        
        # 3. GRÁFICO OPEX (Solo RO)
        if modo == "Planta Completa (RO)":
            col_main.subheader("💸 Análisis Económico")
            xc1, xc2 = col_main.columns([2,1])
            with xc1:
                df = pd.DataFrame(list(res['breakdown'].items()), columns=['Concepto', 'Coste'])
                fig = px.pie(df, values='Coste', names='Concepto', hole=0.6, color_discrete_sequence=px.colors.sequential.Teal)
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="white", showlegend=True, margin=dict(t=0, b=0, l=0, r=0))
                st.plotly_chart(fig, use_container_width=True)
            with xc2:
                st.metric("Coste Diario Total", f"{(res['opex']/365):.2f} €")
                st.metric("Consumo Sal", f"{int(res.get('sal_anual',0))} Kg/año")

        # 4. DOWNLOAD PDF
        col_main.markdown("---")
        try:
            inputs_pdf = {'consumo': consumo, 'horas': horas, 'origen': origen, 'ppm': ppm, 'dureza': dureza} # Pasar dureza al PDF
            pdf_data = create_pdf(res, inputs_pdf, modo)
            b64 = base64.b64encode(pdf_data).decode()
            col_main.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="informe_aimywater.pdf"><button style="background:#00e5ff;color:black;width:100%;padding:15px;border:none;border-radius:10px;font-weight:bold;">📥 DESCARGAR INFORME TÉCNICO PDF</button></a>', unsafe_allow_html=True)
        except Exception as e:
            col_main.error(f"Error al generar PDF: {e}")
            
    else:
        col_main.error("No se encontró solución estándar. Contactar ingeniería.")

else:
    col_main.info("👈 Configura el proyecto en el menú lateral.")
