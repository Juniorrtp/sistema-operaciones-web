import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.auth import obtener_usuarios, crear_usuario, actualizar_usuario, eliminar_usuario


def mostrar():
    """Página de gestión de usuarios"""
    
    # Verificar permiso
    if st.session_state.get('usuario', {}).get('rol') != 'admin':
        st.error("⛔ Acceso denegado. Solo administradores pueden gestionar usuarios.")
        return
    
    st.subheader("👥 Gestión de Usuarios")
    
    # ========== FORMULARIO AGREGAR ==========
    with st.expander("➕ Agregar Usuario", expanded=False):
        with st.form("form_usuario"):
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input("Usuario", placeholder="Ej: jperez")
                nombre = st.text_input("Nombre completo", placeholder="Ej: Juan Pérez")
            
            with col2:
                password = st.text_input("Contraseña", type="password", placeholder="Mínimo 6 caracteres")
                email = st.text_input("Email", placeholder="Ej: jperez@empresa.com")
            
            rol = st.selectbox(
                "Rol",
                options=["admin", "supervisor", "operador", "invitado"],
                help="admin: Todo | supervisor: Ver/editar, sin eliminar | operador: Solo ingresar | invitado: Solo ver"
            )
            
            if st.form_submit_button("💾 Guardar", type="primary"):
                if not username or not nombre or not password:
                    st.error("❌ Usuario, nombre y contraseña son obligatorios")
                elif len(password) < 6:
                    st.error("❌ La contraseña debe tener al menos 6 caracteres")
                else:
                    usuario_id = crear_usuario(username, password, nombre, rol, email)
                    if usuario_id:
                        st.success(f"✅ Usuario {username} creado correctamente")
                        st.rerun()
                    else:
                        st.error(f"❌ El usuario {username} ya existe")
    
    # ========== LISTA DE USUARIOS ==========
    st.markdown("---")
    st.markdown("### 📋 Usuarios Registrados")
    
    usuarios = obtener_usuarios()
    
    if usuarios:
        df = pd.DataFrame(usuarios)
        
        st.dataframe(
            df,
            column_config={
                'id': 'ID',
                'username': 'Usuario',
                'nombre': 'Nombre',
                'email': 'Email',
                'rol': st.column_config.TextColumn('Rol'),
                'activo': 'Activo',
                'created_at': 'Creado'
            },
            use_container_width=True,
            hide_index=True
        )
        
        # ========== SECCIÓN DE EDICIÓN ==========
        st.markdown("---")
        st.markdown("### ✏️ Editar/Eliminar Usuario")
        
        opciones = [f"{u['id']} - {u['username']} ({u['nombre']})" for u in usuarios]
        seleccion = st.selectbox("Seleccionar usuario", options=[""] + opciones)
        
        if seleccion:
            usuario_id = int(seleccion.split(" - ")[0])
            usuario = next(u for u in usuarios if u['id'] == usuario_id)
            
            with st.form("form_editar_usuario"):
                col1, col2 = st.columns(2)
                
                with col1:
                    nombre_edit = st.text_input("Nombre completo", value=usuario['nombre'])
                    email_edit = st.text_input("Email", value=usuario['email'] or '')
                
                with col2:
                    rol_edit = st.selectbox(
                        "Rol",
                        options=["admin", "supervisor", "operador", "invitado"],
                        index=["admin", "supervisor", "operador", "invitado"].index(usuario['rol'])
                    )
                    activo_edit = st.checkbox("Activo", value=usuario['activo'] == 1)
                    nueva_password = st.text_input("Nueva contraseña (dejar vacío para no cambiar)", type="password")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.form_submit_button("💾 Actualizar", type="primary"):
                        datos = {
                            'nombre': nombre_edit,
                            'email': email_edit,
                            'rol': rol_edit,
                            'activo': 1 if activo_edit else 0
                        }
                        if nueva_password and len(nueva_password) >= 6:
                            datos['password'] = nueva_password
                        
                        actualizar_usuario(usuario_id, datos)
                        st.success("✅ Usuario actualizado correctamente")
                        st.rerun()
                
                with col2:
                    if st.form_submit_button("🗑️ Eliminar", type="secondary"):
                        if usuario['username'] == 'admin':
                            st.error("❌ No se puede eliminar al usuario administrador principal")
                        else:
                            eliminar_usuario(usuario_id)
                            st.success("✅ Usuario eliminado correctamente")
                            st.rerun()
    else:
        st.info("No hay usuarios registrados")