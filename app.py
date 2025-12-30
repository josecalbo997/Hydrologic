import streamlit as st
from fpdf import FPDF
import base64
import plotly.express as px
import pandas as pd
from supabase import create_client, Client
import requests
import tempfile
import math
import time
from PIL import Image

# ==============================================================================
# 0. CONFIGURACIÓN VISUAL
# ==============================================================================
st.set_page_config(
    page_title="HYDROLOGIC V73",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CONEXIÓN SUPABASE
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
        
        html, body, [class*="css"], [data-testid="stAppViewContainer"] {
            font-family: 'Manrope', sans-serif !important;
            background-color: #f8fafc !important;
            color: #0f172a !important;
        }

        [data-testid="stSidebar"] {
            background-color: #ffffff !important;
            border-right: 1px solid #cbd5e1;
        }

        /* INPUTS MEJORADOS */
        input, .stNumberInput input, .stSelectbox div[data-baseweb="select"] {
            background-color: #ffffff !important;
            color: #000000 !important;
            border-color: #94a3b8 !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
        }
        
        /* CENTRAR TEXTO EN INPUTS DE LOGIN */
        .stTextInput input {
            text-align: center;
        }

        label { color: #0284c7 !important; font-weight: 700 !important; font-size: 0.95rem !important; }

        div[data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important;
            padding: 20px !important;
            border-radius: 12px !important;
        }
        div[data-testid="stMetricLabel"] { color: #64748b !important; font-size: 0.85rem !important; }
        div[data-testid="stMetricValue"] { color: #0f172a !important; font-weight: 800 !important; font-size: 1.8rem !important; }

        div.stButton > button:first-child {
            background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
            color: white !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
            padding: 0.75rem 1.5rem !important;
            font-size: 1rem !important;
            border: none !important;
            box-shadow: 0 4px 6px rgba(2, 132, 199, 0.2) !important;
        }

        .tech-card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-left: 5px solid #0ea5e9;
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        }
        .tech-title { color: #0ea5e9; font-size: 0.8rem; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px; }
        .tech-value { color: #0f172a; font-size: 1.2rem; font-weight: 800; margin-top: 5px; }
        .tech-sub { color: #64748b; font-size: 0.85rem; }
        
        .tank-card {
            background-color: #f0f9ff;
            border: 1px solid #bae6fd;
            padding: 20px;
            border-radius: 16px;
            text-align: center;
            margin-bottom: 20px;
        }
        .tank-final { border-bottom: 4px solid #2563eb; background-color: #eff6ff;}
        .tank-raw { border-bottom: 4px solid #475569; background-color: #f8fafc;}
        .tank-val { font-size: 1.5rem; font-weight: 800; color: #0f172a; }
        .tank-label { color: #0369a1; font-weight: 700; font-size: 0.9rem; text-transform: uppercase; }

        .pump-card {
            background-color: #fff7ed;
            border: 1px solid #ffedd5;
            border-left: 5px solid #f97316;
            padding: 20px;
            border-radius: 12px;
        }
        .pump-val { color: #c2410c; font-weight: 800; font-size: 1.5rem; }
        
        .alert-box {
            background-color: #fffbeb; border: 1px solid #fcd34d; color: #92400e;
            padding: 15px; border-radius: 8px; font-size: 0.95rem; margin-top: 15px; font-weight: 500;
        }
        .admin-panel { background-color: #1e1b4b; color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; }
        
        /* LOGIN ESTILO */
        .login-title { 
            font-family: 'Manrope', sans-serif; 
            font-weight: 800; 
            font-size: 2.8rem; /* Título más grande */
            color: #0f172a; 
            margin: 0; 
            text-align: center; 
            letter-spacing: -1px; 
        }
        .login-sub { 
            color: #64748b; 
            font-size: 1rem; 
            text-align: center; 
            margin-bottom: 30px; 
            text-transform: uppercase; 
            letter-spacing: 3px; 
            font-weight: 700; 
        }
    </style>
    """, unsafe_allow_html=True)
local_css()

# ==============================================================================
# 1. LOGIN MEJORADO (LOGO CENTRADO Y GRANDE)
# ==============================================================================
def check_auth():
    if "auth" not in st.session_state: st.session_state["auth"] = False
    if st.session_state["auth"]: return True
    
    # Columnas principales para centrar la caja en la pantalla
    c1,c2,c3 = st.columns([1, 2, 1]) # La del medio más ancha para tener espacio
    
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True) 
        
        # --- TRUCO PARA CENTRAR IMAGEN ---
        # Creamos 3 columnas DENTRO de la columna central.
        # [1 (Vacío), 2 (Logo), 1 (Vacío)] -> Esto fuerza el centro.
        ic1, ic2, ic3 = st.columns([1, 3, 1]) 
        
        with ic2:
            try: 
                # use_container_width=True hace que la imagen ocupe todo el ancho de la columna 2 (que es grande)
                st.image("logo.png", use_container_width=True)
            except: 
                st.warning("⚠️ Sube 'logo.png' a GitHub")
        
        st.markdown('<p class="login-title">HYDROLOGIC</p>', unsafe_allow_html=True)
        st.markdown('<p class="login-sub">ENGINEERING ACCESS</p>', unsafe_allow_html=True)
        
        with st.container():
            # Inputs
            user = st.text_input("Usuario", placeholder="ID Cliente")
            pwd = st.text_input("Contraseña", type="password", placeholder="••••••••")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("INICIAR SESIÓN", type="primary", use_container_width=True):
                # 1. Intento Supabase
                if supabase:
                    try:
                        response = supabase.table("usuarios").select("*").eq("username", user).eq("password", pwd).execute()
                        if len(response.data) > 0:
                            u = response.data[0]
                            if u["activo"]:
                                st.session_state["auth"] = True
                                st.session_state["user_info"] = u
                                st.rerun()
                            else: st.error("⚠️ Licencia expirada.")
                            return
                    except: pass 

                # 2. Credencial Maestra
                if user == "admin" and pwd == "hydro2025":
                    st.session_state["auth"] = True
                    st.session_state["user_info"] = {"username": "admin", "empresa": "HYDROLOGIC HQ", "rol": "admin", "logo_url": ""}
                    st.rerun()
                else:
                    st.error("❌ Credenciales inválidas")
            
            st.markdown("<div style='text-align: center; color: #94a3b8; font-size: 0.8rem; margin-top: 30px;'>v73.0 | Secure Platform</div>", unsafe_allow_html=True)

    return False

if not check_auth(): st.stop()

# ==============================================================================
# 2. LÓGICA (CON MEMBRANAS)
# ==============================================================================
class EquipoRO:
    def __init__(self, n, prod, ppm, ef, kw, mem):
        self.nombre = n; self.produccion_nominal = prod; self.max_ppm = ppm; self.eficiencia = ef; self.potencia_kw = kw; self.membranas = mem
class Filtro:
    def __init__(self, tipo, n, bot, caud, wash, sal=0, cap=0):
        self.tipo = tipo; self.nombre = n; self.medida_botella = bot; self.caudal_max = caud; self.caudal_wash = wash; self.sal_kg = sal; self.capacidad = cap

# CATÁLOGOS CON MEMBRANAS
ro_db = [
    # Doméstico
    EquipoRO("PURHOME PLUS", 300, 3000, 0.5, 0.03, "Membrana HRM"),
    EquipoRO("DF 800 UV-LED", 3000, 1500, 0.71, 0.08, "2x400 GPD"),
    EquipoRO("Direct Flow 1200", 4500, 1500, 0.66, 0.10, "3x400 GPD"),
    # Industrial
    EquipoRO("ALFA 140", 5000, 2000, 0.5, 0.75, "1x4040"),
    EquipoRO("ALFA 240", 10000, 2000, 0.5, 1.1, "2x4040"),
    EquipoRO("ALFA 340", 15000, 2000, 0.6, 1.5, "3x4040"),
    EquipoRO("ALFA 440", 20000, 2000, 0.6, 1.5, "4x4040"),
    EquipoRO("ALFA 640", 30000, 2000, 0.6, 2.2, "6x4040"),
    EquipoRO("ALFA 840 (Custom)", 40000, 2000, 0.7, 3.0, "8x4040"),
    EquipoRO("AP-6000 LUXE", 18000, 6000, 0.6, 2.2, "4x4040 High TDS"),
    EquipoRO("AP-10000 LUXE", 30000, 6000, 0.6, 4.0, "6x4040 High TDS"),
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
    if caudal_lh < 2000: return "0.75 CV", 0.55
    elif caudal_lh < 4000: return "1.0 CV", 0.75
    elif caudal_lh < 6000: return "1.5 CV", 1.1
    elif caudal_lh < 10000: return "2.0 CV", 1.5
    elif caudal_lh < 15000: return "3.0 CV", 2.2
    else: return "5.5 CV", 4.0

def calcular_tuberia(caudal_lh):
    if caudal_lh < 1500: return '3/4"'
    elif caudal_lh < 3000: return '1"'
    elif caudal_lh < 5000: return '1 1/4"'
    elif caudal_lh < 9000: return '1 1/2"'
    elif caudal_lh < 20000: return '2"'
    else: return '2 1/2"'

def calcular(origen, modo, consumo, caudal_punta, ppm, dureza, temp, horas, costes, buffer_on, descal_on, man_fin, man_buf):
    res = {}
    msgs = []
    
    # 1. DEPÓSITOS
    res['v_final'] = man_fin if man_fin > 0 else max(consumo * 0.75, caudal_punta * 60)
    
    fs = 1.2 if origen == "Pozo" else 1.0
    
    # 2. CÁLCULO
    if modo == "Solo Descalcificación":
        q_target = consumo / horas
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
        
        q_bomba = max(res.get('q_filtros', 0), res.get('wash', 0))
        res['bomba_nom'], res['bomba_kw'] = calcular_bomba(q_bomba)
        res['v_raw'] = man_raw if man_raw > 0 else res.get('wash', 0) * 0.4

    else: # MODO RO
        tcf = 1.0 if temp >= 25 else max(1.0 - ((25 - temp) * 0.03), 0.1)
        factor_recuperacion = 0.8 if ppm > 2500 else 1.0
        q_target = consumo
        ro_cands = [r for r in ro_db if ppm <= r.max_ppm and ((r.produccion_nominal * tcf / 24) * horas) >= q_target]
        
        if ro_cands:
            res['ro'] = next((r for r in ro_cands if "ALFA" in r.nombre or "AP" in r.nombre), ro_cands[-1]) if q_target > 600 else ro_cands[0]
            res['efi_real'] = res['ro'].eficiencia * factor_recuperacion
            res['q_prod_hora'] = (res['ro'].produccion_nominal * tcf) / 24
            
            agua_in = consumo / res['efi_real']
            q_bomba = (res['ro'].produccion_nominal / 24 / res['ro'].eficiencia) * 1.5
            
            if buffer_on:
                q_filtros = (agua_in / 20) * fs 
                res['v_buffer'] = man_buf if man_buf > 0 else q_bomba * 2
            else:
                q_filtros = q_bomba * fs 
                res['v_buffer'] = 0
            
            res['q_filtros'] = q_filtros
            
            sx_cands = [s for s in silex_db if (s.caudal_max * 1000) >= q_filtros]
            res['silex'] = sx_cands[0] if sx_cands else None
            
            cb_cands = [c for c in carbon_db if (c.caudal_max * 1000) >= q_filtros]
            res['carbon'] = cb_cands[0] if cb_cands else None

            if descal_on and dureza > 5:
                ds = [d for d in descal_db if (d.caudal_max*1000) >= q_filtros]
                if ds:
                    carga = (agua_in/1000)*dureza
                    v = [d for d in ds if (d.capacidad/carga if carga>0 else 99) >= 5]
                    res['descal'] = v[0] if v else ds[-1]
                    res['dias'] = res['descal'].capacidad / carga if carga > 0 else 99
                    res['sal_anual'] = (365/res['dias']) * res['descal'].sal_kg
                    res['wash'] = res['descal'].caudal_wash * 1000
                else: res['descal'] = None
            
            kwh = (consumo / res['q_prod_hora']) * res['ro'].potencia_kw * 365
            sal = res.get('sal_anual', 0)
            m3 = (agua_in/1000)*365
            res['opex'] = (kwh*costes['luz']) + (sal*costes['sal']) + (m3*costes['agua'])
            res['breakdown'] = {'Agua': m3*costes['agua'], 'Sal': sal*costes['sal'], 'Luz': kwh*costes['luz']}
            
            w1 = res['silex'].caudal_wash if res.get('silex') else 0
            w2 = res['carbon'].caudal_wash if res.get('carbon') else 0
            w3 = res['descal'].caudal_wash if res.get('descal') else 0
            res['wash'] = max(w1, w2, w3) * 1000
            
            q_bomba_aporte = max(res['q_filtros'], res['wash'])
            res['bomba_nom'], res['bomba_kw'] = calcular_bomba(q_bomba_aporte)
            
            res['v_raw'] = man_raw if man_raw > 0 else (res['wash'] * 0.35)
            
            kwh_ap = (consumo / res['q_filtros']) * res['bomba_kw'] * 365 
            res['opex'] += (kwh_ap * costes['luz'])
            res['breakdown']['Luz'] += (kwh_ap * costes['luz'])
            
        else: res['ro'] = None

    max_flow = max(res.get('q_filtros', 0), res.get('wash', 0))
    res['tuberia'] = calcular_tuberia(max_flow)
    res['msgs'] = msgs
    return res

# ==============================================================================
# 3. GENERADOR PDF
# ==============================================================================
def create_pdf(res, inputs, modo, user_data):
    pdf = FPDF()
    pdf.add_page()
    
    logo_impreso = False
    if user_data.get("logo_url") and len(str(user_data["logo_url"])) > 5:
        try:
            response = requests.get(user_data["logo_url"])
            if response.status_code == 200:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    tmp.write(response.content)
                    pdf.image(tmp.name, 10, 8, 33)
                    logo_impreso = True
        except: pass
    
    if not logo_impreso:
        try: pdf.image('logo.png', 10, 8, 33)
        except: pass

    pdf.ln(20)
    def clean(text): return str(text).encode('latin-1', 'replace').decode('latin-1') if text else "N/A"
    
    empresa_nombre = user_data.get("empresa", "HYDROLOGIC").upper()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, clean(f"INFORME TÉCNICO - {empresa_nombre}"), 0, 1, 'C')
    pdf.ln(10)
    
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, clean("1. PARAMETROS"), 0, 1)
    pdf.set_font("Arial", '', 10); pdf.cell(0, 8, clean(f"Consumo: {inputs['consumo']} L/dia | Punta: {inputs['punta']} L/min"), 0, 1)
    if modo == "Planta Completa (RO)": pdf.cell(0, 8, clean(f"TDS Entrada: {inputs['ppm']} ppm | Dureza: {inputs['dureza']} Hf"), 0, 1)
    pdf.ln(5)
    
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, clean("2. EQUIPOS"), 0, 1)
    pdf.set_font("Arial", '', 10)
    
    # AGUA BRUTA
    pdf.cell(0, 8, clean(f"A. DEPOSITO AGUA BRUTA: {int(res.get('v_raw', 0))} L"), 0, 1)
    pdf.cell(0, 8, clean(f"B. BOMBA APORTE: {res.get('bomba_nom', 'N/A')} @ 5 Bar"), 0, 1)

    if modo == "Solo Descalcificación":
        if res.get('descal'):
            pdf.cell(0, 8, clean(f"C. DESCAL: {res['descal'].nombre} ({res['descal'].medida_botella})"), 0, 1)
            pdf.set_font("Arial", 'I', 9)
            pdf.cell(0, 6, clean(f"   Autonomia: {res['dias']:.1f} dias"), 0, 1)
    else:
        if res.get('silex'): pdf.cell(0, 8, clean(f"C. SILEX: {res['silex'].nombre} ({res['silex'].medida_botella})"), 0, 1)
        if res.get('carbon'): pdf.cell(0, 8, clean(f"D. CARBON: {res['carbon'].nombre} ({res['carbon'].medida_botella})"), 0, 1)
        if res.get('v_buffer', 0)>0: pdf.cell(0, 8, clean(f"E. BUFFER: {int(res['v_buffer'])} Litros"), 0, 1)
        if res.get('descal'): pdf.cell(0, 8, clean(f"F. DESCAL: {res['descal'].nombre} ({res['descal'].medida_botella})"), 0, 1)
        if res.get('ro'): 
            pdf.cell(0, 8, clean(f"G. OSMOSIS: {res['ro'].nombre}"), 0, 1)
            pdf.set_font("Arial", 'I', 9)
            pdf.cell(0, 6, clean(f"   Config: {res['ro'].membranas} | Prod. Nominal: {res['ro'].produccion_nominal} L/d"), 0, 1)
            pdf.set_font("Arial", '', 10)
    
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, clean("3. REQUISITOS"), 0, 1)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, clean(f"DEPOSITO FINAL: {int(res['v_final'])} Litros"), 0, 1)
    pdf.set_text_color(200,0,0); pdf.cell(0, 8, clean(f"ACOMETIDA REQUERIDA: {int(res.get('wash', 0))} L/h a 2.5 bar"), 0, 1); pdf.set_text_color(0,0,0)
    pdf.cell(0, 8, clean(f"TUBERIA: {res['tuberia']}"), 0, 1)
    return pdf.output(dest='S').encode('latin-1')

# ==============================================================================
# 4. INTERFAZ
# ==============================================================================
c_head1, c_head2 = st.columns([1, 5])
with c_head1:
    try:
        logo_url = st.session_state["user_info"].get("logo_url")
        if logo_url: st.image(logo_url, width=120)
        else: st.image("logo.png", width=120)
    except: st.warning("Logo?")

with c_head2:
    emp = st.session_state["user_info"].get("empresa", "HYDROLOGIC")
    st.markdown('<p class="brand-logo">HYDROLOGIC</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="brand-sub">LICENCIA: {emp}</p>', unsafe_allow_html=True)

st.divider()

col_sb, col_main = st.columns([1, 2.5])

with col_sb:
    rol = st.session_state["user_info"].get("rol", "cliente")
    if rol == "admin":
        st.markdown("""<div class="admin-panel">👑 <b>PANEL GESTIÓN</b></div>""", unsafe_allow_html=True)
        with st.expander("Nuevo Usuario"):
            nu = st.text_input("User"); np = st.text_input("Pass"); nc = st.text_input("Empresa"); 
            ul = st.file_uploader("Logo (PNG/JPG)", type=['png','jpg','jpeg','webp'])
            if st.button("➕ Crear"):
                try:
                    furl = ""
                    if ul:
                        file_bytes = ul.getvalue()
                        path = f"logos/{nu}_{int(time.time())}.png"
                        supabase.storage.from_("logos").upload(path, file_bytes, {"content-type": "image/png"})
                        furl = supabase.storage.from_("logos").get_public_url(path)
                    supabase.table("usuarios").insert({"username": nu, "password": np, "empresa": nc, "rol": "cliente", "activo": True, "logo_url": furl}).execute()
                    st.success("Creado!")
                except Exception as e: st.error(f"Error: {e}")

    if st.button("Cerrar Sesión"): st.session_state["auth"] = False; st.rerun()
    st.subheader("Configuración")
    origen = st.selectbox("Origen", ["Red Pública", "Pozo"])
    modo = st.selectbox("Modo", ["Planta Completa (RO)", "Solo Descalcificación"])
    consumo = st.number_input("Consumo Diario (L)", value=2000, step=100)
    caudal_punta = st.number_input("Caudal Punta (L/min)", value=40)
    horas = st.number_input("Horas Prod", value=20)
    buffer = st.checkbox("Buffer Intermedio", value=True) if "RO" in modo else False
    descal = st.checkbox("Descalcificador", value=True) if "RO" in modo else True
    ppm = st.number_input("TDS (ppm)", value=800) if "RO" in modo else 0
    dureza = st.number_input("Dureza (Hf)", value=35)
    temp = st.number_input("Temp (C)", value=15) if "RO" in modo else 25
    with st.expander("Costes / Manual"):
        ca = st.number_input("Agua €", 1.5); cs = st.number_input("Sal €", 0.45); cl = st.number_input("Luz €", 0.20)
        mf = st.number_input("Dep Final (L)", 0); mr = st.number_input("Dep Bruta", 0)
        mb = st.number_input("Buffer (L)", 0)
    costes = {'agua': ca, 'sal': cs, 'luz': cl}
    if st.button("CALCULAR", type="primary", use_container_width=True): st.session_state['run'] = True

if st.session_state.get('run'):
    # LLAMADA V73 FIX (13 args)
    res = calcular(origen, modo, consumo, caudal_punta, ppm, dureza, temp, horas, costes, buffer, descal, mf, mr)
    
    if res.get('ro') or res.get('descal'):
        for msg in res['msgs']: col_main.markdown(f"<div class='alert-box alert-yellow'>{msg}</div>", unsafe_allow_html=True)
        
        c1, c2, c3, c4 = col_main.columns(4)
        c1.markdown(f"<div class='tank-card tank-raw'><span class='tank-label'>Depósito Entrada</span><div class='tank-val'>{int(res.get('v_raw', 0))} L</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='pump-card'><span class='tank-label'>Bomba Aporte</span><div class='pump-val'>{res.get('bomba_nom', 'N/A')}</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='tech-card'><span class='tech-title'>Caudal Diseño</span><div class='tech-value'>{int(res['q_filtros'])} L/h</div></div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='tank-card tank-final'><span class='tank-label'>Depósito Final</span><div class='tank-val'>{int(res['v_final'])} L</div></div>", unsafe_allow_html=True)

        col_main.subheader("⚡ Equipos Seleccionados")
        eq1, eq2, eq3, eq4 = col_main.columns(4)
        if modo == "Planta Completa (RO)":
            with eq1:
                if res.get('silex'): st.markdown(f"<div class='tech-card'><div class='tech-title'>🪨 SILEX</div><div class='tech-sub'>{res['silex'].medida_botella}</div></div>", unsafe_allow_html=True)
            with eq2:
                if res.get('carbon'): st.markdown(f"<div class='tech-card'><div class='tech-title'>⚫ CARBON</div><div class='tech-sub'>{res['carbon'].medida_botella}</div></div>", unsafe_allow_html=True)
            with eq3:
                if res.get('descal'): st.markdown(f"<div class='tech-card'><div class='tech-title'>🧂 DESCAL</div><div class='tech-sub'>{res['descal'].medida_botella}</div></div>", unsafe_allow_html=True)
            with eq4:
                st.markdown(f"<div class='tech-card' style='border-left-color:#00c6ff'><div class='tech-title'>💧 OSMOSIS</div><div class='tech-sub'>{res['ro'].nombre}</div></div>", unsafe_allow_html=True)
        else:
            eq1.markdown(f"<div class='tech-card'><div class='tech-title'>🧂 DESCAL</div><div class='tech-value'>{res['descal'].nombre}</div><div class='tech-sub'>{res['descal'].medida_botella}</div></div>", unsafe_allow_html=True)

        col_main.subheader("📊 Análisis")
        d1, d2 = col_main.columns(2)
        with d1:
            st.info(f"**Prod. Horaria:** {int(res.get('q_prod_hora', consumo/horas))} L/h")
            st.warning(f"**Acometida Min:** {int(res.get('wash', 0))} L/h")
            st.write(f"Tubería: **{res['tuberia']}**")
        with d2:
            if modo == "Planta Completa (RO)":
                df = pd.DataFrame(list(res['breakdown'].items()), columns=['Item', 'Coste'])
                fig = px.pie(df, values='Coste', names='Item', hole=0.6, color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", font_color="black", showlegend=False, height=150, margin=dict(t=0,b=0,l=0,r=0))
                st.plotly_chart(fig, use_container_width=True)
            st.metric("OPEX Diario", f"{(res['opex']/365):.2f} €")

        col_main.markdown("---")
        try:
            inputs_pdf = {'consumo': consumo, 'horas': horas, 'origen': origen, 'ppm': ppm, 'dureza': dureza, 'punta': caudal_punta}
            pdf_data = create_pdf(res, inputs_pdf, modo, st.session_state["user_info"])
            b64 = base64.b64encode(pdf_data).decode()
            col_main.markdown(f'<a href="data:application/octet-stream;base64,{b64}" download="informe_{emp}.pdf"><button style="background:#00e5ff;color:black;width:100%;padding:15px;border:none;border-radius:10px;font-weight:bold;">📥 DESCARGAR INFORME OFICIAL</button></a>', unsafe_allow_html=True)
        except Exception as e: col_main.error(f"Error PDF: {e}")

    else: col_main.error("Sin solución.")
else: col_main.info("👈 Introduce parámetros.")
