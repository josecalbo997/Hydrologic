import streamlit as st
from fpdf import FPDF
import base64
import plotly.express as px
import pandas as pd
from supabase import create_client, Client
import requests
import tempfile
import math

# ==============================================================================
# 0. CONFIGURACIÓN VISUAL
# ==============================================================================
st.set_page_config(
    page_title="HYDROLOGIC V60",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CONEXIÓN SUPABASE ---
@st.cache_resource
def init_connection():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except: return None

supabase = init_connection()

def local_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');
        
        /* GLOBAL */
        html, body, [class*="css"], [data-testid="stAppViewContainer"] {
            font-family: 'Manrope', sans-serif !important;
            background-color: #f8fafc !important;
            color: #0f172a !important;
        }

        /* SIDEBAR */
        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #cbd5e1;
        }

        /* INPUTS */
        input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
            background-color: #ffffff !important;
            color: #000000 !important;
            border-color: #cbd5e1 !important;
            font-weight: 600 !important;
        }
        label { color: #334155 !important; font-weight: 700 !important; }

        /* TARJETAS MÉTRICAS */
        div[data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
            padding: 15px !important;
            border-radius: 10px !important;
        }
        div[data-testid="stMetricLabel"] { color: #64748b !important; }
        div[data-testid="stMetricValue"] { color: #0f172a !important; font-weight: 800 !important; font-size: 1.6rem !important; }

        /* BOTONES */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
            color: white !important;
            font-weight: 700 !important;
            border-radius: 6px;
        }

        /* ELEMENTOS PERSONALIZADOS */
        .tech-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-left: 4px solid #0ea5e9;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        }
        .tech-title { color: #0ea5e9; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; }
        .tech-value { color: #0f172a; font-size: 1.1rem; font-weight: 800; }
        .tech-sub { color: #64748b; font-size: 0.8rem; }
        
        .tank-card {
            background-color: #f1f5f9;
            border: 1px solid #cbd5e1;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 15px;
        }
        .tank-final { border-bottom: 4px solid #2563eb; background-color: #eff6ff;}
        .tank-raw { border-bottom: 4px solid #475569; background-color: #f8fafc;}
        .tank-val { font-size: 1.5rem; font-weight: 800; color: #0f172a; }
        .tank-label { color: #475569; font-weight: 700; font-size: 0.8rem; text-transform: uppercase; }

        .pump-card {
            background-color: #fff7ed;
            border: 1px solid #ffedd5;
            border-left: 4px solid #f97316;
            padding: 15px;
            border-radius: 8px;
        }
        .pump-val { color: #c2410c; font-weight: 800; font-size: 1.4rem; }
        
        .alert-box {
            background-color: #fffbeb; border: 1px solid #fcd34d; color: #92400e;
            padding: 10px; border-radius: 6px; font-size: 0.9rem; margin-top: 10px;
        }
    </style>
    """, unsafe_allow_html=True)
local_css()

# ==============================================================================
# 1. LOGIN
# ==============================================================================
def check_auth():
    if "auth" not in st.session_state: st.session_state["auth"] = False
    if st.session_state["auth"]: return True
    
    c1,c2,c3 = st.columns([1,2,1])
    with c2:
        st.markdown("<br><div style='text-align: center;'>", unsafe_allow_html=True)
        try: st.image("logo.png", width=160)
        except: pass
        st.markdown("### 🔐 HYDROLOGIC ACCESS")
        st.markdown("</div>", unsafe_allow_html=True)
        
        user = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")
        
        if st.button("ENTRAR", type="primary", use_container_width=True):
            if not supabase:
                # Fallback sin base de datos
                if user == "admin" and pwd == "hydro2025":
                    st.session_state["auth"] = True
                    st.session_state["user_info"] = {"username": "admin", "empresa": "HYDROLOGIC HQ", "rol": "admin", "logo_url": ""}
                    st.rerun()
                else: st.error("Error conexión DB y credenciales incorrectas.")
                return

            try:
                response = supabase.table("usuarios").select("*").eq("username", user).eq("password", pwd).execute()
                if len(response.data) > 0:
                    u = response.data[0]
                    if u["activo"]:
                        st.session_state["auth"] = True
                        st.session_state["user_info"] = u
                        st.rerun()
                    else: st.error("Licencia expirada")
                else: st.error("Credenciales incorrectas")
            except: st.error("Error de conexión")
    return False

if not check_auth(): st.stop()

# ==============================================================================
# 2. LÓGICA DE INGENIERÍA
# ==============================================================================
class EquipoRO:
    def __init__(self, n, prod, ppm, ef, kw):
        self.nombre = n; self.produccion_nominal = prod; self.max_ppm = ppm; self.eficiencia = ef; self.potencia_kw = kw
class Filtro:
    def __init__(self, tipo, n, bot, caud, wash, sal=0, cap=0):
        self.tipo = tipo; self.nombre = n; self.medida_botella = bot; self.caudal_max = caud; self.caudal_wash = wash; self.sal_kg = sal; self.capacidad = cap

# CATÁLOGOS
ro_db = [
    EquipoRO("PURHOME PLUS", 300, 3000, 0.5, 0.03), EquipoRO("DF 800 UV-LED", 3000, 1500, 0.71, 0.08),
    EquipoRO("Direct Flow 1200", 4500, 1500, 0.66, 0.10), EquipoRO("ALFA 140", 5000, 2000, 0.5, 0.75),
    EquipoRO("ALFA 240", 10000, 2000, 0.5, 1.1), EquipoRO("ALFA 440", 20000, 2000, 0.6, 1.1),
    EquipoRO("ALFA 640", 30000, 2000, 0.6, 2.2), EquipoRO("ALFA 840 (Custom)", 40000, 2000, 0.7, 3.0),
    EquipoRO("AP-6000 LUXE", 18000, 6000, 0.6, 2.2),
]
silex_db = [
    Filtro("Silex", "SIL 10x35", "10x35", 0.8, 2.0), Filtro("Silex", "SIL 10x44", "10x44", 0.8, 2.0),
    Filtro("Silex", "SIL 12x48", "12x48", 1.1, 3.5), Filtro("Silex", "SIL 18x65", "18x65", 2.6, 8.0),
    Filtro("Silex", "SIL 21x60", "21x60", 3.6, 11.0), Filtro("Silex", "SIL 24x69", "24x69", 4.4, 14.0),
    Filtro("Silex", "SIL 30x72", "30x72", 7.0, 20.0), Filtro("Silex", "SIL 36x72", "36x72", 10.0, 28.0)
]
carbon_db = [
    Filtro("Carbon", "DEC 30L", "10x35", 0.38, 2.0), Filtro("Carbon", "DEC 45L", "10x54", 0.72, 3.0),
    Filtro("Carbon", "DEC 60L", "12x48", 0.80, 4.0), Filtro("Carbon", "DEC 75L", "13x54", 1.10, 5.0),
    Filtro("Carbon", "DEC 90KG", "18x65", 2.68, 8.0)
]
descal_db = [
    Filtro("Descal", "BI BLOC 30L", "10x35", 1.8, 2.0, 4.5, 192), Filtro("Descal", "BI BLOC 60L", "12x48", 3.6, 3.5, 9.0, 384),
    Filtro("Descal", "TWIN 40L", "10x44", 2.4, 2.5, 6.0, 256), Filtro("Descal", "TWIN 100L", "14x65", 6.0, 5.0, 15.0, 640),
    Filtro("Descal", "DUPLEX 300L", "24x69", 6.5, 9.0, 45.0, 1800)
]

def calcular_bomba(caudal_lh):
    # Estimación de Potencia para 5 Bar (50 m.c.a)
    # HP = (Q * H) / (270 * Eficiencia) aprox.
    # Usamos una tabla heurística para bombas multicelulares estándar
    if caudal_lh < 2000: return "0.75 CV (Multicelular)", 0.55
    elif caudal_lh < 4000: return "1.0 CV (Multicelular)", 0.75
    elif caudal_lh < 6000: return "1.5 CV (Multicelular)", 1.1
    elif caudal_lh < 10000: return "2.0 CV (Multicelular)", 1.5
    elif caudal_lh < 15000: return "3.0 CV (Vertical)", 2.2
    elif caudal_lh < 25000: return "5.5 CV (Vertical)", 4.0
    else: return "7.5 CV (Vertical)", 5.5

def calcular(origen, modo, consumo, caudal_punta, ppm, dureza, temp, horas, costes, descal_on, man_fin, man_raw):
    res = {}
    msgs = []
    
    # 1. DEPÓSITOS
    # Depósito Final: 75% del consumo diario (Buffer para picos)
    res['v_final'] = man_fin if man_fin > 0 else consumo * 0.75
    
    # 2. MODO DESCALCIFICACIÓN
    if modo == "Solo Descalcificación":
        # Llenado lento
        q_target = consumo / horas
        cands = [d for d in descal_db if (d.caudal_max * 1000) >= q_target]
        if cands:
            carga = (consumo/1000)*dureza
            validos = [d for d in cands if (d.capacidad/carga if carga>0 else 99) >= 5]
            res['descal'] = validos[0] if validos else cands[-1]
            res['dias'] = res['descal'].capacidad / carga if carga > 0 else 99
            res['sal_anual'] = (365/res['dias']) * res['descal'].sal_kg
            res['wash'] = res['descal'].caudal_wash * 1000
            res['q_filtros'] = q_target
        else: res['descal'] = None
        
        # Bomba aporte
        q_bomba = max(res.get('q_filtros', 0), res.get('wash', 0))
        res['bomba_nom'], res['bomba_kw'] = calcular_bomba(q_bomba)
        res['v_raw'] = man_raw if man_raw > 0 else res.get('wash', 0) * 0.4 # 24 min de lavado

    # 3. MODO ÓSMOSIS
    else:
        tcf = 1.0 if temp >= 25 else max(1.0 - ((25 - temp) * 0.03), 0.1)
        # Selección RO (Producción en horas)
        ro_cands = [r for r in ro_db if ppm <= r.max_ppm and ((r.produccion_nominal * tcf / 24) * horas) >= consumo]
        
        if ro_cands:
            res['ro'] = next((r for r in ro_cands if "ALFA" in r.nombre or "AP" in r.nombre), ro_cands[-1]) if consumo > 600 else ro_cands[0]
            efi_real = res['ro'].eficiencia * (0.8 if ppm > 2500 else 1.0)
            res['q_prod_hora'] = (res['ro'].produccion_nominal * tcf) / 24
            
            # Agua bruta necesaria
            agua_in = consumo / efi_real
            
            # Caudal instantáneo Bomba RO (Chupón)
            q_bomba_ro_succion = (res['ro'].produccion_nominal / 24 / res['ro'].eficiencia) * 1.5
            
            # Caudal diseño filtros = Max(Llenado Lento, Succión RO si fuera directo)
            # Como tenemos depósito 1, la bomba de aporte alimenta a los filtros a velocidad de la RO
            # OJO: Los filtros se lavan con la bomba de aporte.
            # El caudal de diseño debe ser el de la Bomba de RO para producción.
            res['q_filtros'] = q_bomba_ro_succion
            
            # Selección Equipos
            sx = [s for s in silex_db if (s.caudal_max * 1000) >= res['q_filtros']]
            res['silex'] = sx[0] if sx else None
            
            cb = [c for c in carbon_db if (c.caudal_max * 1000) >= res['q_filtros']]
            res['carbon'] = cb[0] if cb else None
            
            if descal_on and dureza > 5:
                ds = [d for d in descal_db if (d.caudal_max*1000) >= res['q_filtros']]
                if ds:
                    carga = (agua_in/1000)*dureza
                    v = [d for d in ds if (d.capacidad/carga if carga>0 else 99) >= 5]
                    res['descal'] = v[0] if v else ds[-1]
                    res['dias'] = res['descal'].capacidad / carga if carga > 0 else 99
                    res['sal_anual'] = (365/res['dias']) * res['descal'].sal_kg
                else: res['descal'] = None

            # Caudal Máximo Bomba Aporte (Max producción o Max lavado)
            w1 = res['silex'].caudal_wash if res.get('silex') else 0
            w2 = res['carbon'].caudal_wash if res.get('carbon') else 0
            w3 = res['descal'].caudal_wash if res.get('descal') else 0
            res['wash'] = max(w1, w2, w3) * 1000
            
            q_bomba_aporte = max(res['q_filtros'], res['wash'])
            res['bomba_nom'], res['bomba_kw'] = calcular_bomba(q_bomba_aporte)
            
            # Depósito 1 (Agua Bruta)
            # Debe garantizar un lavado completo (aprox 20 min a caudal de lavado)
            res['v_raw'] = man_raw if man_raw > 0 else (res['wash'] * 0.35) # 21 min reserva lavado
            
            # Costes
            kwh_ro = (consumo / res['q_prod_hora']) * res['ro'].potencia_kw * 365
            # Añadir coste bomba aporte (aprox mismas horas que RO + lavados)
            kwh_aporte = (consumo / res['q_filtros']) * res['bomba_kw'] * 365 
            
            sal = res.get('sal_anual', 0)
            m3 = (agua_in/1000)*365
            res['opex'] = ((kwh_ro + kwh_aporte)*costes['luz']) + (sal*costes['sal']) + (m3*costes['agua'])
            res['breakdown'] = {'Agua': m3*costes['agua'], 'Sal': sal*costes['sal'], 'Luz': (kwh_ro+kwh_aporte)*costes['luz']}
            
        else: res['ro'] = None

    return res

# ==============================================================================
# 3. PDF
# ==============================================================================
def create_pdf(res, inputs, modo, user_data):
    pdf = FPDF()
    pdf.add_page()
    try:
        if user_data.get("logo_url"):
            r = requests.get(user_data["logo_url"])
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as t:
                t.write(r.content); pdf.image(t.name, 10, 8, 33)
        else: pdf.image('logo.png', 10, 8, 33)
    except: pass
    pdf.ln(20)
    
    def clean(t): return str(t).encode('latin-1','replace').decode('latin-1') if t else ""
    emp = user_data.get("empresa", "HYDROLOGIC").upper()
    pdf.set_font("Arial", 'B', 16); pdf.cell(0, 10, clean(f"INFORME TÉCNICO - {emp}"), 0, 1, 'C'); pdf.ln(5)
    
    # 1. PARÁMETROS
    pdf.set_fill_color(240, 248, 255); pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "1. BASES DE DISENO", 1, 1, 'L', 1)
    pdf.set_font("Arial", '', 10)
    pdf.cell(95, 8, clean(f"Consumo: {inputs['consumo']} L/dia"), 1)
    pdf.cell(95, 8, clean(f"Caudal Punta: {inputs['punta']} L/min"), 1, 1)
    pdf.ln(5)
    
    # 2. ESQUEMA HIDRÁULICO (LISTADO)
    pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, "2. TREN DE TRATAMIENTO PROPUESTO", 1, 1, 'L', 1)
    pdf.set_font("Arial", '', 10)
    
    # Paso 1: Acumulación Bruta
    pdf.cell(0, 8, clean(f"1. DEPOSITO AGUA BRUTA: {int(res['v_raw'])} Litros (Reserva Lavado)"), 0, 1)
    pdf.cell(0, 8, clean(f"2. BOMBA DE APORTE: {res['bomba_nom']} @ 5 Bar"), 0, 1)
    
    # Paso 2: Filtración
    if res.get('silex'): pdf.cell(0, 8, clean(f"3. FILTRO SILEX: {res['silex'].nombre}"), 0, 1)
    if res.get('carbon'): pdf.cell(0, 8, clean(f"4. DECLORACION: {res['carbon'].nombre}"), 0, 1)
    if res.get('descal'): pdf.cell(0, 8, clean(f"5. DESCALCIFICADOR: {res['descal'].nombre}"), 0, 1)
    
    # Paso 3: Producción
    if res.get('ro'): 
        pdf.cell(0, 8, clean(f"6. OSMOSIS INVERSA: {res['ro'].nombre}"), 0, 1)
        pdf.set_font("Arial", 'I', 9)
        pdf.cell(0, 6, clean(f"   Prod. Nominal: {res['ro'].produccion_nominal} L/d | Real Estimada: {int(res['q_prod_hora']*24)} L/d"), 0, 1)
        pdf.set_font("Arial", '', 10)

    # Paso 4: Acumulación Final
    pdf.ln(2)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 8, clean(f"7. DEPOSITO PRODUCTO FINAL: {int(res['v_final'])} Litros"), 0, 1)
    pdf.ln(5)
    
    # 3. REQUISITOS
    pdf.set_font("Arial", 'B', 11); pdf.cell(0, 8, "3. NOTAS TÉCNICAS", 1, 1, 'L', 1)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 6, clean(f"La bomba de aporte ha sido dimensionada para soportar el caudal de contralavado de los filtros ({int(res.get('wash',0))} L/h). El deposito de agua bruta garantiza el volumen necesario para un ciclo de lavado sin interrupcion."))

    return pdf.output(dest='S').encode('latin-1')

# ==============================================================================
# 4. INTERFAZ
# ==============================================================================
c1, c2 = st.columns([1,5])
with c1:
    try: 
        l = st.session_state["user_info"].get("logo_url")
        if l: st.image(l, width=120)
        else: st.image("logo.png", width=120)
    except: st.warning("Logo?")
with c2:
    emp = st.session_state["user_info"].get("empresa", "HYDROLOGIC")
    st.markdown('<p style="font-size:2.5em;font-weight:800;color:#0f172a;margin:0">HYDROLOGIC</p>', unsafe_allow_html=True)
    st.markdown(f'<p style="color:#64748b;margin-top:-10px">LICENCIA: {emp}</p>', unsafe_allow_html=True)

st.divider()

col_sb, col_main = st.columns([1, 2.5])

with col_sb:
    rol = st.session_state["user_info"].get("rol", "cliente")
    if rol == "admin":
        st.markdown("""<div class="admin-panel">👑 <b>PANEL GESTIÓN</b></div>""", unsafe_allow_html=True)
        with st.expander("Nuevo Usuario"):
            nu = st.text_input("User"); np = st.text_input("Pass"); nc = st.text_input("Empresa"); 
            ul = st.file_uploader("Logo", type=['png','jpg'])
            if st.button("➕ Crear"):
                try:
                    furl = ""
                    if ul:
                        fb = ul.getvalue(); path = f"logos/{nu}_{int(time.time())}.png"
                        supabase.storage.from_("logos").upload(path, fb, {"content-type": "image/png"})
                        furl = supabase.storage.from_("logos").get_public_url(path)
                    supabase.table("usuarios").insert({"username": nu, "password": np, "empresa": nc, "rol": "cliente", "activo": True, "logo_url": furl}).execute()
                    st.success("OK")
                except: st.error("Error")

    if st.button("Cerrar Sesión"): st.session_state["auth"] = False; st.rerun()
    
    st.subheader("Configuración")
    origen = st.selectbox("Origen", ["Red Pública", "Pozo"])
    modo = st.selectbox("Modo", ["Planta Completa (RO)", "Solo Descalcificación"])
    consumo = st.number_input("Consumo (L/día)", value=2000, step=100)
    punta = st.number_input("Caudal Punta (L/min)", value=40)
    horas = st.number_input("Horas Prod", value=20, max_value=24)
    descal = st.checkbox("Descalcificador", value=True) if "RO" in modo else True
    
    ppm = st.number_input("TDS (ppm)", value=800) if "RO" in modo else 0
    dureza = st.number_input("Dureza (Hf)", value=35)
    temp = st.number_input("Temp (C)", value=15) if "RO" in modo else 25
    
    with st.expander("Costes / Manual"):
        ca = st.number_input("Agua €", 1.5); cs = st.number_input("Sal €", 0.45); cl = st.number_input("Luz €", 0.20)
        mf = st.number_input("Dep Final", 0); mr = st.number_input("Dep Bruta", 0)
    
    costes = {'agua': ca, 'sal': cs, 'luz': cl}
    if st.button("CALCULAR", type="primary", use_container_width=True): st.session_state['run'] = True

if st.session_state.get('run'):
    res = calcular(origen, modo, consumo, punta, ppm, dureza, temp, horas, costes, False, descal, mf, mr) # buffer_on siempre False pq ahora usamos deposito bruta
    
    if res.get('ro') or res.get('descal'):
        for msg in res['msgs']: col_main.markdown(f"<div class='alert-box alert-yellow'>{msg}</div>", unsafe_allow_html=True)
        
        # 1. ESQUEMA HIDRÁULICO
        col_main.subheader("📐 Esquema Hidráulico")
        c1, c2, c3, c4 = col_main.columns(4)
        c1.markdown(f"<div class='tank-card tank-raw'><span class='tank-label'>Depósito Entrada</span><div class='tank-val'>{int(res['v_raw'])} L</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='pump-card'><span class='tank-label'>Bomba Aporte</span><div class='pump-val'>{res['bomba_nom']}</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='tech-card'><span class='tech-title'>Caudal Diseño</span><div class='tech-value'>{int(res['q_filtros'])} L/h</div></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='tank-card tank-final'><span class='tank-label'>Depósito Final</span><div class='tank-val'>{int(res['v_final'])} L</div></div>", unsafe_allow_html=True)

        # 2. EQUIPOS
        col_main.subheader("⚡ Equipos")
        eq1, eq2, eq3, eq4 = col_main.columns(4)
        if modo == "Planta Completa (RO)":
            if res.get('silex'): eq1.markdown(f"<div class='tech-card'><div class='tech-title'>SILEX</div><div class='tech-sub'>{res['silex'].medida_botella}</div></div>", unsafe_allow_html=True)
            if res.get('carbon'): eq2.markdown(f"<div class='tech-card'><div class='tech-title'>CARBON</div><div class='tech-sub'>{res['carbon'].medida_botella}</div></div>", unsafe_allow_html=True)
            if res.get('descal'): eq3.markdown(f"<div class='tech-card'><div class='tech-title'>DESCAL</div><div class='tech-sub'>{res['descal'].medida_botella}</div></div>", unsafe_allow_html=True)
            eq4.markdown(f"<div class='tech-card' style='border-left-color:#00c6ff'><div class='tech-title'>OSMOSIS</div><div class='tech-sub'>{res['ro'].nombre}</div></div>", unsafe_allow_html=True)
        else:
            eq1.markdown(f"<div class='tech-card'><div class='tech-title'>DESCAL</div><div class='tech-value'>{res['descal'].nombre}</div></div>", unsafe_allow_html=True)

        # 3. COSTES
        col_main.subheader("💸 Económico")
        cx1, cx2 = col_main.columns(2)
        if modo == "Planta Completa (RO)":
            with cx1:
                df = pd.DataFrame(list(res['breakdown'].items()), columns=['Item', 'Coste'])
                fig = px.pie(df, values='Coste', names='Item', hole=0.6, color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="black", showlegend=False, height=150, margin=dict(t=0,b=0,l=0,r=0))
                st.plotly_chart(fig, use_container_width=True)
            with cx2:
                st.metric("OPEX Diario", f"{(res['opex']/365):.2f} €")
                st.info(f"Caudal Lavado: {int(res['wash'])} L/h")

        # 4. PDF
        col_main.markdown("---")
        try:
            inputs_pdf = {'consumo': consumo, 'horas': horas, 'origen': origen, 'ppm': ppm, 'dureza': dureza, 'punta': caudal_punta}
            pdf_data = create_pdf(res, inputs_pdf, modo, st.session_state["user_info"])
            b64 = base64.b64encode(pdf_data).decode()
            col_main.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="informe_{emp}.pdf"><button style="background:#00e5ff;color:black;width:100%;padding:15px;border:none;border-radius:10px;font-weight:bold;">📥 DESCARGAR INFORME OFICIAL</button></a>', unsafe_allow_html=True)
        except Exception as e: col_main.error(f"Error PDF: {e}")

    else: col_main.error("Sin solución.")
else: col_main.info("👈 Configura el proyecto.")
