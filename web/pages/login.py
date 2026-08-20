import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.auth import autenticar_usuario


def mostrar():
    """Página de login"""
    
    # Ocultar el menú lateral en la página de login
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            display: none;
        }
        .stApp {
            max-width: 400px;
            margin: 0 auto;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("### 🔐 Iniciar Sesión")
    st.markdown("Ingresa tus credenciales para acceder al sistema")
    
    # Limpiar cualquier sesión anterior
    if 'usuario' in st.session_state:
        del st.session_state.usuario
    
    st.markdown("---")
    
    with st.form("login_form"):
        username = st.text_input("👤 Usuario", placeholder="Ingresa tu usuario")
        password = st.text_input("🔑 Contraseña", type="password", placeholder="Ingresa tu contraseña")
        
        submitted = st.form_submit_button("🚪 Ingresar", type="primary", use_container_width=True)
        
        if submitted:
            if not username or not password:
                st.error("❌ Usuario y contraseña son obligatorios")
                return
            
            usuario = autenticar_usuario(username, password)
            
            if usuario:
                # Guardar usuario en sesión
                st.session_state.usuario = usuario
                st.success(f"✅ Bienvenido {usuario['nombre']} ({usuario['rol']})")
                st.balloons()
                st.rerun()
            else:
                st.error("❌ Usuario o contraseña incorrectos")
    
    st.markdown("---")
    st.caption("💡 Usuario por defecto: admin / contraseña: admin123")