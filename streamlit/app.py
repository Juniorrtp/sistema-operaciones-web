import streamlit as st
from utils.styles import apply_custom_styles
# ============================================
# CONFIGURACIÓN DE PÁGINA
# ============================================

st.set_page_config(
    page_title="Sistema de Operaciones - Control de Aceros",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

apply_custom_styles()
# ============================================
# ESTILOS CSS PARA PERSONALIZAR EL SIDEBAR
# ============================================


# ============================================
# CONTENIDO DEL SIDEBAR (USANDO EL NATIVO)
# ============================================

with st.sidebar:
    # Título personalizado
    st.markdown("""
        <div class="sidebar-title">
            🏗️ SISTEMA DE<br>OPERACIONES
            <small>Control de Aceros</small>
        </div>
        <hr class="sidebar-divider">
    """, unsafe_allow_html=True)
    
    # El menú de radio se crea automáticamente con las páginas
    # Solo agregamos contenido adicional después
    
    # Separador
    st.markdown("---")
    
    # Estado de conexión
    try:
        import requests
        api_url = st.secrets.get("API_URL", "https://sistema-operaciones-web.onrender.com")
        response = requests.get(f"{api_url}/api/movimientos?limit=1", timeout=5)
        if response.status_code == 200:
            st.markdown("""
                <div class="connection-status online">
                    🟢 API Conectada
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
                <div class="connection-status offline">
                    🟡 API no disponible
                </div>
            """, unsafe_allow_html=True)
    except:
        st.markdown("""
            <div class="connection-status offline">
                🔴 Error de conexión
            </div>
        """, unsafe_allow_html=True)
    
    # Versión
    st.markdown("""
        <div class="sidebar-version">
            v1.0.0 · 2026
        </div>
    """, unsafe_allow_html=True)

# ============================================
# CONTENIDO PRINCIPAL
# ============================================

st.title("🏗️ Sistema de Operaciones")
st.markdown("---")

st.markdown("""
### 📋 Bienvenido al Sistema de Control de Aceros y Perforación

Este sistema te permite gestionar y analizar:

- 📊 **Dashboard** - Resumen ejecutivo con KPIs principales
- 🏆 **Rendimiento** - Análisis de aceros y operadores
- 🚜 **Equipos** - Estado y consumo por equipo
- 📅 **Avance Semanal** - Reporte gerencial de consumo y metros
- 📈 **Reporte Gerencial** - Análisis detallado para la gerencia

---

### 🚀 ¿Cómo usar el sistema?

1. **Selecciona una página** en el menú lateral izquierdo
2. **Aplica filtros** para ajustar los datos
3. **Visualiza** las tablas y gráficos
4. **Exporta** los reportes a Excel si lo necesitas

---

### 📊 Estado del sistema

- ✅ Módulo de Rendimiento completo
- ✅ Módulo de Equipos completo
- ✅ Avance Semanal completo
- 🚧 Dashboard en construcción
- 🚧 Reporte Gerencial en construcción
""")