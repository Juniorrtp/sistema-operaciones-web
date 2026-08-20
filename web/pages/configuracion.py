import streamlit as st
import pandas as pd
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.configuracion import (
    obtener_operadores, guardar_operador, eliminar_operador,
    obtener_equipos, guardar_equipo, eliminar_equipo,
    obtener_aceros, guardar_acero, eliminar_acero,
    obtener_tipos_perforacion_opciones, obtener_familias_opciones, obtener_guardias_opciones
)


def mostrar():
    """Página de configuración - Catálogos"""
    
    st.subheader("⚙️ Configuración - Gestión de Catálogos")
    
    # Pestañas
    tab1, tab2, tab3 = st.tabs(["👥 Operadores", "🚜 Equipos", "🔩 Aceros"])
    
    with tab1:
        mostrar_operadores()
    
    with tab2:
        mostrar_equipos()
    
    with tab3:
        mostrar_aceros()


# ==================== OPERADORES ====================
def mostrar_operadores():
    """Muestra catálogo de operadores"""
    
    st.markdown("### 👥 Gestión de Operadores")
    
    # Buscador y botón agregar
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        busqueda = st.text_input("🔍 Buscar operador", placeholder="Nombre o guardia...", key="buscar_operador")
    with col2:
        if st.button("➕ Agregar", use_container_width=True, type="primary", key="btn_agregar_op"):
            st.session_state.mostrar_dialogo_operador = True
            st.session_state.editar_operador_id = None
            st.rerun()
    with col3:
        if st.button("🔄 Actualizar", use_container_width=True, key="btn_actualizar_op"):
            st.rerun()
    
    # Cargar datos
    operadores = obtener_operadores(busqueda if busqueda else None)
    
    if not operadores:
        st.info("No hay operadores registrados")
        return
    
    # Mostrar tabla con botones por fila
    df = pd.DataFrame(operadores)
    
    st.markdown("---")
    
    for idx, row in df.iterrows():
        col1, col2, col3, col4 = st.columns([0.5, 3, 2, 1.5])
        with col1:
            st.code(row['id'], language="text")
        with col2:
            st.write(row['nombre'])
        with col3:
            st.write(row['guardia'] if row['guardia'] else "-")
        with col4:
            col_edit, col_del = st.columns(2)
            with col_edit:
                if st.button("✏️", key=f"edit_op_{row['id']}"):
                    st.session_state.mostrar_dialogo_operador = True
                    st.session_state.editar_operador_id = row['id']
                    st.session_state.operador_datos = dict(row)
                    st.rerun()
            with col_del:
                if st.button("🗑️", key=f"del_op_{row['id']}"):
                    st.session_state.eliminar_op_id = row['id']
                    st.session_state.eliminar_op_nombre = row['nombre']
                    st.rerun()
        st.divider()
    
    # ========== CONFIRMACIÓN ELIMINAR ==========
    if st.session_state.get('eliminar_op_id'):
        st.warning(f"⚠️ ¿Eliminar operador '{st.session_state.eliminar_op_nombre}'?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="confirm_op_si"):
                try:
                    eliminar_operador(st.session_state.eliminar_op_id)
                    st.success("✅ Operador eliminado")
                    st.session_state.eliminar_op_id = None
                    st.session_state.eliminar_op_nombre = None
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        with col2:
            if st.button("❌ No", key="confirm_op_no"):
                st.session_state.eliminar_op_id = None
                st.session_state.eliminar_op_nombre = None
                st.rerun()
    
    # ========== DIÁLOGO DE OPERADOR ==========
    if st.session_state.get('mostrar_dialogo_operador', False):
        mostrar_dialogo_operador()


def mostrar_dialogo_operador():
    """Diálogo para agregar/editar operador"""
    
    es_edicion = st.session_state.get('editar_operador_id') is not None
    titulo = "✏️ Editar Operador" if es_edicion else "➕ Nuevo Operador"
    
    st.markdown(f"### {titulo}")
    
    if es_edicion:
        datos = st.session_state.get('operador_datos', {})
    else:
        datos = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        nombre = st.text_input(
            "👤 Nombre",
            value=datos.get('nombre', ''),
            placeholder="Ej: Juan Pérez",
            key="dialog_op_nombre"
        )
    
    with col2:
        guardias = obtener_guardias_opciones()
        guardia_idx = guardias.index(datos.get('guardia', '')) if datos.get('guardia') in guardias else 0
        guardia = st.selectbox(
            "🛡️ Guardia",
            options=guardias,
            index=guardia_idx,
            key="dialog_op_guardia"
        )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Guardar", type="primary", use_container_width=True, key="dialog_op_guardar"):
            if not nombre:
                st.error("❌ El nombre es obligatorio")
                return
            try:
                guardar_operador(
                    {'nombre': nombre, 'guardia': guardia},
                    st.session_state.get('editar_operador_id')
                )
                st.success("✅ Operador guardado correctamente")
                cerrar_dialogo_operador()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    with col2:
        if st.button("❌ Cancelar", use_container_width=True, key="dialog_op_cancelar"):
            cerrar_dialogo_operador()


def cerrar_dialogo_operador():
    st.session_state.mostrar_dialogo_operador = False
    st.session_state.editar_operador_id = None
    if 'operador_datos' in st.session_state:
        del st.session_state.operador_datos
    st.rerun()


# ==================== EQUIPOS ====================
def mostrar_equipos():
    """Muestra catálogo de equipos"""
    
    st.markdown("### 🚜 Gestión de Equipos")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        busqueda = st.text_input("🔍 Buscar equipo", placeholder="Equipo, compañía o tipo...", key="buscar_equipo")
    with col2:
        if st.button("➕ Agregar", use_container_width=True, type="primary", key="btn_agregar_eq"):
            st.session_state.mostrar_dialogo_equipo = True
            st.session_state.editar_equipo_id = None
            st.rerun()
    with col3:
        if st.button("🔄 Actualizar", use_container_width=True, key="btn_actualizar_eq"):
            st.rerun()
    
    equipos = obtener_equipos(busqueda if busqueda else None)
    
    if not equipos:
        st.info("No hay equipos registrados")
        return
    
    st.markdown("---")
    
    for idx, row in enumerate(equipos):
        col1, col2, col3, col4, col5, col6 = st.columns([0.5, 1.5, 1.5, 1.5, 0.8, 1.5])
        with col1:
            st.code(row['id'], language="text")
        with col2:
            st.write(row['equipo'])
        with col3:
            st.write(row['compania'] if row['compania'] else "-")
        with col4:
            st.write(row['tipo_perforacion'] if row['tipo_perforacion'] else "-")
        with col5:
            st.write(row['ceco_tipo'] if row['ceco_tipo'] else "-")
        with col6:
            col_edit, col_del = st.columns(2)
            with col_edit:
                if st.button("✏️", key=f"edit_eq_{row['id']}"):
                    st.session_state.mostrar_dialogo_equipo = True
                    st.session_state.editar_equipo_id = row['id']
                    st.session_state.equipo_datos = dict(row)
                    st.rerun()
            with col_del:
                if st.button("🗑️", key=f"del_eq_{row['id']}"):
                    st.session_state.eliminar_eq_id = row['id']
                    st.session_state.eliminar_eq_nombre = row['equipo']
                    st.rerun()
        st.divider()
    
    # ========== CONFIRMACIÓN ELIMINAR ==========
    if st.session_state.get('eliminar_eq_id'):
        st.warning(f"⚠️ ¿Eliminar equipo '{st.session_state.eliminar_eq_nombre}'?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="confirm_eq_si"):
                try:
                    eliminar_equipo(st.session_state.eliminar_eq_id)
                    st.success("✅ Equipo eliminado")
                    st.session_state.eliminar_eq_id = None
                    st.session_state.eliminar_eq_nombre = None
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        with col2:
            if st.button("❌ No", key="confirm_eq_no"):
                st.session_state.eliminar_eq_id = None
                st.session_state.eliminar_eq_nombre = None
                st.rerun()
    
    if st.session_state.get('mostrar_dialogo_equipo', False):
        mostrar_dialogo_equipo()


def mostrar_dialogo_equipo():
    """Diálogo para agregar/editar equipo"""
    
    es_edicion = st.session_state.get('editar_equipo_id') is not None
    titulo = "✏️ Editar Equipo" if es_edicion else "➕ Nuevo Equipo"
    
    st.markdown(f"### {titulo}")
    
    if es_edicion:
        datos = st.session_state.get('equipo_datos', {})
    else:
        datos = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        equipo = st.text_input(
            "🚜 Equipo",
            value=datos.get('equipo', ''),
            placeholder="Ej: Jumbo 123",
            key="dialog_eq_nombre"
        )
        compania = st.text_input(
            "🏢 Compañía",
            value=datos.get('compania', ''),
            placeholder="Ej: Minera XYZ",
            key="dialog_eq_compania"
        )
    
    with col2:
        tipos = obtener_tipos_perforacion_opciones()
        tipo_idx = tipos.index(datos.get('tipo_perforacion', '')) if datos.get('tipo_perforacion') in tipos else 0
        tipo = st.selectbox(
            "📌 Tipo Perforación",
            options=tipos,
            index=tipo_idx,
            key="dialog_eq_tipo"
        )
        ceco = st.text_input(
            "🔢 CECO",
            value=datos.get('ceco_tipo', ''),
            placeholder="Ej: 123456",
            key="dialog_eq_ceco"
        )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Guardar", type="primary", use_container_width=True, key="dialog_eq_guardar"):
            if not equipo:
                st.error("❌ El nombre del equipo es obligatorio")
                return
            try:
                guardar_equipo(
                    {
                        'equipo': equipo,
                        'compania': compania if compania else None,
                        'tipo_perforacion': tipo if tipo else None,
                        'ceco_tipo': ceco if ceco else None
                    },
                    st.session_state.get('editar_equipo_id')
                )
                st.success("✅ Equipo guardado correctamente")
                cerrar_dialogo_equipo()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    with col2:
        if st.button("❌ Cancelar", use_container_width=True, key="dialog_eq_cancelar"):
            cerrar_dialogo_equipo()


def cerrar_dialogo_equipo():
    st.session_state.mostrar_dialogo_equipo = False
    st.session_state.editar_equipo_id = None
    if 'equipo_datos' in st.session_state:
        del st.session_state.equipo_datos
    st.rerun()


# ==================== ACEROS ====================
def mostrar_aceros():
    """Muestra catálogo de aceros"""
    
    st.markdown("### 🔩 Gestión de Aceros")
    
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        busqueda = st.text_input("🔍 Buscar acero", placeholder="Código, descripción o familia...", key="buscar_acero")
    with col2:
        if st.button("➕ Agregar", use_container_width=True, type="primary", key="btn_agregar_ac"):
            st.session_state.mostrar_dialogo_acero = True
            st.session_state.editar_acero_id = None
            st.rerun()
    with col3:
        if st.button("🔄 Actualizar", use_container_width=True, key="btn_actualizar_ac"):
            st.rerun()
    
    aceros = obtener_aceros(busqueda if busqueda else None)
    
    if not aceros:
        st.info("No hay aceros registrados")
        return
    
    st.markdown("---")
    
    for idx, row in enumerate(aceros):
        col1, col2, col3, col4, col5, col6, col7, col8, col9 = st.columns([0.4, 0.8, 0.8, 1.8, 1.2, 0.8, 0.8, 0.8, 1.2])
        with col1:
            st.code(row['id'], language="text")
        with col2:
            st.write(row['codigo'] if row['codigo'] else "-")
        with col3:
            st.write(row['numparte'] if row['numparte'] else "-")
        with col4:
            st.write(row['descripcion'])
        with col5:
            st.write(row['proveedor'] if row['proveedor'] else "-")
        with col6:
            st.write(row['marca'] if row['marca'] else "-")
        with col7:
            st.write(row['familia'] if row['familia'] else "-")
        with col8:
            st.write(row['subfamilia'] if row['subfamilia'] else "-")
        with col9:
            col_edit, col_del = st.columns(2)
            with col_edit:
                if st.button("✏️", key=f"edit_ac_{row['id']}"):
                    st.session_state.mostrar_dialogo_acero = True
                    st.session_state.editar_acero_id = row['id']
                    st.session_state.acero_datos = dict(row)
                    st.rerun()
            with col_del:
                if st.button("🗑️", key=f"del_ac_{row['id']}"):
                    st.session_state.eliminar_ac_id = row['id']
                    st.session_state.eliminar_ac_nombre = row['descripcion']
                    st.rerun()
        st.divider()
    
    # ========== CONFIRMACIÓN ELIMINAR ==========
    if st.session_state.get('eliminar_ac_id'):
        st.warning(f"⚠️ ¿Eliminar acero '{st.session_state.eliminar_ac_nombre}'?")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Sí", key="confirm_ac_si"):
                try:
                    eliminar_acero(st.session_state.eliminar_ac_id)
                    st.success("✅ Acero eliminado")
                    st.session_state.eliminar_ac_id = None
                    st.session_state.eliminar_ac_nombre = None
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        with col2:
            if st.button("❌ No", key="confirm_ac_no"):
                st.session_state.eliminar_ac_id = None
                st.session_state.eliminar_ac_nombre = None
                st.rerun()
    
    if st.session_state.get('mostrar_dialogo_acero', False):
        mostrar_dialogo_acero()


def mostrar_dialogo_acero():
    """Diálogo para agregar/editar acero"""
    
    es_edicion = st.session_state.get('editar_acero_id') is not None
    titulo = "✏️ Editar Acero" if es_edicion else "➕ Nuevo Acero"
    
    st.markdown(f"### {titulo}")
    
    if es_edicion:
        datos = st.session_state.get('acero_datos', {})
    else:
        datos = {}
    
    col1, col2 = st.columns(2)
    
    with col1:
        codigo = st.text_input(
            "🔢 Código",
            value=datos.get('codigo', ''),
            placeholder="Ej: 12345",
            key="dialog_ac_codigo"
        )
        numparte = st.text_input(
            "📦 N° Parte",
            value=datos.get('numparte', ''),
            placeholder="Ej: PART-001",
            key="dialog_ac_numparte"
        )
        descripcion = st.text_input(
            "📝 Descripción",
            value=datos.get('descripcion', ''),
            placeholder="Ej: Barra de perforación 6m",
            key="dialog_ac_descripcion"
        )
        proveedor = st.text_input(
            "🏭 Proveedor",
            value=datos.get('proveedor', ''),
            placeholder="Ej: Proveedor S.A.",
            key="dialog_ac_proveedor"
        )
    
    with col2:
        marca = st.text_input(
            "🏷️ Marca",
            value=datos.get('marca', ''),
            placeholder="Ej: Sandvik",
            key="dialog_ac_marca"
        )
        familias = obtener_familias_opciones()
        familia_idx = familias.index(datos.get('familia', '')) if datos.get('familia') in familias else 0
        familia = st.selectbox(
            "👪 Familia",
            options=familias,
            index=familia_idx,
            key="dialog_ac_familia"
        )
        subfamilia = st.text_input(
            "📎 Subfamilia",
            value=datos.get('subfamilia', ''),
            placeholder="Ej: Integral",
            key="dialog_ac_subfamilia"
        )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Guardar", type="primary", use_container_width=True, key="dialog_ac_guardar"):
            if not descripcion:
                st.error("❌ La descripción es obligatoria")
                return
            try:
                guardar_acero(
                    {
                        'codigo': codigo if codigo else None,
                        'numparte': numparte if numparte else None,
                        'descripcion': descripcion,
                        'proveedor': proveedor if proveedor else None,
                        'marca': marca if marca else None,
                        'familia': familia if familia else None,
                        'subfamilia': subfamilia if subfamilia else None
                    },
                    st.session_state.get('editar_acero_id')
                )
                st.success("✅ Acero guardado correctamente")
                cerrar_dialogo_acero()
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    with col2:
        if st.button("❌ Cancelar", use_container_width=True, key="dialog_ac_cancelar"):
            cerrar_dialogo_acero()


def cerrar_dialogo_acero():
    st.session_state.mostrar_dialogo_acero = False
    st.session_state.editar_acero_id = None
    if 'acero_datos' in st.session_state:
        del st.session_state.acero_datos
    st.rerun()