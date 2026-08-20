import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.database import get_db
from core.movimientos import obtener_movimientos, eliminar_movimiento
from core.aceros import obtener_opciones


def mostrar():
    """Página de movimientos - Adaptada para móvil"""
    
    st.subheader("📋 Movimientos")
    
    if 'mostrar_formulario' not in st.session_state:
        st.session_state.mostrar_formulario = False
    
    # ========== FILTROS (colapsados en móvil) ==========
    with st.expander("🔍 Filtros", expanded=False):
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            fecha_desde = st.date_input(
                "Desde",
                value=datetime.now() - timedelta(days=30),
                key="mov_fecha_desde"
            )
            anos = obtener_opciones("ano")
            ano_seleccionado = st.multiselect("Año", anos, key="mov_ano")
            movimientos = ["INGRESO", "SALIDA"]
            movimiento_seleccionado = st.multiselect("Movimiento", movimientos, key="mov_movimiento")
        
        with col2:
            fecha_hasta = st.date_input(
                "Hasta",
                value=datetime.now(),
                key="mov_fecha_hasta"
            )
            meses_orden = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
                          "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
            mes_seleccionado = st.multiselect("Mes", meses_orden, key="mov_mes")
            estados = obtener_opciones("estado")
            estado_seleccionado = st.multiselect("Estado", estados, key="mov_estado")
        
        with col3:
            with st.expander("⚙️ Más filtros", expanded=False):
                operadores = obtener_opciones("operador")
                operador_seleccionado = st.multiselect("Operador", operadores, key="mov_operador")
                equipos = obtener_opciones("equipo")
                equipo_seleccionado = st.multiselect("Equipo", equipos, key="mov_equipo")
                guia_busqueda = st.text_input("🔍 Guía", placeholder="Buscar...", key="mov_guia")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Filtrar", use_container_width=True, type="primary"):
                st.rerun()
        with col2:
            if st.button("🧹 Limpiar", use_container_width=True):
                for key in list(st.session_state.keys()):
                    if key.startswith("mov_"):
                        if isinstance(st.session_state[key], list):
                            st.session_state[key] = []
                        elif isinstance(st.session_state[key], str):
                            st.session_state[key] = ""
                st.rerun()
    
    # ========== BOTÓN AGREGAR ==========
    if st.button("➕ Agregar Movimiento", use_container_width=True, type="primary"):
        st.session_state.mostrar_formulario = True
        st.session_state.editar_id = None
        st.rerun()
    
    # ========== CARGAR DATOS ==========
    cargar_y_mostrar_tabla(
        fecha_desde, fecha_hasta,
        ano_seleccionado, mes_seleccionado,
        movimiento_seleccionado, estado_seleccionado,
        operador_seleccionado, equipo_seleccionado,
        guia_busqueda
    )
    
    # ========== FORMULARIO EMERGENTE ==========
    if st.session_state.get('mostrar_formulario', False):
        from pages.formulario import mostrar_formulario
        mostrar_formulario()


def cargar_y_mostrar_tabla(fecha_desde, fecha_hasta, anos, meses, movimientos, estados, operadores, equipos, guia):
    """Carga datos y muestra la tabla con botones Editar/Eliminar por fila"""
    
    try:
        filtros = {
            'fecha_desde': fecha_desde.strftime("%Y-%m-%d"),
            'fecha_hasta': fecha_hasta.strftime("%Y-%m-%d"),
            'ano': anos if anos else None,
            'mes': meses if meses else None,
            'movimiento': movimientos if movimientos else None,
            'estado': estados if estados else None,
            'operador': operadores if operadores else None,
            'equipo': equipos if equipos else None,
            'guia': guia if guia else None
        }
        filtros = {k: v for k, v in filtros.items() if v}
        
        registros = obtener_movimientos(filtros)
        
        if not registros:
            st.info("ℹ️ No hay registros")
            return
        
        df = pd.DataFrame(registros)
        
        # ========== MÉTRICAS ==========
        col1, col2, col3 = st.columns(3)
        col1.metric("📊 Total", len(df))
        col2.metric("📥 Ingresos", len(df[df['movimiento'] == 'INGRESO']) if 'movimiento' in df else 0)
        col3.metric("📤 Salidas", len(df[df['movimiento'] == 'SALIDA']) if 'movimiento' in df else 0)
        
        st.markdown("---")
        st.markdown("### 📋 Lista de Movimientos")
        
        # ========== MOSTRAR CADA FILA CON BOTONES ==========
        for idx, row in df.iterrows():
            
            with st.container():
                # 🔥 Mostrar información compacta
                col1, col2, col3, col4, col5 = st.columns([1.5, 1.5, 1.5, 1, 1.5])
                
                with col1:
                    st.write(f"**ID:** {row['id']}")
                    st.write(f"📅 {row['fecha']}")
                
                with col2:
                    st.write(f"**{row['movimiento']}**")
                    st.write(f"📋 {row['guia'] if row['guia'] else '-'}")
                
                with col3:
                    st.write(f"👤 {row['operador'] if row['operador'] else '-'}")
                    st.write(f"🚜 {row['equipo'] if row['equipo'] else '-'}")
                
                with col4:
                    st.write(f"🏷️ {row['estado'] if row['estado'] else '-'}")
                    st.write(f"📆 {row['mes']} {row['ano']}")
                
                with col5:
                    # 🔥 Botones de acción en la misma fila
                    col_edit, col_del = st.columns(2)
                    with col_edit:
                        if st.button("✏️", key=f"edit_{row['id']}", help="Editar"):
                            st.session_state.mostrar_formulario = True
                            st.session_state.editar_id = row['id']
                            st.rerun()
                    with col_del:
                        if st.button("🗑️", key=f"del_{row['id']}", help="Eliminar"):
                            # Confirmar eliminación
                            if st.button("⚠️ Confirmar", key=f"confirm_{row['id']}"):
                                try:
                                    eliminar_movimiento(row['id'])
                                    st.success(f"✅ Registro {row['id']} eliminado")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                
                st.divider()
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())