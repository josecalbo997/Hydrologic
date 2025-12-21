import streamlit as st
from fpdf import FPDF
import base64
import plotly.express as px
import pandas as pd

# ==============================================================================
# 0. CONFIGURACIÓN Y ESTILOS PREMIUM
# ==============================================================================
st.set_page_config(
    page_title="AimyWater Premium",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

def local_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap');
        
        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }
        
        .stApp { background-color: #f8f9fa; color: #1f2937; }
        
        /* Tarjetas Métricas Estilo SaaS */
        div[data-testid="stMetric"] {
            background-color: #ffffff !important;
            border: 1px solid #e5e7eb !important;
            padding: 20px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            transition: box-shadow 0.3s ease-in-out;
        }
        div[data-testid="stMetric"]:hover {
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
            border-color: #3b82f6 !important;
        }
        
        div[data-testid="stMetricLabel"] { color: #6b7280 !important; font-weight: 600; font-size: 0.9rem; }
        div[data-testid="stMetricValue"] { color: #111827 !important; font-size: 1.8rem; }
        
        /* Encabezados */
        h1, h2, h3 { color: #1e3a8a !important; font-weight: 700; letter-spacing: -0.025em; }
        
        /* Botón Principal */
        div.stButton > button:first-child {
            background: linear-gradient(135deg, #2563eb 0%, #1e40af 100%) !important;
            color: white !important;
            border-radius: 8px;
            height: 3.5em;
            font-weight: 600;
            border: none;
            box-shadow: 0 4px 6px rgba(37, 99, 235, 0.2);
            transition: all 0.2s;
        }
        div.stButton > button:first-child:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 8px rgba(37, 99, 235, 0.3);
        }
        
        /* Alertas personalizadas */
        div[data-testid="stAlert"] {
            border-radius: 10px;
            border: none;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
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

# --- CATÁLOGOS ---
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
# 2. MOTOR DE CÁLCULO
# ==============================================================================

def generar_pdf_tecnico(modo, ro, descal, carbon, silex, flow, blending_pct, consumo, ppm_in, ppm_out, dureza, alerta_dias, opex):
    pdf = FPDF()
    pdf.add_page()
    
    try: pdf.image('logo.png', 10, 8, 33)
    except: pass
    pdf.ln(20)

    titulo = "PROYECTO TÉCNICO - TRATAMIENTO DE AGUA"
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, titulo, 0, 1, 'C')
    pdf.ln(5)

    # 1. Datos
    pdf.set_fill_color(240, 240, 240)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "1. BASES DE DISEÑO", 1, 1, 'L', 1)
    pdf.set_font("Arial", size=10)
    pdf.cell(95, 8, f"Consumo Diario: {consumo} L/dia", 1)
    pdf.cell(95, 8, f"Dureza: {dureza} Hf", 1, 1)
    if modo == "Planta Completa (RO)":
        pdf.cell(95, 8, f"Salinidad Entrada: {ppm_in} ppm", 1)
        pdf.cell(95, 8, f"Salinidad Objetivo: {ppm_out} ppm", 1, 1)
    pdf.ln(5)

    # 2. Equipos
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "2. TREN DE TRATAMIENTO", 1, 1, 'L', 1)
    pdf.set_font("Arial", size=10)

    if modo == "Solo Descalcificación":
        pdf.ln(2)
        if descal:
            pdf.cell(0, 8, f"DESCALCIFICADOR: {descal[0].nombre}", 0, 1)
            pdf.cell(10, 8, "", 0, 0)
            pdf.cell(0, 6, f"Botella: {descal[0].medida_botella} | Valvula: {descal[0].tipo_valvula}", 0, 1)
            pdf.cell(10, 8, "", 0, 0)
            pdf.cell(0, 6, f"Autonomia: {descal[1]:.1f} dias", 0, 1)
            pdf.cell(10, 8, "", 0, 0)
            pdf.cell(0, 6, f"Consumo Sal: {int(opex['kg_sal'])} Kg/ano", 0, 1)
            if alerta_dias:
                pdf.set_text_color(200,0,0)
                pdf.cell(10, 8, "", 0, 0)
                pdf.cell(0, 6, f"NOTA: {alerta_dias}", 0, 1)
                pdf.set_text_color(0,0,0)
        else:
            pdf.cell(0, 8, "No se encontro equipo adecuado", 0, 1)
            
    else: 
        if silex:
            pdf.cell(0, 8, f"A. FILTRACION: {silex.nombre} ({silex.medida_botella})", 0, 1)
        if carbon:
            pdf.cell(0, 8, f"B. DECLORACION: {carbon.nombre} ({carbon.medida_botella})", 0, 1)
        if descal:
            pdf.cell(0, 8, f"C. DESCALCIFICADOR: {descal[0].nombre}", 0, 1)
            pdf.cell(10, 6, "", 0, 0)
            pdf.cell(0, 6, f"Regeneracion cada {descal[1]:.1f} dias", 0, 1)
        pdf.cell(0, 8, f"D. OSMOSIS: {ro.nombre} ({ro.produccion_nominal} L/dia)", 0, 1)

    return pdf.output(dest='S').encode('latin-1')

def calcular_logica(modo, consumo, ppm_in, ppm_out, dureza, temp, horas, coste_agua, coste_sal, coste_luz, usar_buffer, activar_descal):
    ro_sel = None
    descal_sel = None
    carbon_sel = None
    silex_sel = None
    flow = {}
    opex = {}
    alerta_autonomia = None
    v_buffer = 0

    if modo == "Solo Descalcificación":
        caudal_calculo = consumo / horas
        if dureza > 0:
            carga = (consumo / 1000) * dureza
            cands_validos = []
            cands_fallback = []
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
        opex = {"kg_sal": kg_sal, "coste_sal": kg_sal * coste_sal}

    else:
        tcf = 1.0 if temp >= 25 else max(1.0 - ((25 - temp) * 0.03), 0.1)
        ppm_ro = ppm_in * 0.05
        if ppm_out < ppm_ro: ppm_out = ppm_ro
        pct_ro = 1.0 if ppm_in == ppm_ro else (ppm_in - ppm_out) / (ppm_in - ppm_ro)
        pct_ro = max(0.0, min(1.0, pct_ro))
        
        litros_ro = consumo * pct_ro
        litros_bypass = consumo - litros_ro

        candidatos = []
        for ro in catalogo_ro:
            if ppm_in <= ro.max_ppm:
                factor = 1.0 if ro.categoria == "Industrial" else 0.4
                if (ro.produccion_nominal * tcf * factor) >= litros_ro:
                    candidatos.append(ro)
        if candidatos:
            ro_sel = next((x for x in candidatos if x.categoria == "Industrial"), candidatos[-1]) if litros_ro > 600 else next((x for x in candidatos if x.categoria == "Doméstico"), candidatos[0])

        if ro_sel:
            agua_entrada_ro = litros_ro / ro_sel.eficiencia
            agua_total = agua_entrada_ro + litros_bypass
            caudal_bomba_ro_lh = (ro_sel.produccion_nominal / 24 / ro_sel.eficiencia) * 1.5 
            
            if usar_buffer:
                caudal_filtros = agua_total / 20 
                v_buffer = caudal_bomba_ro_lh * 2 
            else:
                caudal_filtros = caudal_bomba_ro_lh + (litros_bypass / horas)
                v_buffer = 0

            flow = {
                "prod_ro_dia": litros_ro,
                "caudal_bypass_dia": litros_bypass,
                "prod_total_dia": consumo,
                "blending_pct": (litros_bypass / consumo) * 100,
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
                cands_validos = []   
                cands_fallback = []  
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
            
            # OPEX detallado para el gráfico
            opex_agua = (agua_total / 1000) * 365 * coste_agua
            opex_sal = kg_sal * coste_sal
            horas_ro = litros_ro / ((ro_sel.produccion_nominal * tcf)/24)
            opex_luz = horas_ro * ro_sel.potencia_kw * 365 * coste_luz
            
            opex = {
                "kg_sal": kg_sal,
                "coste_agua": opex_agua,
                "coste_sal": opex_sal,
                "coste_luz": opex_luz,
                "total": opex_agua + opex_sal + opex_luz
            }

    return ro_sel, descal_sel, carbon_sel, silex_sel, flow, opex, alerta_autonomia, v_buffer

# ==============================================================================
# 3. INTERFAZ VISUAL
# ==============================================================================

col_logo, col_header = st.columns([1, 5])
with col_logo:
    try: st.image("logo.png", width=150)
    except: st.warning("Logo?")
with col_header:
    st.title("AimyWater Premium")
    st.markdown("**Plataforma de Ingeniería Hidráulica v19**")

st.markdown("---")

with st.sidebar:
    modo = st.radio("🎛️ Modo de Operación", ["Planta Completa (RO)", "Solo Descalcificación"])
    st.markdown("---")
    
    st.header("⚙️ Parámetros")
    with st.expander("1. Hidráulica", expanded=True):
        consumo = st.number_input("Caudal Diario (L)", 100, 100000, 5000, step=500)
        horas = st.slider("Horas Trabajo", 1, 24, 12)
        if modo == "Planta Completa (RO)":
            usar_buffer = st.checkbox("Depósito Intermedio", value=True)
            activar_descal = st.checkbox("Incluir Descalcificador", value=True)
        else:
            usar_buffer = False
            activar_descal = True

    with st.expander("2. Calidad Agua", expanded=True):
        dureza = st.number_input("Dureza (ºHf)", 0, 100, 35)
        if modo == "Planta Completa (RO)":
            ppm_in = st.number_input("TDS Entrada", 50, 8000, 800)
            ppm_out = st.slider("TDS Objetivo", 0, 1000, 50)
            temp = st.slider("Temp (ºC)", 5, 35, 15)
        else:
            ppm_in, ppm_out, temp = 0, 0, 25

    with st.expander("3. Costes (€)"):
        coste_agua = st.number_input("Agua €/m3", 0.0, 10.0, 1.5)
        coste_sal = st.number_input("Sal €/kg", 0.0, 5.0, 0.45)
        coste_luz = st.number_input("Luz €/kWh", 0.0, 1.0, 0.20)
    
    st.markdown("---")
    btn_calc = st.button("CALCULAR PROYECTO", type="primary")

if btn_calc:
    ro, descal, carbon, silex, flow, opex, alerta, v_buffer = calcular_logica(modo, consumo, ppm_in, ppm_out, dureza, temp, horas, coste_agua, coste_sal, coste_luz, usar_buffer, activar_descal)
    
    if modo == "Solo Descalcificación":
        if descal:
            st.subheader("✅ Solución: Descalcificación Industrial")
            c1, c2 = st.columns([1,1])
            with c1:
                st.info(f"**MODELO: {descal[0].nombre}**")
                st.metric("Botella", descal[0].medida_botella)
                st.metric("Configuración", descal[0].tipo_valvula)
            with c2:
                if alerta: st.warning(alerta)
                else: st.success("Autonomía Correcta")
                st.metric("Regeneración", f"Cada {descal[1]:.1f} días")
                st.metric("Sal Anual", f"{int(opex['kg_sal'])} Kg")
        else:
            st.error("No se encontró equipo.")
    
    else: # MODO RO
        if not ro:
            st.error("❌ Sin solución viable.")
        else:
            # --- DASHBOARD VISUAL ---
            st.subheader("📊 Resumen del Proyecto")
            
            # Diagrama de Flujo Visual (Emojis + Columnas)
            st.markdown("#### 🏭 Tren de Tratamiento")
            f1, f2, f3, f4, f5 = st.columns(5)
            with f1:
                st.markdown("#### 🪨")
                if silex: st.caption(f"**Silex**\n{silex.medida_botella}")
                else: st.caption("No Silex")
            with f2:
                st.markdown("#### ⚫")
                if carbon: st.caption(f"**Carbón**\n{carbon.medida_botella}")
                else: st.caption("No Carbón")
            with f3:
                st.markdown("#### 🧂")
                if descal: st.caption(f"**Descal**\n{descal[0].medida_botella}")
                else: st.caption("Antiincrustante")
            with f4:
                st.markdown("#### 🛡️")
                if usar_buffer: st.caption(f"**Buffer**\n{int(v_buffer)} L")
                else: st.caption("Directo")
            with f5:
                st.markdown("#### 💧")
                st.caption(f"**Ósmosis**\n{ro.nombre}")

            st.markdown("---")

            # PESTAÑAS DETALLADAS
            tab_tec, tab_fin, tab_doc = st.tabs(["🛠️ Ingeniería", "💸 Análisis Financiero", "📄 Documentación"])
            
            with tab_tec:
                c1, c2 = st.columns(2)
                with c1:
                    st.success("Configuración RO")
                    st.write(f"- Modelo: **{ro.nombre}**")
                    st.write(f"- Producción Pura: **{int(flow['prod_ro_dia'])} L/d**")
                    st.write(f"- Bypass: **{int(flow['caudal_bypass_dia'])} L/d** ({flow['blending_pct']:.1f}%)")
                with c2:
                    st.info("Configuración Filtros")
                    st.write(f"- Caudal Diseño: **{int(flow['caudal_filtros'])} L/h**")
                    if descal:
                        st.write(f"- Descalcificador: **{descal[0].nombre}**")
                        if alerta: st.error(alerta)
            
            with tab_fin:
                c_chart, c_data = st.columns([2, 1])
                with c_chart:
                    # GRÁFICO DE DONUT DE COSTES
                    data_dict = {
                        "Concepto": ["Agua", "Sal", "Electricidad"],
                        "Coste (€)": [opex['coste_agua'], opex['coste_sal'], opex['coste_luz']]
                    }
                    df = pd.DataFrame(data_dict)
                    fig = px.pie(df, values='Coste (€)', names='Concepto', title='Distribución OPEX Anual', hole=0.4)
                    st.plotly_chart(fig, use_container_width=True)
                
                with c_data:
                    st.metric("Coste Total", f"{(opex['total']/365):.2f} €/día")
                    st.write(f"- Agua: {opex['coste_agua']:.0f} €/año")
                    st.write(f"- Sal: {opex['coste_sal']:.0f} €/año")
                    st.write(f"- Luz: {opex['coste_luz']:.0f} €/año")

            with tab_doc:
                try:
                    pdf_bytes = generar_pdf_tecnico(modo, ro, descal, carbon, silex, flow, 
                                                  flow.get('blending_pct', 0), consumo, ppm_in, ppm_out, dureza, alerta, opex)
                    b64 = base64.b64encode(pdf_bytes).decode()
                    href = f'<a href="data:application/octet-stream;base64,{b64}" download="informe_aimywater.pdf" style="text-decoration:none;"><button style="background-color:#cc0000;color:white;padding:10px;border-radius:5px;border:none;cursor:pointer;width:100%;">📥 Descargar Informe PDF</button></a>'
                    st.markdown(href, unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error PDF: {e}")

else:
    # LANDING PAGE AMIGABLE
    st.info("👈 Configura tu proyecto en el menú lateral para comenzar.")
    cols = st.columns(3)
    cols[0].metric("Modo", "Ingeniería")
    cols[1].metric("Estado", "Online 🟢")
    cols[2].metric("IA", "Activa")
