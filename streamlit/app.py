import streamlit as st
import os

# ============================================
# CONFIGURACIÓN DE PÁGINA
# ============================================

st.set_page_config(
    page_title="Sistema de Operaciones",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ============================================
# RUTA BASE DEL PROYECTO
# ============================================

# 🔥 Obtener la ruta del directorio donde está app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PAGES_DIR = os.path.join(BASE_DIR, "pages")

# 🔍 Debug: Mostrar rutas
print(f"BASE_DIR: {BASE_DIR}")
print(f"PAGES_DIR: {PAGES_DIR}")
print(f"Archivos en pages: {os.listdir(PAGES_DIR) if os.path.exists(PAGES_DIR) else 'No existe'}")

# ============================================
# ESTILOS CSS - OCULTAR SIDEBAR
# ============================================

st.markdown("""
    <style>
        /* 🔥 OCULTAR LA BARRA LATERAL COMPLETAMENTE */
        [data-testid="stSidebar"] {
            display: none !important;
            width: 0 !important;
            min-width: 0 !important;
        }
        
        [data-testid="collapsedControl"] {
            display: none !important;
        }
        
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
    label_visibility="collapsed",
    key="navegacion_superior"
)

st.markdown("---")

# ============================================
# FUNCIÓN PARA CARGAR PÁGINAS
# ============================================

def cargar_pagina(nombre_archivo):
    """Carga una página desde la carpeta pages"""
    ruta = os.path.join(PAGES_DIR, nombre_archivo)
    
    print(f"🔍 Intentando cargar: {ruta}")
    print(f"   ¿Existe?: {os.path.exists(ruta)}")
    
    if not os.path.exists(ruta):
        st.error(f"❌ No se encontró el archivo: {nombre_archivo}")
        st.write(f"**Ruta buscada:** `{ruta}`")
        st.write(f"**Archivos disponibles:**")
        if os.path.exists(PAGES_DIR):
            for f in os.listdir(PAGES_DIR):
                st.write(f"- {f}")
        return
    
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            codigo = f.read()
        
        # 🔥 Eliminar st.set_page_config si existe
        import re
        codigo = re.sub(r'st\.set_page_config\([^)]*\)', '', codigo)
        
        exec(codigo, {'__name__': '__main__'})
        
    except Exception as e:
        st.error(f"❌ Error al cargar {nombre_archivo}: {e}")
        import traceback
        st.code(traceback.format_exc())

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
    cargar_pagina("2_🏆_Rendimiento.py")

elif pagina == "🚜 Equipos":
    cargar_pagina("3_🚜_Equipos.py")

elif pagina == "📅 Avance Semanal":
    cargar_pagina("4_📅_Avance_Semanal.py")

elif pagina == "📈 Reporte Gerencial":
    cargar_pagina("5_📈_Reporte_Gerencial.py")