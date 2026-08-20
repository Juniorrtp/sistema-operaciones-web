import streamlit as st

# ========== CONFIGURACIÓN DE LA PÁGINA ==========
st.set_page_config(
    page_title="Sistema de Gestión de Operaciones",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed"  # 🔥 Sidebar colapsado por defecto
)

# ========== CSS PARA OCULTAR SIDEBAR COMPLETAMENTE ==========
st.markdown("""
<style>
    /* 🔥 Ocultar completamente el sidebar */
    section[data-testid="stSidebar"] {
        display: none !important;
    }
    
    /* 🔥 Ocultar el menú de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stAppDeployButton {display: none !important;}
    
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .stDataFrame {
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
    
    .stMetric {
        background: #f8f9fa;
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# ========== VERIFICAR AUTENTICACIÓN ==========
if 'usuario' not in st.session_state:
    from pages.login import mostrar as mostrar_login
    mostrar_login()
    st.stop()

usuario = st.session_state.usuario
nombre_usuario = usuario.get('nombre', 'Usuario')
rol_usuario = usuario.get('rol', 'invitado')
es_admin = rol_usuario == 'admin'

# ========== TÍTULO PRINCIPAL ==========
st.title("📦 Sistema de Gestión de Operaciones")
st.markdown(f"👤 {nombre_usuario} | 🛡️ {rol_usuario.upper()}")
st.markdown("---")

# ========== MENÚ EN LA PARTE SUPERIOR (BOTONES) ==========
st.markdown("### 📋 Navegación")

# OPCIONES DEL MENÚ
menu_opciones = [
    "📋 Movimientos",
    "📏 Metros",
    "📊 Dashboard",
    "📈 Rendimiento",
    "📜 Histórico",
    "📅 Avance Semanal",
    "📊 Consumo Equipo",
    "📦 Conciliación Stock",
    "📊 Reporte Gerencial"
]

if es_admin:
    menu_opciones.append("⚙️ Configuración")
    menu_opciones.append("👥 Usuarios")

# 🔥 Dividir en columnas para los botones
# Calcular cuántas columnas necesitamos (máximo 4 por fila)
cols = st.columns(4)

# Botones de cerrar sesión y usuario en la parte superior derecha
col_user, col_logout = st.columns([6, 1])
with col_user:
    st.write(f"👤 {nombre_usuario} | 🛡️ {rol_usuario.upper()}")
with col_logout:
    if st.button("🚪 Salir", use_container_width=True):
        del st.session_state.usuario
        st.rerun()

st.markdown("---")

# 🔥 Mostrar botones en filas de 4
for i, opcion in enumerate(menu_opciones):
    col_idx = i % 4
    if col_idx == 0:
        cols = st.columns(4)
    
    with cols[col_idx]:
        if st.button(opcion, use_container_width=True, type="secondary"):
            st.session_state.pagina = opcion
            st.rerun()

st.markdown("---")

# ========== CARGAR PÁGINA SELECCIONADA ==========
pagina = st.session_state.get('pagina', "📋 Movimientos")

try:
    if pagina == "📋 Movimientos":
        from pages.movimientos import mostrar
        mostrar()
    elif pagina == "📏 Metros":
        from pages.metros import mostrar
        mostrar()
    elif pagina == "📊 Dashboard":
        from pages.dashboard import mostrar
        mostrar()
    elif pagina == "📈 Rendimiento":
        from pages.rendimiento import mostrar
        mostrar()
    elif pagina == "📜 Histórico":
        from pages.historico import mostrar
        mostrar()
    elif pagina == "📅 Avance Semanal":
        from pages.avance_semanal import mostrar
        mostrar()
    elif pagina == "📊 Consumo Equipo":
        from pages.consumo_equipo import mostrar
        mostrar()
    elif pagina == "📦 Conciliación Stock":
        from pages.conciliacion import mostrar
        mostrar()
    elif pagina == "📊 Reporte Gerencial":
        from pages.reporte_gerencial import mostrar
        mostrar()
    elif pagina == "⚙️ Configuración":
        from pages.configuracion import mostrar
        mostrar()
    elif pagina == "👥 Usuarios":
        from pages.usuarios import mostrar
        mostrar()
    else:
        st.warning("⚠️ Página no encontrada")
except Exception as e:
    st.error(f"❌ Error: {str(e)}")
    import traceback
    st.code(traceback.format_exc())