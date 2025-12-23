import streamlit as st
from fpdf import FPDF
import base64
import plotly.express as px
import pandas as pd

# ==============================================================================
# 0. CONFIGURACIÓN E INYECCIÓN DE ESTILOS V34 (FIX VISIBILIDAD TOTAL)
# ==============================================================================
st.set_page_config(
    page_title="AimyWater V34",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

def local_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap');
        
        /* --- 1. FORZADO NUCLEAR DE MODO CLARO --- */
        [data-testid="stAppViewContainer"] {
            background-color: #f8fafc !important; /* Fondo Gris Claro */
        }
        [data-testid="stSidebar"] {
            background-color: #ffffff !important; /* Sidebar Blanca */
            border-right: 1px solid #e2e8f0;
        }
        
        /* --- 2. CORRECCIÓN CRÍTICA DE INPUTS (NÚMEROS INVISIBLES) --- */
        /* Esto ataca al input específico del navegador */
        input[type="number"], input[type="text"] {
            color: #000000 !important;          /* Texto NEGRO */
            background-color: #ffffff !important; /* Fondo BLANCO */
            -webkit-text-fill-color: #000000 !important; /* Safari/Chrome fix */
            caret-color: #000000 !important;    /* Cursor negro */
            font-weight: 700 !important;        /* Letra gruesa */
        }
        
        /* Contenedor del input */
        div[data-baseweb="input"] {
            background-color: #ffffff !important;
            border-color: #cbd5e1 !important;
            border-radius: 6px !important;
        }
        
        /* Etiquetas (Labels) de los inputs */
        .stNumberInput label, .stSlider label, .stSelectbox label {
            color: #1e293b !important; /* Gris oscuro muy legible */
            font-size: 0.95rem !important;
            font-weight: 700 !important;
        }
        
        /* Textos pequeños de ayuda */
        .stMarkdown p {
            color: #334155 !important;
        }

        /* --- 3. ESTILO DE TARJETAS Y MÉTRICAS --- */
        div[data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
            padding: 15px !important;
            border-radius: 10px !important;
        }
        div[data-testid="stMetricLabel"] { color: #64748b !important; }
        div[data-testid="stMetricValue"] { color: #003366 !important; font-weight: 800 !important; }

        /* --- 4. TÍTULOS Y ENCABEZADOS --- */
        h1, h2, h3, h4 {
            color: #0f172a !important;
            font-family: 'Outfit', sans-serif !important;
            font-weight: 800 !important;
        }

        /* --- 5. BOTONES --- */
        div.stButton > button:first-child {
            background-color: #0284c7 !important;
            color: #ffffff !important;
            border: none !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
        }
        div.stButton > button:first-child p {
            color: #ffffff !important;
        }

        /* --- 6. DEPÓSITOS --- */
        .tank-container {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            text-align: center;
        }
        .tank-final { border-left: 6px solid #2563eb; }
        .tank-intermedio { border-left: 6px solid #16a34a; }
        
        .tank-header { color: #1e3a8a !important; font-weight: 700; text-transform: uppercase; }
        .tank-val { color: #0f172a !important; font-weight: 900; font-size: 2rem; margin: 10px 0; }
        .tank-desc { color: #64748b !important; font-size: 0.85rem; font-weight: 600; }
        
        /* AVISO */
        .warning-box {
            background-color: #fffbeb;
            border: 1px solid #fcd34d;
            padding: 15px;
            border-radius: 8px;
            color: #92400e !important;
        }
    </style>
    """, unsafe_allow_html=True)

local_css()

# ==============================================================================
# SEGURIDAD (LOGIN)
# ==============================================================================
def check_password():
    if "password_correct" not in st.session_state: st.session_state["password_correct"] = False
    if st.session_state["password_correct"]: return True
    
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("### 🔐 Acceso Ingeniero")
        try: st.image("logo.png", width=150)
        except: pass
        user = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")
        if st.button("ENTRAR", type="primary"):
            users = st.secrets.get("users", {"admin": "aimywater2025"})
            if user in users and pwd == users[user]:
                st.session_state["password_correct"] = True
                st.rerun()
            else: st.error("Acceso Denegado")
    return False

if not check_password(): st.stop()

# ==============================================================================
# 1. BASE DE DATOS
# ==============================================================================

class EquipoRO:
    def __init__(self, categoria, nombre, produccion_nominal, max_ppm, eficiencia, potencia_kw):
        self.categoria = categoria
        self.nombre = nombre
        self.produccion_nominal = produccion_nominal
        self.max_ppm = max_ppm
        self.eficiencia = eficiencia
        self.potencia_kw = potencia_kw

class PreTratamiento:
    def __init__(self, tipo_equipo, nombre, medida_botella, caudal_max_m3h, caudal_contralavado_m3h, capacidad_intercambio=0, sal_kg=0, tipo_valvula=""):
        self.tipo_equipo = tipo_equipo 
        self.nombre = nombre
        self.medida_botella = medida_botella 
        self.caudal_max_m3h = caudal_max_m3h
        self.caudal_contralavado_m3h = caudal_contralavado_m3h
        self.capacidad_intercambio = capacidad_intercambio 
        self.sal_kg = sal_kg 
        self.tipo_valvula = tipo_valvula 

# CATÁLOGOS
catalogo_ro = [
    EquipoRO("Doméstico", "PURHOME PLUS", 300, 3000, 0.50, 0.03),
    EquipoRO("Doméstico", "DF 800 UV-LED", 3000, 1500, 0.71, 0.08),
    EquipoRO("Doméstico", "Direct Flow 1200", 4500, 1500, 0.66, 0.10),
    EquipoRO("Industrial", "ALFA 140", 5000, 2000, 0.50, 0.75),
    EquipoRO("Industrial", "ALFA 240", 10000, 2000, 0.50, 1.1),
    EquipoRO("Industrial", "ALFA 440", 20000, 2000, 0.60, 1.1),
    EquipoRO("Industrial", "ALFA 640", 30000, 2000, 0.60, 2.2),
    EquipoRO("Industrial", "AP-6000 LUXE", 18000, 6000, 0.60, 2.2),
]

catalogo_descal = [
    PreTratamiento("Descalcificador", "BI BLOC 30L", "10x35", 1.8, 2.0, 192, 4.5, "Simplex"),
    PreTratamiento("Descalcificador", "BI BLOC 60L", "12x48", 3.6, 3.5, 384, 9.0, "Simplex"),
    PreTratamiento("Descalcificador", "BI BLOC 100L", "14x65", 6.0, 5.0, 640, 15.0, "Simplex"),
    PreTratamiento("Descalcificador", "TWIN 40L DF", "10x44", 2.4, 2.5, 256, 6.0, "Duplex"),
    PreTratamiento("Descalcificador", "TWIN 100L DF", "14x65", 6.0, 5.0, 640, 15.0, "Duplex"),
    PreTratamiento("Descalcificador", "TWIN 140L DF", "16x65", 6.0, 6.0, 896, 25.0, "Duplex"),
    PreTratamiento("Descalcificador", "DUPLEX 300L", "24x69", 6.5, 9.0, 1800, 45.0, "Duplex"),
]

catalogo_carbon = [
    PreTratamiento("Carbon", "DEC 30L", "10x35", 0.38, 2.5, 0, 0, "1\""),
    PreTratamiento("Carbon", "DEC 45L", "10x54", 0.72, 3.0, 0, 0, "1\""),
    PreTratamiento("Carbon", "DEC 60L", "12x48", 0.80, 4.0, 0, 0, "1\""),
    PreTratamiento("Carbon", "DEC 75L", "13x54", 1.10, 5.0, 0, 0, "1\""),
    PreTratamiento("Carbon", "DEC 90KG", "18x65", 2.68, 8.0, 0, 0, "1.25\""),
]

catalogo_silex = [
    PreTratamiento("Silex", "SIL 10x35", "10x35", 0.8, 3.0, 0, 0, "1\""),
    PreTratamiento("Silex", "SIL 10x44", "10x44", 0.8, 3.0, 0, 0, "1\""),
    PreTratamiento("Silex", "SIL 12x48", "12x48", 1.1, 4.5, 0, 0, "1\""),
    PreTratamiento("Silex", "SIL 18x65", "18x65", 2.6, 9.0, 0, 0, "1.25\""),
    PreTratamiento("Silex", "SIL 21x60", "21x60", 3.6, 12.0, 0, 0, "1.25\""),
    PreTratamiento("Silex", "SIL 24x69", "24x69", 4.4, 15.0, 0, 0, "1.25\""),
    PreTratamiento("Silex", "SIL 30x72", "30x72", 7.0, 22.0, 0, 0, "1.5\""),
    PreTratamiento("Silex", "SIL 36x72", "36x72", 10.0, 30.0, 0, 0, "2\""),
]

# ==============================================================================
# 2. GENERADOR PDF
# ==============================================================================

def generar_pdf_tecnico(modo, ro, descal, carbon, silex, flow, blending_pct, consumo, ppm_in, ppm_out, dureza, alerta, opex, v_deposito_final, v_buffer_intermedio, horas_trabajo, caudal_acom_nec):
    pdf = FPDF()
    pdf.add_page()
    try: pdf.image('logo.png', 10, 8, 33)
    except: pass
    pdf.ln(20)

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "INFORME TÉCNICO AIMYWATER", 0, 1, 'C')
    pdf.ln(5)

    # BASES
    pdf.set_fill_color(240, 248, 255)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "1. BASES DE DISEÑO", 1, 1, 'L', 1)
    pdf.set_font("Arial", size=10)
    pdf.cell(95, 8, f"Consumo: {consumo} L/dia", 1)
    pdf.cell(95, 8, f"Produccion: {horas_trabajo} h/dia", 1, 1)
    pdf.cell(95, 8, f"Dureza: {dureza} Hf", 1)
    if modo == "Planta Completa (RO)":
        pdf.cell(95, 8, f"Salinidad In: {ppm_in} ppm", 1, 1)
    else:
        pdf.cell(95, 8, "", 1, 1)
    pdf.ln(5)

    # REQUISITOS INSTALACIÓN
    pdf.set_font("Arial", 'B', 11)
    pdf.set_text_color(200, 0, 0)
    pdf.cell(0, 8, "2. REQUISITOS CRÍTICOS DE INSTALACIÓN", 1, 1, 'L', 0)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 6, f"IMPORTANTE: La acometida de agua bruta debe garantizar un caudal punta minimo de {int(caudal_acom_nec)} L/h a 2.5 bar para el contralavado de filtros.")
    pdf.ln(5)

    # EQUIPOS
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "3. EQUIPOS SELECCIONADOS", 1, 1, 'L', 1)
    pdf.set_font("Arial", size=10)

    if modo == "Solo Descalcificación":
        pdf.ln(2)
        if descal:
            pdf.cell(0, 8, f"DESCAL: {descal[0].nombre} ({descal[0].medida_botella})", 0, 1)
            pdf.cell(10, 8, "", 0, 0)
            pdf.cell(0, 6, f"Autonomia: {descal[1]:.1f} dias | Valvula: {descal[0].tipo_valvula}", 0, 1)
            if alerta:
                alerta_clean = alerta.replace("⚠️", "AVISO:")
                pdf.cell(10, 8, "", 0, 0)
                pdf.set_text_color(200,0,0)
                pdf.cell(0, 6, alerta_clean, 0, 1)
                pdf.set_text_color(0,0,0)
    else: 
        if silex: pdf.cell(0, 8, f"A. SILEX: {silex.nombre} ({silex.medida_botella})", 0, 1)
        if carbon: pdf.cell(0, 8, f"B. CARBON: {carbon.nombre} ({carbon.medida_botella})", 0, 1)
        
        if v_buffer_intermedio > 0:
            pdf.cell(0, 8, f"C. BUFFER: {int(v_buffer_intermedio)} Litros (Recomendado)", 0, 1)

        if descal:
            pdf.cell(0, 8, f"D. DESCAL: {descal[0].nombre} ({descal[0].medida_botella})", 0, 1)
        
        if ro:
            pdf.cell(0, 8, f"E. OSMOSIS: {ro.nombre} ({ro.produccion_nominal} L/dia)", 0, 1)

    # DEPÓSITO FINAL
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "4. ACUMULACIÓN FINAL", 1, 1, 'L', 1)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, f"VOLUMEN RECOMENDADO: {int(v_deposito_final)} LITROS", 0, 1)

    return pdf.output(dest='S').encode('latin-1')

# ==============================================================================
# 3. MOTOR LÓGICO
# ==============================================================================

def calcular_logica(modo, consumo, ppm_in, ppm_out, dureza, temp, horas, coste_agua, coste_sal, coste_luz, usar_buffer, activar_descal, manual_final_l, manual_buffer_l):
    
    ro_sel, descal_sel, carbon_sel, silex_sel = None, None, None, None
    flow, opex = {}, {}
    alerta_autonomia = None
    caudal_acometida_necesario = 0 
    
    if manual_final_l > 0:
        v_deposito_final = manual_final_l
        is_manual_final = True
    else:
        v_deposito_final = consumo * 0.75 
        is_manual_final = False

    v_buffer_intermedio = 0
    is_manual_buffer = False

    if modo == "Solo Descalcificación":
        caudal_calculo = consumo / horas
        if dureza > 0:
            carga = (consumo / 1000) * dureza
            cands_validos, cands_fallback = [], []
            for d in catalogo_descal:
                if (d.caudal_max_m3h * 1000) >= caudal_calculo:
                    dias = d.capacidad_intercambio / carga if carga > 0 else 99
                    if dias >= 5.0: cands_validos.append((d, dias))
                    else: cands_fallback.append((d, dias))
            
            if cands_validos:
                cands_validos.sort(key=lambda x: x[0].medida_botella)
                descal_sel = cands_validos[0]
            elif cands_fallback:
                cands_fallback.sort(key=lambda x: x[0].caudal_max_m3h, reverse=True)
                descal_sel = cands_fallback[0]
                alerta_autonomia = f"⚠️ Autonomía: {descal_sel[1]:.1f} días"

        kg_sal = 0
        if descal_sel: 
            kg_sal = (365 / descal_sel[1]) * descal_sel[0].sal_kg
            caudal_acometida_necesario = descal_sel[0].caudal_contralavado_m3h * 1000
            
        opex = {"kg_sal": kg_sal, "coste_sal": kg_sal * coste_sal, "total": kg_sal * coste_sal}

    else:
        # MODO RO
        tcf = 1.0 if temp >= 25 else max(1.0 - ((25 - temp) * 0.03), 0.1)
        ppm_ro = ppm_in * 0.05
        if ppm_out < ppm_ro: ppm_out = ppm_ro
        pct_ro = 1.0 if ppm_in == ppm_ro else (ppm_in - ppm_out) / (ppm_in - ppm_ro)
        pct_ro = max(0.0, min(1.0, pct_ro))
        
        litros_ro_dia = consumo * pct_ro
        litros_bypass_dia = consumo - litros_ro_dia

        candidatos = []
        for ro in catalogo_ro:
            if ppm_in <= ro.max_ppm:
                capacidad_jornada = (ro.produccion_nominal * tcf / 24) * horas
                if capacidad_jornada >= litros_ro_dia:
                    candidatos.append(ro)
        if candidatos:
            ro_sel = next((x for x in candidatos if x.categoria == "Industrial"), candidatos[-1]) if litros_ro_dia > 600 else next((x for x in candidatos if x.categoria == "Doméstico"), candidatos[0])

        if ro_sel:
            agua_entrada_ro = litros_ro_dia / ro_sel.eficiencia
            agua_total = agua_entrada_ro + litros_bypass_dia
            
            caudal_bomba_ro_lh = (ro_sel.produccion_nominal / 24 / ro_sel.eficiencia) * 1.5 
            
            if usar_buffer:
                caudal_filtros = agua_total / 20 
                if manual_buffer_l > 0:
                    v_buffer_intermedio = manual_buffer_l
                    is_manual_buffer = True
                else:
                    v_buffer_intermedio = caudal_bomba_ro_lh * 2 
                    is_manual_buffer = False
            else:
                caudal_filtros = caudal_bomba_ro_lh + (litros_bypass_dia / horas)
                v_buffer_intermedio = 0

            flow = {
                "prod_ro_dia": litros_ro_dia,
                "caudal_bypass_dia": litros_bypass_dia,
                "prod_total_dia": consumo,
                "blending_pct": (litros_bypass_dia / consumo) * 100,
                "caudal_filtros": caudal_filtros
            }

            cands_silex = [s for s in catalogo_silex if (s.caudal_max_m3h * 1000) >= caudal_filtros]
            if cands_silex: 
                cands_silex.sort(key=lambda x: x.caudal_max_m3h)
                silex_sel = cands_silex[0]

            cands_carbon = [c for c in catalogo_carbon if (c.caudal_max_m3h * 1000) >= caudal_filtros]
            if cands_carbon:
                cands_carbon.sort(key=lambda x: x.caudal_max_m3h)
                carbon_sel = cands_carbon[0]

            if activar_descal and dureza > 5:
                carga = (agua_total / 1000) * dureza
                cands_validos, cands_fallback = [], []
                for d in catalogo_descal:
                    if (d.caudal_max_m3h * 1000) >= caudal_filtros:
                        dias = d.capacidad_intercambio / carga if carga > 0 else 99
                        if dias >= 5.0: cands_validos.append((d, dias))
                        else: cands_fallback.append((d, dias))
                
                if cands_validos:
                    cands_validos.sort(key=lambda x: x[0].medida_botella)
                    descal_sel = cands_validos[0]
                elif cands_fallback:
                    cands_fallback.sort(key=lambda x: x[0].caudal_max_m3h, reverse=True)
                    descal_sel = cands_fallback[0]
                    alerta_autonomia = f"⚠️ Autonomía: {descal_sel[1]:.1f} días"

            max_wash = 0
            if silex_sel: max_wash = max(max_wash, silex_sel.caudal_contralavado_m3h)
            if carbon_sel: max_wash = max(max_wash, carbon_sel.caudal_contralavado_m3h)
            if descal_sel: max_wash = max(max_wash, descal_sel[0].caudal_contralavado_m3h)
            caudal_acometida_necesario = max_wash * 1000

            kg_sal = 0
            if descal_sel: kg_sal = (365 / descal_sel[1]) * descal_sel[0].sal_kg
            
            opex
