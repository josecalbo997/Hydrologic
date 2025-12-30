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
    page_title="HYDROLOGIC V59",
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
        
        /* --- 1. RESET GLOBAL NUCLEAR (Adiós Modo Oscuro) --- */
        html, body, [class*="css"], [data-testid="stAppViewContainer"], .stApp {
            font-family: 'Manrope', sans-serif !important;
            background-color: #f1f5f9 !important; /* Fondo Gris Claro Global */
            color: #0f172a !important; /* Texto Negro Global */
        }

        /* --- 2. SOLUCIÓN PARA LOS INPUTS (USUARIO Y CONTRASEÑA) --- */
        /* Forzamos que la caja donde escribes sea BLANCA */
        input.st-ae, input.st-af, input.st-ag, input.st-ah, input {
            background-color: #ffffff !important; 
            color: #000000 !important;          /* Letra NEGRA */
            caret-color: #000000 !important;    /* Cursor NEGRO */
            border-radius: 4px !important;
        }
        
        /* El borde de la caja */
        div[data-baseweb="input"] {
            background-color: #ffffff !important;
            border: 1px solid #94a3b8 !important;
        }
        
        /* Texto de placeholder (el grisito antes de escribir) */
        ::placeholder {
            color: #94a3b8 !important;
            opacity: 1 !important;
        }

        /* --- 3. TARJETAS Y CONTENEDORES --- */
        [data-testid="stSidebar"] { background-color: #ffffff !important; border-right: 1px solid #cbd5e1; }
        
        div[data-testid="stMetric"] {
            background-color: #ffffff !important; 
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
            padding: 15px !important;
            border-radius: 10px !important;
        }
        div[data-testid="stMetricLabel"] { color: #64748b !important; }
        div[data-testid="stMetricValue"] { color: #0f172a !important; font-weight: 800 !important; font-size: 1.6rem !important; }

        /* --- 4. BOTONES --- */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #0ea5e9 0%, #0284c7 100%) !important;
            color: white !important;
            border: none !important;
            font-weight: 700 !important;
            border-radius: 6px;
        }
        div.stButton > button:first-child p { color: #ffffff !important; }

        /* --- 5. ESTILOS PROPIOS --- */
        .tech-card {
            background-color: #ffffff; border: 1px solid #e2e8f0; border-left: 4px solid #0ea5e9; padding: 15px; border-radius: 8px; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.03);
        }
        .tech-title { color: #0ea5e9; font-size: 0.75rem; font-weight: 800; text-transform: uppercase; }
        .tech-value { color: #0f172a; font-size: 1.1rem; font-weight: 800; }
        .tech-sub { color: #64748b; font-size: 0.8rem; }
        
        .tank-card {
            background-color: #ffffff; border: 1px solid #cbd5e1; padding: 15px; border-radius: 10px; text-align: center; margin-bottom: 15px;
        }
        .tank-final { border-bottom: 4px solid #2563eb; background-color: #eff6ff;}
        .tank-raw { border-bottom: 4px solid #475569; background-color: #f8fafc;}
        .tank-val { font-size: 1.5rem; font-weight: 800; color: #0f172a; }
        .tank-label { color: #475569; font-weight: 700; font-size: 0.8rem; text-transform: uppercase; }

        .alert-box {
            background-color: #fffbeb; border: 1px solid #fcd34d; color: #92400e; padding: 10px; border-radius: 6px; font-size: 0.9rem; margin-top: 10px;
        }
        .admin-panel { background-color: #1e1b4b; color: white; padding: 15px; border-radius: 10px; margin-bottom: 20px; }
        
        /* CAJA DE LOGIN ESPECIAL */
        .login-box {
            background-color: #ffffff;
            padding: 2rem;
            border-radius: 15px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
            border: 1px solid #e2e8f0;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)
local_css()

# ==============================================================================
# 1. LOGIN (REDITADO PARA ALTA VISIBILIDAD)
# ==============================================================================
def check_auth():
    if "auth" not in st.session_state: st.session_state["auth"] = False
    if st.session_state["auth"]: return True
    
    # Columnas para centrar
    c1,c2,c3 = st.columns([1, 1.5, 1]) 
    
    with c2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        
        # LOGO CENTRADO
        ic1, ic2, ic3 = st.columns([1, 2, 1])
        with ic2:
            try: st.image("logo.png", use_container_width=True)
            except: pass
            
        st.markdown("<h2 style='text-align: center; color: #0f172a;'>HYDROLOGIC</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748b; font-weight: 600; margin-bottom: 30px;'>ENGINEERING ACCESS</p>", unsafe_allow_html=True)
        
        # --- AQUÍ EMPIEZA LA CAJA DE LOGIN ---
        # Usamos un contenedor de Streamlit que se verá blanco gracias al CSS
        with st.container():
            st.markdown("##### Iniciar Sesión") # Título pequeño negro
            user = st.text_input("Usuario", placeholder="Introduce tu ID")
            pwd = st.text_input("Contraseña", type="password", placeholder="Introduce tu clave")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("ENTRAR AL SISTEMA", type="primary", use_container_width=True):
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

                # 2. Credencial Maestra (BACKUP)
                if user == "admin" and pwd == "hydro2025":
                    st.session_state["auth"] = True
                    st.session_state["user_info"] = {"username": "admin", "empresa": "HYDROLOGIC HQ", "rol": "admin", "logo_url": ""}
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")

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

ro_db = [
    EquipoRO("PURHOME PLUS", 300, 3000, 0.5, 0.03, "Membrana HRM"), EquipoRO("DF 800 UV-LED", 3000, 1500, 0.71, 0.08, "2x400 GPD"),
    EquipoRO("Direct Flow 1200", 4500, 1500, 0.66, 0.10, "3x400 GPD"), EquipoRO("ALFA 140", 5000, 2000, 0.5, 0.75, "1x4040"),
    EquipoRO("ALFA 240", 10000, 2000, 0.5, 1.1, "2x4040"), EquipoRO("ALFA 340", 15000, 2000, 0.6, 1.5, "3x4040"),
    EquipoRO("ALFA 440", 20000, 2000, 0.6, 1.5, "4x4040"), EquipoRO("ALFA 640", 30000, 2000, 0.6, 2.2, "6x4040"),
    EquipoRO("ALFA 840 (Custom)", 40000, 2000, 0.7, 3.0, "8x4040"),
    EquipoRO("AP-6000 LUXE", 18000, 6000, 0.6, 2.2, "4x4040 High TDS"), EquipoRO("AP-10000 LUXE", 30000, 6000, 0.6, 4.0, "6x4040 High TDS"),
]
silex_db = [Filtro("Silex", "SIL 10x35", "10x35", 0.8, 2.0), Filtro("Silex", "SIL 10x44", "10x44", 0.8, 2.0), Filtro("Silex", "SIL 12x48", "12x48", 1.1, 3.5), Filtro("Silex", "SIL 18x65", "18x65", 2.6, 8.0), Filtro("Silex", "SIL 21x60", "21x60", 3.6, 11.0), Filtro("Silex", "SIL 24x69", "24x69", 4.4, 14.0), Filtro("Silex", "SIL 30x72", "30x72", 7.0, 20.0), Filtro("Silex", "SIL 36x72", "36x72", 10.0, 28.0)]
carbon_db = [Filtro("Carbon", "DEC 30L", "10x35", 0.38, 2.0), Filtro("Carbon", "DEC 45L", "10x54", 0.72, 2.0), Filtro("Carbon", "DEC 60L", "12x48", 0.80, 4.0), Filtro("Carbon", "DEC 75L", "13x54", 1.10, 5.0), Filtro("Carbon", "DEC 90KG", "18x65", 2.68, 8.0)]
descal_db = [Filtro("Descal", "BI BLOC 30L", "10x35", 1.8, 2.0, 4.5, 192), Filtro("Descal", "BI BLOC 60L", "12x48", 3.6, 3.5, 9.0, 384), Filtro("Descal", "TWIN 40L", "10x44", 2.4, 2.5, 6.0, 256), Filtro("Descal", "TWIN 100L", "14x65", 6.0, 5.0, 15.0, 640), Filtro("Descal", "DUPLEX 300L", "24x69", 6.5, 9.0, 45.0, 1800)]

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

def calcular(origen, modo, consumo, caudal_punta, ppm, dureza, temp, horas, costes, descal_on, man_fin, man_raw):
    res = {}
    msgs = []
    fs = 1.2 if origen == "Pozo" else 1.0
    res['v_final'] = man_fin if man_fin > 0 else max(consumo * 0.75, caudal_punta * 60)
    
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
    else: 
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
                    v = [d for d in
