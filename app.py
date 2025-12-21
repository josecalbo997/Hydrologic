import streamlit as st

# ==============================================================================
# 0. CONFIGURACIÓN E INYECCIÓN DE ESTILOS (HIGH CONTRAST)
# ==============================================================================
st.set_page_config(
    page_title="AimyWater Pro Calc",
    page_icon="💧",
    layout="wide",
    initial_sidebar_state="expanded"
)

def local_css():
    st.markdown("""
    <style>
        /* FORZAR MODO CLARO Y ALTO CONTRASTE */
        .stApp {
            background-color: #ffffff;
            color: #000000;
        }
        
        /* Tarjetas de Métricas */
        div[data-testid="stMetric"] {
            background-color: #f8f9fa !important;
            border: 1px solid #dee2e6 !important;
            padding: 15px !important;
            border-radius: 8px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        }

        /* Colores de Texto Forzados */
        div[data-testid="stMetricLabel"] { color: #6c757d !important; font-size: 14px !important; }
        div[data-testid="stMetricValue"] { color: #003366 !important; font-weight: bold !important; }
        
        p, h1, h2, h3, h4, h5, li, label { color: #212529 !important; }
        h1, h2, h3 { color: #004d99 !important; }

        /* Botón Principal */
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
        }
        
        /* Sidebar */
        section[data-testid="stSidebar"] { background-color: #f0f2f6 !important; }
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
# 2. MOTOR DE CÁLCULO (LÓGICA MODIFICADA 5 DÍAS)
# ==============================================================================

def calcular_sistema(consumo_diario, ppm, dureza, temp, horas_punta, coste_agua, coste_sal, coste_luz):
    tcf = 1.0 if temp >= 25 else max(1.0 - ((25 - temp) * 0.03), 0.1)
    
    # --- SELECCIÓN RO ---
    ro_sel = None
    candidatos_ro = []
    for ro in catalogo_ro:
        if ppm <= ro.max_ppm:
            factor_uso = 1.0 if ro.categoria == "Industrial" else 0.4
            cap_real = ro.produccion_nominal * tcf * factor_uso
            if cap_real >= consumo_diario:
                candidatos_ro.append(ro)
    
    if candidatos_ro:
        ro_sel = next((x for x in candidatos_ro if x.categoria == "Industrial"), candidatos_ro[-1]) if consumo_diario > 600 else next((x for x in candidatos_ro if x.categoria == "Doméstico"), candidatos_ro[0])

    # --- SELECCIÓN DESCALCIFICADOR Y FLUJOS ---
    descal_sel = None
    flow = {}
    opex = {}
    logistica = {}
    alerta_autonomia = None # Nueva variable para avisar si no llegamos a 5 días

    if ro_sel:
        agua_entrada = consumo_diario / ro_sel.eficiencia
        caudal_prod_lh = (ro_sel.produccion_nominal * tcf) / 24
        
        flow = {
            "entrada": agua_entrada,
            "rechazo": agua_entrada - consumo_diario,
            "prod_real_dia": ro_sel.produccion_nominal * tcf,
            "prod_lh": caudal_prod_lh
        }

        # LÓGICA DESCALCIFICADOR (MODIFICADA: REGLA DE 5 DÍAS)
        if dureza > 5:
            carga_dia = (agua_entrada / 1000) * dureza
            caudal_alim_lh = (ro_sel.produccion_nominal / 24 / ro_sel.eficiencia) * 1.5
            
            cands_soft_validos = []     # Cumplen > 5 días
            cands_soft_fallback = []    # No cumplen 5 días pero sirven por caudal (Plan B)
            
            es_ind = ro_sel.categoria == "Industrial"
            
            for d in catalogo_descal:
                # 1. Filtro Hidráulico (Caudal)
                if (d.caudal_max_m3h * 1000) >= caudal_alim_lh:
                    
                    # 2. Cálculo de Autonomía
                    dias = d.capacidad_intercambio / carga_dia if carga_dia > 0 else 99
                    
                    # 3. Clasificación según regla de 5 días
                    if dias >= 5.0:
                        cands_soft_validos.append((d, dias))
                    else:
                        cands_soft_fallback.append((d, dias))
            
            # SELECCIÓN FINAL
            if cands_soft_validos:
                # Si hay equipos que aguantan 5 días, cogemos el más pequeño de ellos (más barato)
                cands_soft_validos.sort(key=lambda x: x[0].litros_resina)
                descal_sel = cands_soft_validos[0]
            elif cands_soft_fallback:
                # Si NINGUNO aguanta 5 días (consumo muy alto), cogemos el MÁS GRANDE disponible
                # y lanzamos alerta.
                cands_soft_fallback.sort(key=lambda x: x[0].litros_resina, reverse=True) # El más grande primero
                descal_sel = cands_soft_fallback[0]
                alerta_autonomia = f"⚠️ Alto Consumo: Autonomía de {descal_sel[1]:.1f} días (No alcanza 5 días con equipos estándar)."

        # CÁLCULO OPEX
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

        # CÁLCULO LOGÍSTICA
        demanda_lh = consumo_diario / horas_punta
        if demanda_lh > caudal_prod_lh:
            deficit = demanda_lh - caudal_prod_lh
            logistica = {"tanque": deficit * horas_punta * 1.2, "msg": f"Déficit {int(deficit)} L/h"}
        else:
            logistica = {"tanque": 0, "msg": "OK"}

    return ro_sel, descal_sel, flow, opex, logistica, alerta_autonomia

# ==============================================================================
# 3. INTERFAZ DE USUARIO
# ==============================================================================

# HEADER
c1, c2 = st.columns([1, 5])
with c1:
    try:
        st.image("logo.png", width=140)
    except:
        st.info("Logotipo")
with c2:
    st.title("AimyWater Enterprise")
    st.markdown("##### Dimensionamiento con Lógica de Ciclo Extendido (5 Días)")

st.divider()

# SIDEBAR
with st.sidebar:
    st.markdown("### ⚙️ Datos del Proyecto")
    with st.expander("1. Hidráulica", expanded=True):
        litros = st.number_input("Consumo (L/día)", 100, 50000, 2000, step=100)
        horas = st.slider("Horas uso", 1, 24, 8)
    with st.expander("2. Calidad Agua", expanded=True):
        ppm = st.number_input("TDS (ppm)", 50, 8000, 800)
        dureza = st.number_input("Dureza (ºHf)", 0, 100, 35)
        temp = st.slider("Temperatura (ºC)", 5, 35, 15)
    with st.expander("3. Costes (€)"):
        coste_agua = st.number_input("Agua (€/m3)", 0.0, 10.0, 1.5)
        coste_sal = st.number_input("Sal (€/kg)", 0.0, 5.0, 0.45)
        coste_luz = st.number_input("Luz (€/kWh)", 0.0, 1.0, 0.20)
    
    st.markdown("---")
    btn_calc = st.button("CALCULAR SOLUCIÓN", use_container_width=True)

# RESULTADOS
if btn_calc:
    ro, descal, flow, opex, log, alerta = calcular_sistema(litros, ppm, dureza, temp, horas, coste_agua, coste_sal, coste_luz)
    
    if not ro:
        st.error("❌ **SIN SOLUCIÓN:** Parámetros fuera de rango.")
    else:
        # SECCIÓN 1: RECOMENDACIÓN
        st.subheader("✅ Solución Técnica")
        
        col_main, col_details = st.columns([1.5, 1])
        
        with col_main:
            st.info(f"🔵 **RO: {ro.nombre}**")
            m1, m2 = st.columns(2)
            m1.metric("Prod. Real", f"{int(flow['prod_real_dia'])} L/día")
            m2.metric("Eficiencia", f"{int(ro.eficiencia*100)}%")
            
            if descal:
                d, dias = descal
                # Cambiamos color de alerta si no llega a 5 días
                if alerta:
                    st.error(f"🟠 **PRE: {d.nombre}**")
                    st.write(alerta)
                else:
                    st.warning(f"🟠 **PRE: {d.nombre}**")
                
                d1, d2, d3 = st.columns(3)
                d1.metric("Resina", f"{d.litros_resina} L")
                d2.metric("Config", d.tipo)
                # Destacamos la autonomía
                d3.metric("Autonomía", f"{dias:.1f} días", "Objetivo > 5")
            else:
                st.success("🟢 **PRE:** No requerido")

        with col_details:
            st.markdown("#### 📦 Logística")
            if log["tanque"] > 0:
                st.metric("Depósito", f"{int(log['tanque'])} L", "Necesario", delta_color="inverse")
                st.caption("Para cubrir picos de demanda.")
            else:
                st.metric("Depósito", "Directo", "OK")

        st.markdown("---")

        # TABS
        t1, t2, t3 = st.tabs(["💰 Financiero", "⚙️ Balance Hídrico", "📋 Resumen"])
        
        with t1:
            c1, c2, c3 = st.columns(3)
            c1.metric("Agua", f"{opex['agua']:.0f} €/año")
            c2.metric("Sal", f"{opex['sal']:.0f} €/año")
            c3.metric("OPEX Total", f"{(opex['total']/365):.2f} €/día")
            
        with t2:
            st.write(f"- Entrada Red: **{int(flow['entrada'])} L/día**")
            st.write(f"- Producto: **{litros} L/día**")
            st.write(f"- Rechazo: **{int(flow['rechazo'])} L/día**")
            
        with t3:
            txt = f"""
            SOLUCIÓN AIMYWATER
            ------------------
            RO: {ro.nombre}
            PRE: {descal[0].nombre if descal else "N/A"}
               > Autonomía: {descal[1]:.1f} días
            DEPÓSITO: {int(log['tanque'])} L
            """
            st.code(txt)
else:
    st.info("👈 Introduce datos para calcular.")
