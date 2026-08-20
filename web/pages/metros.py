import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.metros import (
    obtener_metros, contar_metros, eliminar_metro,
    obtener_tipos_perforacion
)
from core.aceros import obtener_opciones


# Cantidad de registros por página
REGISTROS_POR_PAGINA = 15


def mostrar():
    """Página de Metros - Tabla con filtros y paginación"""
    
    st.subheader("📏 Registros de Metros Perforados")
    
    # Estado para el formulario
    if 'metro_mostrar_formulario' not in st.session_state:
        st.session_state.metro_mostrar_formulario = False
    if 'metro_editar_id' not in st.session_state:
        st.session_state.metro_editar_id = None
    if 'metro_pagina' not in st.session_state:
        st.session_state.metro_pagina = 1
    
    # ========== FILTROS ==========
    with st.expander("🔍 Filtros de Búsqueda", expanded=True):
        
        col1, col2, col3, col4 = st.columns([1, 2, 1, 2])
        with col1:
            st.write("**Desde:**")
        with col2:
            fecha_desde = st.date_input(
                "Desde",
                value=datetime.now() - timedelta(days=30),
                label_visibility="collapsed",
                key="metro_fecha_desde"
            )
        with col3:
            st.write("**Hasta:**")
        with col4:
            fecha_hasta = st.date_input(
                "Hasta",
                value=datetime.now(),
                label_visibility="collapsed",
                key="metro_fecha_hasta"
            )
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            anos = obtener_opciones("ano")
            ano_seleccionado = st.multiselect("Año", anos, key="metro_filtro_ano")
        
        with col2:
            meses_orden = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
                          "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
            mes_seleccionado = st.multiselect("Mes", meses_orden, key="metro_filtro_mes")
        
        with col3:
            operadores = obtener_opciones("operador")
            operador_seleccionado = st.multiselect("Operador", operadores, key="metro_filtro_operador")
        
        with col4:
            equipos = obtener_opciones("equipo")
            equipo_seleccionado = st.multiselect("Equipo", equipos, key="metro_filtro_equipo")
        
        with st.expander("⚙️ Más filtros"):
            col1, col2 = st.columns(2)
            with col1:
                tipos = obtener_tipos_perforacion()
                tipo_seleccionado = st.multiselect("Tipo Perforación", tipos, key="metro_filtro_tipo")
            with col2:
                st.write("")
        
        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("🔍 Filtrar", use_container_width=True, type="primary"):
                st.session_state.metro_pagina = 1
                st.rerun()
        with col2:
            if st.button("🧹 Limpiar", use_container_width=True):
                for key in st.session_state.keys():
                    if key.startswith("metro_filtro_"):
                        if isinstance(st.session_state[key], list):
                            st.session_state[key] = []
                        elif isinstance(st.session_state[key], str):
                            st.session_state[key] = ""
                st.session_state.metro_pagina = 1
                st.rerun()
    
    # ========== BOTÓN AGREGAR ==========
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("➕ Agregar Metro", use_container_width=True, type="primary"):
            st.session_state.metro_mostrar_formulario = True
            st.session_state.metro_editar_id = None
            st.rerun()
    
    # ========== CARGAR DATOS ==========
    cargar_y_mostrar_tabla(
        fecha_desde, fecha_hasta,
        ano_seleccionado, mes_seleccionado,
        operador_seleccionado, equipo_seleccionado,
        tipo_seleccionado
    )
    
    # ========== FORMULARIO EMERGENTE ==========
    if st.session_state.get('metro_mostrar_formulario', False):
        from pages.metro_formulario import mostrar_formulario
        mostrar_formulario()


