import streamlit as st
from fpdf import FPDF
import base64
import plotly.express as px
import pandas as pd

# ==============================================================================
# 0. CONFIGURACIÓN
# ==============================================================================
st.set_page_config(
    page_title="AimyWater V23 Dual Tank",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

def local_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
        .stApp { background-color: #f8f9fa; color: #1f2937; }
        
        div[data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            padding: 20px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        }
        div[data-testid="stMetricLabel"] { color: #6b7280 !important; font-weight: 600; font-size: 0.9rem; }
        div[data-testid="stMetricValue"] { color: #111827 !important; font-size: 1.5rem; }
        h1, h2, h3 { color: #1e3a8a !important; font-weight: 700; }
        
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
            color: white !important;
            border-radius: 8px;
            height: 3.5em;
            font-weight: 600;
            border: none;
        }
        
        /* Estilo Depósito Final (Azul) */
        .deposito-final {
            background-color: #eff6ff;
            border-left: 5px solid #2563eb;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        
        /* Estilo Depósito Intermedio (Gris/Verde) */
        .deposito-intermedio {
            background-color: #f0fdf4;
            border-left: 5px solid #16a34a;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        
        .tank-title { font-weight: bold; font-size: 1.1em; margin-bottom: 5px; }
        .tank-vol { font-size: 1.8em; font-weight: 800; }
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

def generar_pdf_tecnico(modo, ro, descal, carbon, silex, flow, blending_pct, consumo, ppm_in, ppm_out, dureza, alerta, opex, v_deposito_final, v_buffer_intermedio, horas_trabajo):
    pdf = FPDF()
    pdf.add_page()
    
    try: pdf.image('logo.png', 10, 8, 33)
    except: pass
    pdf.ln(20)

    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "PROYECTO TÉCNICO AIMYWATER", 0, 1, 'C')
    pdf.ln(5)

    # 1. BASES
    pdf.set_fill_color(235, 245, 255)
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

    # 2. EQUIPOS
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "2. TREN DE TRATAMIENTO", 1, 1, 'L', 1)
    pdf.set_font("Arial", size=10)

    if modo == "Solo Descalcificación":
        pdf.ln(2)
        if descal:
            pdf.cell(0, 8, f"EQUIPO: {descal[0].nombre}", 0, 1)
            pdf.cell(10, 8, "", 0, 0)
            pdf.cell(0, 6, f"Botella: {descal[0].medida_botella} | Valvula: {descal[0].tipo_valvula}", 0, 1)
            pdf.cell(10, 8, "", 0, 0)
            pdf.cell(0, 6, f"Autonomia: {descal[1]:.1f} dias", 0, 1)
            if alerta:
                alerta_clean = alerta.replace("⚠️", "ATENCION:")
                pdf.set_text_color(200,0,0)
                pdf.cell(10, 8, "", 0, 0)
                pdf.cell(0, 6, f"NOTA: {alerta_clean}", 0, 1)
                pdf.set_text_color(0,0,0)
    else: 
        if silex: pdf.cell(0, 8, f"A. FILTRACION: {silex.nombre} ({silex.medida_botella})", 0, 1)
        if carbon: pdf.cell(0, 8, f"B. DECLORACION: {carbon.nombre} ({carbon.medida_botella})", 0, 1)
        if descal:
            pdf.cell(0, 8, f"C. DESCALCIFICADOR: {descal[0].nombre}", 0, 1)
            pdf.cell(10, 6, "", 0, 0)
            pdf.cell(0, 6, f"Regeneracion cada {descal[1]:.1f} dias", 0, 1)
        
        # DEPÓSITO INTERMEDIO EN PDF
        if v_buffer_intermedio > 0:
            pdf.ln(2)
            pdf.cell(0, 8, f"D. ACUMULACION INTERMEDIA (BUFFER PRE-RO)", 0, 1)
            pdf.cell(10, 8, "", 0, 0)
            pdf.cell(0, 6, f"Volumen Recomendado: {int(v_buffer_intermedio)} Litros", 0, 1)
            pdf.cell(10, 8, "", 0, 0)
            pdf.cell(0, 6, "Funcion: Desacople hidraulico (Filtros lentos -> RO rapida)", 0, 1)

        if ro:
            pdf.ln(2)
            pdf.cell(0, 8, f"E. OSMOSIS INVERSA: {ro.nombre}", 0, 1)
            pdf.cell(10, 6, "", 0, 0)
            pdf.cell(0, 6, f"Produccion Nominal: {ro.produccion_nominal} L/dia", 0, 1)

    # 3. DEPÓSITO FINAL
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "3. ALMACENAMIENTO FINAL (PRODUCTO)", 1, 1, 'L', 1)
    pdf.set_font("Arial", size=10)
    pdf.cell(0, 8, f"VOLUMEN DEPÓSITO RECOMENDADO: {int(v_deposito_final)} LITROS", 0, 1)
    pdf.set_font("Arial", 'I', 9)
    pdf.multi_cell(0, 5, "Deposito final para suministro a vivienda/industria con grupo de presion.")

    return pdf.output(dest='S').encode('latin-1')

# ==============================================================================
# 3. MOTOR LÓGICO V23
# ==============================================================================

def calcular_logica(modo, consumo, ppm_in, ppm_out, dureza, temp, horas, coste_agua, coste_sal, coste_luz, usar_buffer_intermedio, activar_descal):
    
    ro_sel, descal_sel, carbon_sel, silex_sel = None, None, None, None
    flow, opex = {}, {}
    alerta_autonomia = None
    v_buffer_intermedio = 0
    
    # Depósito Final (60-75% del consumo diario para picos)
    v_deposito_final = consumo * 0.75 

    if modo == "Solo Descalcificación":
        # Estrategia: Llenado Lento
        caudal_calculo = consumo / horas
        
        if dureza > 0:
            carga = (consumo / 1000) * dureza
            cands_validos, cands_fallback = [], []
            for d in catalogo_descal:
                if (d.caudal_max_m3h * 1000) >= caudal_calculo:
                    dias = d.capacidad_intercambio / carga if carga > 0 else 99
                    if dias >= 5.0: cands_validos.append((d, dias))
                    else: cands_fallback.append((d, dias))
            
            if c
