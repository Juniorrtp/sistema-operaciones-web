import streamlit as st

# ============================================
# CONFIGURACIÓN DE PÁGINA
# ============================================

st.set_page_config(
    page_title="Sistema de Operaciones",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"  # 🔥 Barra lateral colapsada
)

# ============================================
# ESTILOS CSS - OCULTAR SIDEBAR Y NAVEGACIÓN SUPERIOR
# ============================================

st.markdown("""
    <style>
        /* 🔥 OCULTAR LA BARRA LATERAL COMPLETAMENTE */
        [data-testid="stSidebar"] {
            display: none !important;
        }
        
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        
        /* 🔥 Ocultar botón de hamburguesa */
        button[kind="header"] {
            display: none !important;
        }
        
        /* 🔥 Ocultar elementos por defecto */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
        
        /* 🔥 Ajustar el ancho del contenido */
        .main .block-container {
            padding-top: 1rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            max-width: 100% !important;
        }
        
        /* 🔥 Estilo para la navegación superior */
        .nav-container {
            display: flex;
            justify-content: center;
            gap: 10px;
            padding: 15px 0;
            border-bottom: 2px solid #2c3e50;
            margin-bottom: 20px;
            background: linear-gradient(180deg, #f8f9fa 0%, #ffffff 100%);
            border-radius: 10px;
        }
        
        .nav-item {
            padding: 10px 20px;
            border-radius: 8px;
            text-decoration: none;
            color: #2c3e50;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.2s ease;
            border: 2px solid transparent;
        }
        
        .nav-item:hover {
            background-color: #e8f4f8;
            border-color: #4472C4;
            color: #4472C4;
        }
        
        .nav-item.active {
            background: linear-gradient(135deg, #4472C4 0%, #2a5a9a 100%);
            color: #ffffff;
            border-color: #2a5a9a;
            box-shadow: 0 2px 8px rgba(68, 114, 196, 0.4);
        }
    </style>
""", unsafe_allow_html=True)

# ============================================
# TÍTULO
# ============================================

st.markdown("""
    <div style="text-align: center; padding: 10px 0 20px 0;">
        <h1 style="color: #2c3e50; margin: 0;">🏗️ Sistema de Operaciones</h1>
        <p style="color: #6c757d; font-size: 14px; margin: 5px 0 0 0;">Control de Aceros y Perforación</p>
    </div>
""", unsafe_allow_html=True)

# ============================================
# NAVEGACIÓN SUPERIOR
# ============================================

# Usar st.radio horizontal como navegación
pagina = st.radio(
    "Navegación",
    [
        "📊 Dashboard",
        "🏆 Rendimiento",
        "🚜 Equipos",
        "📅 Avance Semanal",
        "📈 Reporte Gerencial"
    ],
    horizontal=True,
    label_visibility="collapsed",  # 🔥 Ocultar el label "Navegación"
    key="navegacion_superior"
)

st.markdown("---")

# ============================================
# CONTENIDO SEGÚN PÁGINA SELECCIONADA
# ============================================

if pagina == "📊 Dashboard":
    st.info("👈 Selecciona una página en la barra superior para comenzar")
    st.markdown("### 📊 Bienvenido al Sistema de Operaciones")
    st.markdown("""
    Este sistema te permite:
    - 📊 Ver el **Dashboard** con KPIs principales
    - 🏆 Analizar el **Rendimiento** de aceros y operadores
    - 🚜 Revisar el estado de los **Equipos**
    - 📅 Generar el **Avance Semanal**
    - 📈 Crear el **Reporte Gerencial**
    """)

elif pagina == "🏆 Rendimiento":
    # Importar y ejecutar la página de Rendimiento
    exec(open("pages/2_🏆_Rendimiento.py", encoding="utf-8").read())

elif pagina == "🚜 Equipos":
    exec(open("pages/3_🚜_Equipos.py", encoding="utf-8").read())

elif pagina == "📅 Avance Semanal":
    exec(open("pages/4_📅_Avance_Semanal.py", encoding="utf-8").read())

elif pagina == "📈 Reporte Gerencial":
    exec(open("pages/5_📈_Reporte_Gerencial.py", encoding="utf-8").read())