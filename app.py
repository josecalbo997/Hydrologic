import streamlit as st
from fpdf import FPDF
import base64
import plotly.express as px
import pandas as pd

# ==============================================================================
# 0. CONFIGURACIÓN E INYECCIÓN DE ESTILOS (V28: ESTABILIDAD TOTAL)
# ==============================================================================
st.set_page_config(
    page_title="AimyWater Pro",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

def local_css():
    st.markdown("""
    <style>
        /* --- FUENTE GLOBAL --- */
        @import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;600;700;800&display=swap');
        
        /* RESET TOTAL: Forzar colores claros y legibles */
        html, body, [class*="css"], [data-testid="stAppViewContainer"] {
            font-family: 'Manrope', sans-serif !important;
            background-color: #ffffff !important; /* Fondo Blanco Puro */
            color: #1e293b !important; /* Texto Gris Oscuro */
        }

        /* --- SIDEBAR --- */
        section[data-testid="stSidebar"] {
            background-color: #f8fafc !important; /* Gris muy suave */
            border-right: 1px solid #e2e8f0;
        }
        
        /* --- TEXTOS Y TÍTULOS --- */
        h1, h2, h3, h4, h5, h6 {
            color: #0f172a !important; /* Azul muy oscuro casi negro */
            font-weight: 800 !important;
        }
        p, li, span, label, div {
            color: #334155 !important;
        }

        /* --- TARJETAS MÉTRICAS (KPIs) --- */
        div[data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            padding: 15px !important;
            border-radius: 12px !important;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1) !important;
        }
        
        /* Etiquetas de Métricas */
        div[data-testid="stMetricLabel"] p {
            color: #64748b !important; /* Gris medio */
            font-size: 0.9rem !important;
            font-weight: 600 !important;
        }
        /* Valores de Métricas */
        div[data-testid="stMetricValue"] div {
            color: #0284c7 !important; /* Azul AimyWater vivo */
            font-size: 1.6rem !important;
            font-weight: 800 !important;
        }

        /* --- BOTONES --- */
        div.stButton > button:first-child {
            background-color: #0284c7 !important;
            color: white !important;
            border: none !important;
            padding: 0.6rem 1.2rem !important;
            font-weight: 700 !important;
            border-radius: 8px !important;
            transition: background-color 0.2s;
        }
        div.stButton > button:first-child:hover {
            background-color: #0369a1 !important; /* Azul más oscuro al pasar ratón */
            color: white !important; /* Asegurar texto blanco */
        }
        /* Texto dentro del botón forzado a blanco */
        div.stButton > button:first-child p {
            color: white !important;
        }

        /* --- CONTENEDORES PERSONALIZADOS (DEPÓSITOS) --- */
        /* Usamos CSS nativo para evitar superposiciones de HTML */
        .tank-container {
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 1px solid;
        }
        .tank-final {
            background-color: #eff6ff !important;
            border-color: #bfdbfe !important;
        }
        .tank-intermedio {
            background-color: #f0fdf4 !important;
            border-color: #bbf7d0 !important;
        }
        
        /* Forzar color de texto dentro de las tarjetas de depósito */
        .tank-header { color: #1e3a8a !important; font-weight: 700; font-size: 0.9rem; text-transform: uppercase; }
        .tank-number { color: #172554 !important; font-weight: 800; font-size: 2rem; margin: 10px 0; }
        .tank-desc { color: #475569 !important; font-size: 0.9rem; }

        /* Ajustes de Tabs */
        button[data-baseweb="tab"] {
            font-weight: 600 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background-color: white !important;
            border-bottom: 3px solid #0284c7 !important;
        }
        
    </style>
    """, unsafe_allow_html=True)

local_css()

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
    def __init__(self, tipo_equipo, nombre, medida_botella, caudal_max_m3h, capacidad_intercambio=0, sal_kg=0, tipo_valvula=""):
        self.tipo_equipo = tipo_equipo 
        self.nombre = nombre
        self.medida_botella = medida_botella 
        self.caudal_max_m3h = caudal_max_m3h
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
    PreTratamiento("Descalcificador", "BI BLOC 30L IMPRESSION", "10x35", 1.8, 192, 4.5, "Simplex"),
    PreTratamiento("Descalcificador", "BI BLOC 60L IMPRESSION", "12x48", 3.6, 384, 9.0, "Simplex"),
    PreTratamiento("Descalcificador", "BI BLOC 100L IMPRESSION", "14x65", 6.0, 640, 15.0, "Simplex"),
    PreTratamiento("Descalcificador", "TWIN 40L DF IMPRESSION", "10x44", 2.4, 256, 6.0, "Duplex"),
    PreTratamiento("Descalcificador", "TWIN 100L DF IMPRESSION", "14x65", 6.0, 640, 15.0, "Duplex"),
    PreTratamiento("Descalcificador", "TWIN 140L DF IMPRESSION", "16x65", 6.0, 896, 25.0, "Duplex"),
    PreTratamiento("Descalcificador", "DUPLEX 300L IMPRESSION 1.5\"", "24x69", 6.5, 1800, 45.0, "Duplex"),
]

