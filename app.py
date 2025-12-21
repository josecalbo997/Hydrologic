import streamlit as st
from fpdf import FPDF
import base64
import plotly.express as px
import pandas as pd

# ==============================================================================
# 0. CONFIGURACIÓN E INYECCIÓN DE ESTILOS
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
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
        
        html, body, [class*="css"], [data-testid="stAppViewContainer"] {
            font-family: 'Outfit', sans-serif !important;
            background-color: #ffffff !important;
            color: #1e293b !important;
        }

        section[data-testid="stSidebar"] {
            background-color: #f8fafc !important;
            border-right: 1px solid #e2e8f0;
        }
        
        h1, h2, h3, h4, h5, h6 { color: #0f172a !important; font-weight: 800 !important; }
        p, li, span, label, div { color: #334155 !important; }

        div[data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #e2e8f0 !important;
            padding: 15px !important;
            border-radius: 12px !important;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1) !important;
        }
        
        div[data-testid="stMetricLabel"] p { color: #64748b !important; font-size: 0.9rem !important; font-weight: 600 !important; }
        div[data-testid="stMetricValue"] div { color: #0284c7 !important; font-size: 1.6rem !important; font-weight: 800 !important; }

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
            background-color: #0369a1 !important;
            color: white !important;
        }
        div.stButton > button:first-child p { color: white !important; }

        .tank-container {
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
            border: 1px solid;
        }
        .tank-final { background-color: #eff6ff !important; border-color: #bfdbfe !important; }
        .tank-intermedio { background-color: #f0fdf4 !important; border-color: #bbf7d0 !important; }
        
        .tank-header { color: #1e3a8a !important; font-weight: 700; font-size: 0.9rem; text-transform: uppercase; }
        .tank-number { color: #172554 !important; font-weight: 800; font-size: 2rem; margin: 10px 0; }
        .tank-desc { color: #475569 !important; font-size: 0.9rem; }

        button[data-baseweb="tab"] { font-weight: 600 !important; }
        button[data-baseweb="tab"][aria-selected="true"] { background-color: white !important; border-bottom: 3px solid #0284c7 !important; }
        
        /* Estilo Login */
        .login-box {
            padding: 2rem;
            border-radius: 10px;
            background: white;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            max-width: 400px;
            margin: auto;
        }
    </style>
    """, unsafe_allow_html=True)

local_css()

# ==============================================================================
# SISTEMA DE SEGURIDAD (LOGIN)
# ==============================================================================

def check_password():
    """Retorna True si el usuario se loguea correctamente."""

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    # Interfaz de Login
    c1, c2, c3 = st.columns([1,2,1])
    with c2:
        st.markdown("### 🔒 Acceso AimyWater")
        try:
            st.image("logo.png", width=150)
        except: pass
        
        st.info("Introduce tus credenciales para acceder a la ingeniería.")
        
        user = st.text_input("Usuario")
        pwd = st.text_input("Contraseña", type="password")
        
        if st.button("ENTRAR", type="primary"):
            # Verifica contra los secretos de la nube
            try:
                # Comprobamos si el usuario existe y la contraseña coincide
                if user in st.secrets["users"] and pwd == st.secrets["users"][user]:
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("❌ Usuario o contraseña incorrectos")
            except Exception as e:
                # Fallback por si no están configurados los secretos aún
                if user == "admin" and pwd == "aimywater2025":
                    st.session_state["password_correct"] = True
                    st.rerun()
                else:
                    st.error("⚠️ Configura los secretos o usa credenciales de emergencia.")

    return False

if not check_password():
    st.stop() # DETIENE LA EJECUCIÓN AQUÍ SI NO ESTÁ LOGUEADO

# ==============================================================================
# A PARTIR DE AQUÍ: EL CÓDIGO DE LA CALCULADORA (SOLO VISIBLE SI LOGUEADO)
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
            pdf.cell(0, 6, f"Caudal Llenado: {int(consumo/horas_trabajo)} L/h", 0, 1)
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
        
        if v_buffer_intermedio > 0:
            pdf.ln(2)
            pdf.cell(0, 8, f"C. ACUMULACION INTERMEDIA (PRE-RO)", 0, 1)
            nota_buf = "(Manual)" if is_manual_buffer else "(Auto)"
            pdf.cell(10, 8, "", 0, 0)
            pdf.cell(0, 6, f"Volumen: {int(v_buffer_intermedio)} Litros {nota_buf}", 0, 1)

        if descal:
            pdf.ln(2)
            pdf.cell(0, 8, f"D. DESCALCIFICADOR: {descal[0].nombre}", 0, 1)
            pdf.cell(10, 6, "", 0, 0)
            pdf.cell(0, 6, f"Regeneracion cada {descal[1]:.1f} dias", 0, 1)
        
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
    
    nota_fin = "(Manual)" if is_manual_final else "(Auto 75% Consumo)"
    pdf.cell(0, 8, f"VOLUMEN DEPÓSITO: {int(v_deposito_final)} LITROS {nota_fin}", 0, 1)

    return pdf.output(dest='S').encode('latin-1')

# ==============================================================================
# 3. MOTOR LÓGICO
# ==============================================================================

def calcular_logica(modo, consumo, ppm_in, ppm_out, dureza, temp, horas, coste_agua, coste_sal, coste_luz, usar_buffer, activar_descal, manual_final_l, manual_buffer_l):
    
    ro_sel, descal_sel, carbon_sel, silex_sel = None, None, None, None
    flow, opex = {}, {}
    alerta_autonomia = None
    
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
        if descal_sel: kg_sal = (365 / descal_sel[1]) * descal_sel[0].sal_kg
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

            kg_sal = 0
            if descal_sel: kg_sal = (365 / descal_sel[1]) * descal_sel[0].sal_kg
            
            opex_agua = (agua_total / 1000) * 365 * coste_agua
            opex_sal = kg_sal * coste_sal
            horas_ro_reales = litros_ro_dia / ((ro.produccion_nominal * tcf)/24)
            opex_luz = horas_ro_reales * ro.potencia_kw * 365 * coste_luz
            
            opex = {"kg_sal": kg_sal, "coste_agua": opex_agua, "coste_sal": opex_sal, "coste_luz": opex_luz, "total": opex_agua + opex_sal + opex_luz}

    return ro_sel, descal_sel, carbon_sel, silex_sel, flow, opex, alerta_autonomia, v_buffer_intermedio, v_deposito_final, is_manual_final, is_manual_buffer

# ==============================================================================
# 3. INTERFAZ VISUAL
# ==============================================================================

c_head1, c_head2 = st.columns([1, 5])
with c_head1:
    try: st.image("logo.png", width=140)
    except: st.warning("Logo?")
with c_head2:
    st.markdown("## 💧 AimyWater Engineering Suite")
    st.caption("Plataforma Integral de Dimensionamiento v29")

st.markdown("---")

with st.sidebar:
    st.markdown(f"👤 **Usuario:** {st.secrets.get('users', {}).keys()}") # Muestra usuario si quieres
    if st.button("Cerrar Sesión"):
        st.session_state["password_correct"] = False
        st.rerun()
    st.markdown("---")
    
    modo = st.radio("🎛️ MODO DE DISEÑO", ["Planta Completa (RO)", "Solo Descalcificación"])
    st.markdown("---")
    
    st.subheader("⚙️ Configuración")
    
    with st.expander("1. Hidráulica", expanded=True):
        consumo = st.number_input("Consumo Diario (Litros/24h)", 100, 100000, 2000, step=500)
        horas = st.slider("Horas Trabajo Planta", 1, 24, 20)
        
        if modo == "Planta Completa (RO)":
            usar_buffer = st.checkbox("Usar Depósito Intermedio (Pre-RO)", value=True)
            activar_descal = st.checkbox("Incluir Descalcificador", value=True)
        else:
            usar_buffer = False
            activar_descal = True

    with st.expander("2. Acumulación (Personalizar)", expanded=False):
        st.info("Dejar en 0 para cálculo automático.")
        man_final = st.number_input("Depósito Final (L)", 0, 100000, 0, step=100)
        man_buffer = 0
        if usar_buffer:
            man_buffer = st.number_input("Depósito Intermedio (L)", 0, 100000, 0, step=100)

    with st.expander("3. Calidad Agua", expanded=False):
        dureza = st.number_input("Dureza (ºHf)", 0, 100, 35)
        if modo == "Planta Completa (RO)":
            ppm_in = st.number_input("TDS Entrada", 50, 8000, 800)
            ppm_out = st.slider("TDS Objetivo", 0, 1000, 50)
            temp = st.slider("Temp (ºC)", 5, 35, 15)
        else:
            ppm_in, ppm_out, temp = 0, 0, 25

    with st.expander("4. Costes", expanded=False):
        coste_agua = st.number_input("Agua €/m3", 0.0, 10.0, 1.5)
        coste_sal = st.number_input("Sal €/kg", 0.0, 5.0, 0.45)
        coste_luz = st.number_input("Luz €/kWh", 0.0, 1.0, 0.20)
    
    st.markdown("---")
    btn_calc = st.button("CALCULAR PROYECTO", type="primary")

# --- RESULTADOS ---
if btn_calc:
    ro, descal, carbon, silex, flow, opex, alerta, v_buffer, v_producto, is_man_final, is_man_buf = calcular_logica(
        modo, consumo, ppm_in, ppm_out, dureza, temp, horas, coste_agua, coste_sal, coste_luz, usar_buffer, activar_descal, man_final, man_buffer
    )
    
    col_tanks = st.columns(2)
    
    if v_buffer > 0:
        with col_tanks[0]:
            tag = "PERSONALIZADO" if is_man_buf else "AUTO"
            st.markdown(f"""
            <div class='tank-container tank-intermedio'>
                <div class='tank-header'>🛡️ DEPÓSITO INTERMEDIO</div>
                <div class='tank-number'>{int(v_buffer)} L</div>
                <div class='tank-desc'>{tag} • Pre-Ósmosis</div>
            </div>""", unsafe_allow_html=True)
    
    with col_tanks[1] if v_buffer > 0 else col_tanks[0]:
        tag_fin = "PERSONALIZADO" if is_man_final else "AUTO"
        st.markdown(f"""
        <div class='tank-container tank-final'>
            <div class='tank-header'>🛢️ DEPÓSITO FINAL</div>
            <div class='tank-number'>{int(v_producto)} L</div>
            <div class='tank-desc'>{tag_fin} • Agua Producto</div>
        </div>""", unsafe_allow_html=True)
    
    st.markdown("---")

    if modo == "Solo Descalcificación":
        if descal:
            st.subheader("✅ Solución Descalcificación")
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Modelo", descal[0].nombre)
                st.metric("Botella", descal[0].medida_botella)
            with c2:
                st.metric("Regeneración", f"Cada {descal[1]:.1f} días")
                if alerta: st.error(alerta)
                else: st.success("Autonomía Correcta")
        else:
            st.error("No se encontró equipo adecuado.")
    
    else: # MODO RO
        if not ro:
            st.error("❌ No se encontró solución viable (Revisar salinidad o caudal).")
        else:
            st.subheader("📊 Tren de Tratamiento")
            
            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Ósmosis", ro.nombre)
            k2.metric("Silex", silex.medida_botella if silex else "N/A")
            k3.metric("Carbón", carbon.medida_botella if carbon else "N/A")
            k4.metric("Descal", descal[0].medida_botella if descal else "N/A")

            tab_tec, tab_fin, tab_doc = st.tabs(["🛠️ Ingeniería", "💸 Financiero", "📄 Documentación"])
            
            with tab_tec:
                c_tec1, c_tec2 = st.columns(2)
                with c_tec1:
                    st.markdown("**Parámetros de Diseño**")
                    st.write(f"Producción RO: **{int(flow['prod_ro_dia'])} L/día**")
                    st.write(f"Mezcla (Bypass): **{flow['blending_pct']:.1f}%**")
                with c_tec2:
                    st.markdown("**Caudales**")
                    st.write(f"Caudal Diseño Filtros: **{int(flow['caudal_filtros'])} L/h**")
            
            with tab_fin:
                c_fin1, c_fin2 = st.columns([2, 1])
                with c_fin1:
                    data = {
                        "Concepto": ["Agua", "Sal", "Luz"],
                        "Coste": [opex['coste_agua'], opex['coste_sal'], opex['coste_luz']]
                    }
                    fig = px.pie(pd.DataFrame(data), values='Coste', names='Concepto', hole=0.5)
                    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                    st.plotly_chart(fig, use_container_width=True)
                with c_fin2:
                    st.metric("OPEX Diario", f"{(opex['total']/365):.2f} €")

            with tab_doc:
                try:
                    pdf_bytes = generar_pdf_tecnico(modo, ro, descal, carbon, silex, flow, 
                                                  flow.get('blending_pct', 0), consumo, ppm_in, ppm_out, dureza, alerta, opex, 
                                                  v_producto, v_buffer, horas, is_man_final, is_man_buf)
                    b64 = base64.b64encode(pdf_bytes).decode()
                    href = f'<a href="data:application/octet-stream;base64,{b64}" download="informe_aimywater.pdf" style="text-decoration:none;"><button style="background-color:#0284c7;color:white;padding:12px;border-radius:8px;border:none;cursor:pointer;width:100%;font-weight:bold;">📥 Descargar Informe PDF</button></a>'
                    st.markdown(href, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error PDF: {e}")

else:
    st.info("👈 Configura los parámetros en el menú lateral.")