def cargar_y_mostrar_tabla(fecha_desde, fecha_hasta, anos, meses, operadores, equipos, tipos):
    """Carga datos y muestra la tabla con paginación"""
    
    try:
        # Preparar filtros
        filtros = {
            'fecha_desde': fecha_desde.strftime("%Y-%m-%d"),
            'fecha_hasta': fecha_hasta.strftime("%Y-%m-%d"),
            'ano': anos if anos else None,
            'mes': meses if meses else None,
            'operador': operadores if operadores else None,
            'equipo': equipos if equipos else None,
            'tipo_perforacion': tipos if tipos else None
        }
        filtros = {k: v for k, v in filtros.items() if v}
        
        # Contar total de registros
        total_registros = contar_metros(filtros)
        
        if total_registros == 0:
            st.info("ℹ️ No hay registros de metros que coincidan con los filtros")
            return
        
        # Calcular páginas
        total_paginas = (total_registros + REGISTROS_POR_PAGINA - 1) // REGISTROS_POR_PAGINA
        
        # Asegurar que la página actual sea válida
        if st.session_state.metro_pagina > total_paginas:
            st.session_state.metro_pagina = total_paginas
        if st.session_state.metro_pagina < 1:
            st.session_state.metro_pagina = 1
        
        # Calcular offset
        offset = (st.session_state.metro_pagina - 1) * REGISTROS_POR_PAGINA
        
        # Obtener datos paginados
        registros = obtener_metros(filtros, REGISTROS_POR_PAGINA, offset)
        
        if not registros:
            st.info("ℹ️ No hay registros en esta página")
            return
        
        df = pd.DataFrame(registros)
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        col1.metric("📊 Total registros", total_registros)
        col2.metric("📏 Total metros", f"{df['total_mp'].sum():,.0f}" if 'total_mp' in df and df['total_mp'].sum() else "0")
        col3.metric("📅 Promedio diario", f"{df['total_mp'].mean():.1f}" if 'total_mp' in df and df['total_mp'].mean() else "0")
        
        # ========== PAGINACIÓN ==========
        st.markdown(f"**Mostrando página {st.session_state.metro_pagina} de {total_paginas}**")
        
        col1, col2, col3 = st.columns([1, 1, 4])
        with col1:
            if st.button("⬅️ Anterior", use_container_width=True, disabled=st.session_state.metro_pagina <= 1):
                st.session_state.metro_pagina -= 1
                st.rerun()
        with col2:
            if st.button("Siguiente ➡️", use_container_width=True, disabled=st.session_state.metro_pagina >= total_paginas):
                st.session_state.metro_pagina += 1
                st.rerun()
        with col3:
            st.write(f"Total: {total_registros} registros | Página {st.session_state.metro_pagina} de {total_paginas}")
        
        # ========== TABLA CON BOTONES POR FILA ==========
        st.markdown("### 📋 Lista de Metros")
        
        for idx, row in df.iterrows():
            
            with st.container():
                # 🔥 Eliminamos la columna de total_mp
                col_id, col_fecha, col_mes, col_ano, col_turno, col_operador, col_equipo, col_tipo, col_acciones = st.columns(
                    [0.5, 0.9, 0.9, 0.6, 0.6, 1.2, 1.2, 1.1, 1.5]
                )
                
                with col_id:
                    st.code(row['id'], language="text")
                
                with col_fecha:
                    st.write(row['fecha'])
                
                with col_mes:
                    st.write(row['mes'])
                
                with col_ano:
                    st.write(row['ano'])
                
                with col_turno:
                    st.write(row['turno'] if row['turno'] else "")
                
                with col_operador:
                    st.write(row['operador'] if row['operador'] else "")
                
                with col_equipo:
                    st.write(row['equipo'] if row['equipo'] else "")
                
                with col_tipo:
                    st.write(row['tipo_perforacion'] if row['tipo_perforacion'] else "")
                
                with col_acciones:
                    col_edit, col_del = st.columns(2)
                    with col_edit:
                        if st.button("✏️", key=f"medit_{row['id']}", help="Editar"):
                            st.session_state.metro_mostrar_formulario = True
                            st.session_state.metro_editar_id = row['id']
                            st.rerun()
                    with col_del:
                        if st.button("🗑️", key=f"mdel_{row['id']}", help="Eliminar"):
                            st.session_state.metro_eliminar_id = row['id']
                            st.rerun()
            
            st.divider()
        
        # ========== CONFIRMACIÓN DE ELIMINACIÓN ==========
        if 'metro_eliminar_id' in st.session_state and st.session_state.metro_eliminar_id:
            st.warning(f"⚠️ ¿Estás seguro de eliminar el registro ID: {st.session_state.metro_eliminar_id}?")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ Sí, eliminar", type="primary", key="metro_confirmar_si"):
                    try:
                        eliminar_metro(st.session_state.metro_eliminar_id)
                        st.success(f"✅ Registro {st.session_state.metro_eliminar_id} eliminado")
                        st.session_state.metro_eliminar_id = None
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        st.session_state.metro_eliminar_id = None
            with col2:
                if st.button("❌ Cancelar", key="metro_confirmar_no"):
                    st.session_state.metro_eliminar_id = None
                    st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())