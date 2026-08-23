"""
Dashboard Principal - Sistema de Operaciones
Equivalente a la aplicación principal en PyQt6
"""

import streamlit as st
from datetime import datetime

from utils.api_client import APIClient
from components.filtros import PanelFiltros
from views import rendimiento

# Configuración de la página
st.set_page_config(
    page_title="Sistema de Operaciones",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# INICIALIZACIÓN
# ============================================================

@st.cache_resource
def get_api_client():
    return APIClient()

api = get_api_client()

# ============================================================
# SIDEBAR - FILTROS (PanelFiltros en PyQt6)
# ============================================================

with st.sidebar:
    st.title("🎯 Sistema de Operaciones")
    st.markdown("---")
    
    filtros = PanelFiltros(api)
    filtros.render()
    
    st.markdown("---")
    st.caption(f"v1.0 | {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# ============================================================
# MAIN - TABS (RendimientoWidget en PyQt6)
# ============================================================

st.title("📊 Dashboard de Operaciones")

# Crear tabs
tabs = st.tabs([
    "📈 Rendimiento",
    "📦 Consumo",
    "📋 Estado Stock",
    "📅 Avance Semanal",
    "📄 Reporte Gerencial"
])

# TAB 1: RENDIMIENTO (RendimientoWidget)
with tabs[0]:
    # Obtener filtros actualizados como diccionario
    filtros_dict = filtros.obtener_filtros_dict()
    rendimiento.render(api, filtros_dict)

# TAB 2: CONSUMO (en desarrollo)
with tabs[1]:
    st.info("🚧 Módulo de Consumo en desarrollo")

# TAB 3: ESTADO STOCK (en desarrollo)
with tabs[2]:
    st.info("🚧 Módulo de Estado de Stock en desarrollo")

# TAB 4: AVANCE SEMANAL (en desarrollo)
with tabs[3]:
    st.info("🚧 Módulo de Avance Semanal en desarrollo")

# TAB 5: REPORTE GERENCIAL (en desarrollo)
with tabs[4]:
    st.info("🚧 Módulo de Reporte Gerencial en desarrollo")