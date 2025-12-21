import streamlit as st

# ==============================================================================
# 0. CONFIGURACIÓN E INYECCIÓN DE ESTILOS (CORRECCIÓN VISUAL)
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
        /* --- CORRECCIÓN DE COLORES (MODO CLARO FORZADO) --- */
        
        /* Forzar fondo general claro para evitar conflictos */
        .stApp {
            background-color: #ffffff;
            color: #000000;
        }

        /* Estilo de Tarjetas (Cards) para Métricas */
        div[data-testid="stMetric"] {
            background-color: #f8f9fa !important; /* Fondo Gris muy claro */
            border: 1px solid #dee2e6 !important;
            padding: 15px !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        }

        /* FORZAR COLOR DE TEXTO EN MÉTRICAS A NEGRO/AZUL */
        div[data-testid="stMetricLabel"] {
            color: #6c757d !important; /* Gris oscuro para el título pequeño */
            font-size: 14px !important;
        }
        div[data-testid="stMetricValue"] {
            color: #003366 !important; /* Azul AimyWater para el número */
            font-weight: bold !important;
        }
        div[data-testid="stMetricDelta"] {
            color: #28a745 !important; /* Verde para textos secundarios */
        }

        /* Corrección para textos generales y markdown */
        p, h1, h2, h3, h4, h5, li {
            color: #212529 !important; /* Negro suave, nunca blanco */
        }
        
        /* Títulos en Azul Corporativo */
        h1, h2, h3 {
            color: #004d99 !important;
        }

        /* Botón de Cálculo */
        div.stButton > button:first-child {
            background-color: #004d99 !important;
            color: white !important;
            border-radius: 5px;
            height: 3em;
            font-weight: 600;
            border: none;
        }
        div.stButton > button:first-child:hover {
            background-color: #003366 !important;
            color: #ffffff !important;
        }
        
        /* Sidebar: Asegurar legibilidad */
        section[data-testid="stSidebar"] {
            background-color: #f0f2f6 !important;
        }
        section[data-testid="stSidebar"] h1, 
        section[data-testid="stSidebar"] h2, 
        section[data-testid="stSidebar"] label {
            color: #003366 !important;
        }
        
        /* Inputs y Sliders: Asegurar que se vean las etiquetas */
        .stNumberInput label, .stSlider label {
            color: #212529 !important;
        }

    </style>
    """, unsafe_allow_html=True)

local_css()

# ==============================================================================
# 1. LOGICA DE NEGOCIO
# ==============================================================================

class EquipoRO:
    def __init__(self, categoria, nombre, produccion_nominal, max_ppm, eficiencia, potencia_kw):
        self.categoria = categoria
        self.nombre = nombre
        self.produccion_nominal = produccion_nominal
        self.max_ppm = max_ppm
        self.eficiencia = eficiencia
        self.potencia_kw = potencia_kw

class Descalcificador:
    def __init__(self, nombre, litros_resina, caudal_max_m3h, capacidad_intercambio, sal_por_regen_kg, tipo):
        self.nombre = nombre
        self.litros_resina = litros_resina
        self.caudal_max_m3h = caudal_max_m3h
        self.capacidad_intercambio = capacidad_intercambio
        self.sal_por_regen_kg = sal_por_regen_kg
        self.tipo = tipo

# Catálogos
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
    Descalcificador("BI BLOC 30L IMPRESSION", 30, 1.8, 192, 4.5, "Simplex"),
    Descalcificador("BI BLOC 60L IMPRESSION", 60, 3.6, 384, 9.0, "Simplex"),
    Descalcificador("BI BLOC 100L IMPRESSION", 100, 6.0, 640, 15.0, "Simplex"),
    Descalcificador("TWIN 40L DF IMPRESSION", 40, 2.4, 256, 6.0, "Duplex"),
    Descalcificador("TWIN 100L DF IMPRESSION", 100, 6.0, 640, 15.0, "Duplex"),
    Descalcificador("TWIN 140L DF IMPRESSION", 140, 6.0, 896, 25.0, "Duplex"),
]

# ==============================================================================
# 2. MOTOR DE CÁLCULO
# ==============================================================================

def calcular_sistema(consumo_diario, ppm, dureza, temp, horas_punta, coste_agua, coste_sal, coste_luz):
    tcf = 1.0 if temp >= 25 else max(1.0 - ((25 - temp) * 0.03), 0.1)
    
    # RO
    ro_sel = None
    candidatos = []
    for ro in catalogo_ro:
        if ppm <= ro.max_ppm:
            factor_uso = 1.0 if ro.categoria == "Industrial" else 0.4
            cap_real = ro.produccion_nominal * tcf * factor_uso
            if cap_real >= consumo_diario:
                candidatos.append(ro)
    
    if candidatos:
        ro_sel = next((x for x in candidatos if x.categoria == "Industrial"), candidatos[-1]) if consumo_diario > 600 else next((x for x in candidatos if x.categoria == "Doméstico"), candidatos[0])

    # Descalcificador & Flow
    descal_sel = None
    flow = {}
    opex = {}
    logistica = {}

    if ro_sel:
        agua_entrada = consumo_diario / ro_sel.eficiencia
        caudal_prod_lh = (ro_sel.produccion_nominal * tcf) / 24
        
        flow = {
            "entrada": agua_entrada,
            "rechazo": agua_entrada - consumo_diario,
            "prod_real_dia": ro_sel.produccion_nominal * tcf,
            "prod_lh": caudal_prod_lh
        }

        if dureza > 5:
            carga = (agua_entrada / 1000) * dureza
            caudal_alim_lh = (ro_sel.produccion_nominal / 24 / ro_sel.eficiencia) * 1.5
            
            cands_soft = []
            es_ind = ro_sel.categoria == "Industrial"
            for d in catalogo_descal:
                if (d.caudal_max_m3h * 1000) >= caudal_alim_lh:
                    dias = d.capacidad_intercambio / carga if carga > 0 else 99
                    viable = False
                    if es_ind and consumo_diario > 5000:
                        if "Duplex" in d.tipo or dias > 1: viable = True
                    else:
                        if dias >= 0.8: viable = True
                    if viable: cands_soft.append((d, dias))
            
            if cands_soft:
                cands_soft.sort(key=lambda x: (0 if "Duplex" in x[0].tipo and es_ind else 1, x[0].litros_resina))
                descal_sel = cands_soft[0]

        # OPEX
        c_agua = (agua_entrada / 1000) * 365 * coste_agua
        c_sal = 0
        kg_sal = 0
        if descal_sel:
            eq, dias = descal_sel
            kg_sal = (365 / dias) * eq.sal_por_regen_kg
            c_sal = kg_sal * coste_sal
        
        horas_marcha = consumo_diario / caudal_prod_lh
        c_elec = horas_marcha * ro_sel.potencia_kw * 365 * coste_luz
        
        opex = {"total": c_agua + c_sal + c_elec, "agua": c_agua, "sal": c_sal, "elec": c_elec, "kg_sal": kg_sal}

        # Logística
        demanda_lh = consumo_diario / horas_punta
        if demanda_lh > caudal_prod_lh:
            deficit = demanda_lh - caudal_prod_lh
            logistica = {"tanque": deficit * horas_punta * 1.2, "msg": f"Déficit {int(deficit)} L/h"}
        else:
            logistica = {"tanque": 0, "msg": "OK"}

    return ro_sel, descal_sel, flow, opex, logistica

# ==============================================================================
# 3. INTERFAZ DE USUARIO
# ==============================================================================

# --- HEADER ---
c1, c2 = st.columns([1, 5])
with c1:
    try:
        st.image("logo.png", width=140)
    except:
        st.warning("⚠️ Sube 'logo.png' a GitHub")
with c2:
    st.title("AimyWater Enterprise")
    st.markdown("##### Dimensionamiento Inteligente de Tratamiento de Aguas")

st.divider()

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Datos del Proyecto")
    
    st.markdown("#### 1. Hidráulica")
    litros = st.number_input("Consumo (L/día)", 100, 50000, 2000, step=100)
    horas = st.slider("Horas de trabajo", 1, 24, 8)
    
    st.markdown("#### 2. Calidad Agua")
    ppm = st.number_input("TDS (ppm)", 50, 8000, 800)
    dureza = st.number_input("Dureza (ºHf)", 0, 100, 35)
    temp = st.slider("Temperatura (ºC)", 5, 35, 15)
        
    st.markdown("#### 3. Económico (€)")
    coste_agua = st.number_input("Agua (€/m3)", 0.0, 10.0, 1.5)
    coste_sal = st.number_input("Sal (€/kg)", 0.0, 5.0, 0.45)
    coste_luz = st.number_input("Luz (€/kWh)", 0.0, 1.0, 0.20)
    
    st.markdown("---")
    btn_calc = st.button("CALCULAR SOLUCIÓN", use_container_width=True)

# --- PANEL PRINCIPAL ---

if btn_calc:
    ro, descal, flow, opex, log = calcular_sistema(litros, ppm, dureza, temp, horas, coste_agua, coste_sal, coste_luz)
    
    if not ro:
        st.error("❌ **NO SE ENCONTRÓ SOLUCIÓN:** Salinidad excesiva o caudal fuera de rango.")
    else:
        # --- HERO SECTION ---
        st.subheader("✅ Solución Recomendada")
        
        col_main, col_details = st.columns([1.5, 1])
        
        with col_main:
            with st.container():
                st.info(f"🔵 **EQUIPO: {ro.nombre}**")
                m1, m2, m3 = st.columns(3)
                m1.metric("Producción Real", f"{int(flow['prod_real_dia'])} L/día", f"a {temp}ºC")
                m2.metric("Eficiencia", f"{int(ro.eficiencia*100)}%")
                m3.metric("Categoría", ro.categoria)
            
            if descal:
                d, dias = descal
                with st.container():
                    st.warning(f"🟠 **PRE-TRATAMIENTO: {d.nombre}**")
                    d1, d2, d3 = st.columns(3)
                    d1.metric("Resina", f"{d.litros_resina} L")
                    d2.metric("Tipo", d.tipo)
                    d3.metric("Regeneración", f"Cada {dias:.1f} días")
            else:
                st.success("🟢 **AGUA BLANDA:** No requiere descalcificador")

        with col_details:
            st.markdown("#### 📦 Acumulación")
            if log["tanque"] > 0:
                st.error("Requiere Depósito")
                st.metric("Volumen Mínimo", f"{int(log['tanque'])} Litros", "Para cubrir picos")
            else:
                st.success("Suministro Directo")
                st.metric("Estado", "OK", "Producción suficiente")

        st.markdown("---")

        # --- TABS ---
        t_fin, t_tec, t_copy = st.tabs(["💰 Análisis Financiero", "⚙️ Datos Técnicos", "📋 Resumen"])
        
        with t_fin:
            st.markdown("#### Costes Operativos Estimados (OPEX)")
            cf1, cf2, cf3, cf4 = st.columns(4)
            cf1.metric("Coste Diario", f"{(opex['total']/365):.2f} €")
            cf2.metric("Agua", f"{opex['agua']:.0f} €/año")
            cf3.metric("Sal", f"{opex['sal']:.0f} €/año")
            cf4.metric("Luz", f"{opex['elec']:.0f} €/año")
        
        with t_tec:
            ct1, ct2 = st.columns(2)
            with ct1:
                st.markdown("**Balance de Aguas**")
                st.write(f"- Agua Aporte: **{int(flow['entrada'])} L/día**")
                st.write(f"- Agua Producto: **{litros} L/día**")
                st.write(f"- Rechazo: **{int(flow['rechazo'])} L/día**")
            with ct2:
                st.markdown("**Consumibles**")
                st.write(f"- Sal Anual: **{int(opex['kg_sal'])} kg**")
                st.write(f"- Potencia: **{ro.potencia_kw} kW**")

        with t_copy:
            st.markdown("#### Texto para Presupuesto")
            txt = f"""
            SOLUCIÓN AIMYWATER:
            1. RO: {ro.nombre} ({int(flow['prod_real_dia'])} L/día)
            2. PRE: {descal[0].nombre if descal else "N/A"}
            3. LOG: {int(log['tanque'])} L Depósito
            Coste Operativo: {(opex['total']/365):.2f} €/día
            """
            st.code(txt)

else:
    st.info("👈 Introduce los datos en el menú lateral para calcular.")