catalogo_carbon = [
    PreTratamiento("Carbon", "DEC 14KG/30L IMPRESSION 1\"", "10x35", 0.38, 0, 0, "Impression 1\""),
    PreTratamiento("Carbon", "DEC 22KG/45L IMPRESSION 1\"", "10x54", 0.72, 0, 0, "Impression 1\""),
    PreTratamiento("Carbon", "DEC 28KG/60L IMPRESSION 1\"", "12x48", 0.80, 0, 0, "Impression 1\""),
    PreTratamiento("Carbon", "DEC 37KG/75L IMPRESSION 1\"", "13x54", 1.10, 0, 0, "Impression 1\""),
    PreTratamiento("Carbon", "DEC 90KG IMPRESSION 1 1/4\"", "18x65", 2.68, 0, 0, "Impression 1 1/4\""),
]

catalogo_silex = [
    PreTratamiento("Silex", "FILTRO SILEX 10x35 IMPRESSION 1\"", "10x35", 0.8, 0, 0, "Impression 1\""),
    PreTratamiento("Silex", "FILTRO SILEX 10x44 IMPRESSION 1\"", "10x44", 0.8, 0, 0, "Impression 1\""),
    PreTratamiento("Silex", "FILTRO SILEX 12x48 IMPRESSION 1\"", "12x48", 1.1, 0, 0, "Impression 1\""),
    PreTratamiento("Silex", "FILTRO SILEX 18x65 IMPRESSION 1.25\"", "18x65", 2.6, 0, 0, "Impression 1 1/4\""),
    PreTratamiento("Silex", "FILTRO SILEX 21x60 IMPRESSION 1.25\"", "21x60", 3.6, 0, 0, "Impression 1 1/4\""),
    PreTratamiento("Silex", "FILTRO SILEX 24x69 IMPRESSION 1.25\"", "24x69", 4.4, 0, 0, "Impression 1 1/4\""),
    PreTratamiento("Silex", "FILTRO SILEX 30x72 IMPRESSION 1.5\"", "30x72", 7.0, 0, 0, "Impression 1 1/2\""),
    PreTratamiento("Silex", "FILTRO SILEX 36x72 IMPRESSION 2\"", "36x72", 10.0, 0, 0, "Impression 2\""),
]

# ==============================================================================
# 2. GENERADOR PDF
# ==============================================================================

def generar_pdf_tecnico(modo, ro, descal, carbon, silex, flow, blending_pct, consumo, ppm_in, ppm_out, dureza, alerta, opex, v_deposito_final, v_buffer_intermedio, horas_trabajo, is_manual_final, is_manual_buffer):
    pdf = FPDF()
    pdf.add_page()
    
    try: pdf.image('logo.png', 10, 8, 33)
    except: pass
    pdf.ln(20)

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "PROYECTO TÉCNICO AIMYWATER", 0, 1, 'C')
    pdf.ln(5)

    # 1. BASES
    pdf.set_fill_color(240, 248, 255) 
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "1. BASES DE DISEÑO", 1, 1, 'L', 1)
    pdf.set_font("Arial", size=10)
    pdf.cell(95, 8, f"Consumo Diario: {consumo} L/dia", 1)
    pdf.cell(95, 8, f"Horas Produccion: {horas_trabajo} h/dia", 1, 1)
    pdf.cell(95, 8, f"Dureza: {dureza} Hf", 1)
    if modo == "Planta Completa (RO)":
        pdf.cell(95, 8, f"TDS Entrada: {ppm_in} ppm", 1, 1)
    else:
        pdf.cell(95, 8, "", 1, 1)
    pdf.ln(5)

    # 2. EQUI
