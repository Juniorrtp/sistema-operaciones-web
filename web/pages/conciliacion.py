import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os
import io

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.conteo import (
    obtener_ubicaciones, obtener_productos_con_stock,
    obtener_ultimo_conteo_fisico, guardar_conteo_fisico,
    obtener_fechas_conteo, obtener_conteo_por_fecha
)


def mostrar():
    """Página de Conciliación de Stock - Tabla de doble entrada"""
    
    st.subheader("📊 Conciliación de Stock")
    
    tab1, tab2 = st.tabs(["📝 Conteo Actual", "📜 Histórico de Conteos"])
    
    with tab1:
        mostrar_conteo_actual()
    
    with tab2:
        mostrar_historico()


def mostrar_conteo_actual():
    """Muestra tabla de doble entrada para conteo físico"""
    
    st.caption("💡 Ingresa las cantidades físicas contadas en cada ubicación")
    
    # ========== FILTROS ==========
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.write("**📅 Fecha de Conteo**")
        fecha_conteo = st.date_input(
            "Fecha",
            value=datetime.now(),
            key="conc_fecha",
            label_visibility="collapsed"
        )
    
    with col2:
        st.write("**🔍 Filtro**")
        ubicaciones = obtener_ubicaciones()
        ubicacion_filtro = st.selectbox(
            "Ubicación",
            options=["TODAS"] + ubicaciones,
            key="conc_filtro_ubicacion",
            label_visibility="collapsed"
        )
    
    with col3:
        if st.button("🔄 Actualizar", type="primary", use_container_width=True):
            st.rerun()
    
    # ========== CARGAR DATOS ==========
    with st.spinner("Cargando datos..."):
        # 1. Productos con stock en el sistema
        df_productos = obtener_productos_con_stock()
        
        if df_productos.empty:
            st.info("No hay productos con stock en el sistema")
            return
        
        # 2. Último conteo guardado para esta fecha
        df_conteo_anterior = obtener_ultimo_conteo_fisico(
            fecha=fecha_conteo,
            ubicacion_filtro=None if ubicacion_filtro == "TODAS" else ubicacion_filtro
        )
    
    # ========== CONSTRUIR TABLA DE DOBLE ENTRADA ==========
    # Obtener todas las ubicaciones
    todas_ubicaciones = obtener_ubicaciones()
    
    # Si hay filtro de ubicación, solo mostrar esa columna
    if ubicacion_filtro != "TODAS":
        columnas_mostrar = [ubicacion_filtro]
    else:
        columnas_mostrar = todas_ubicaciones
    
    # Crear DataFrame base con productos
    df_base = df_productos.copy()
    
    # Agregar columnas para cada ubicación (inicializadas en 0)
    for ubicacion in columnas_mostrar:
        df_base[ubicacion] = 0
    
    # Si hay conteo anterior, llenar los valores
    if not df_conteo_anterior.empty:
        for _, row in df_conteo_anterior.iterrows():
            codigo = row['codigo']
            ubicacion = row['ubicacion']
            cantidad = row['cantidad']
            if ubicacion in df_base.columns:
                df_base.loc[df_base['codigo'] == codigo, ubicacion] = cantidad
    
    # Reordenar columnas: codigo, descripcion, [ubicaciones]
    columnas_final = ['codigo', 'descripcion'] + columnas_mostrar
    df_final = df_base[columnas_final]
    
    # ========== MOSTRAR TABLA EDITABLE ==========
    st.markdown("### 📋 Conteo Físico por Ubicación")
    st.caption("💡 Edita las cantidades en cada ubicación. Solo se guardan las que tengan valor > 0")
    
    # Configurar columnas
    column_config = {
        'codigo': st.column_config.TextColumn('Código', disabled=True, width='small'),
        'descripcion': st.column_config.TextColumn('Descripción', disabled=True, width='medium'),
    }
    
    for ubicacion in columnas_mostrar:
        column_config[ubicacion] = st.column_config.NumberColumn(
            ubicacion,
            min_value=0,
            step=1,
            width='small'
        )
    
    # Mostrar editor
    edited_df = st.data_editor(
        df_final,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        height=500,
        key="conc_editor"
    )
    
    # ========== MÉTRICAS ==========
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    total_productos = len(edited_df)
    col1.metric("📦 Productos", total_productos)
    
    # Calcular total por ubicación
    total_por_ubicacion = {}
    for ubicacion in columnas_mostrar:
        total_por_ubicacion[ubicacion] = edited_df[ubicacion].sum() if ubicacion in edited_df.columns else 0
    
    total_general = sum(total_por_ubicacion.values())
    col2.metric("📝 Total Contado", f"{total_general:.0f}")
    
    # Mostrar resumen por ubicación
    resumen_text = " | ".join([f"{k}: {v:.0f}" for k, v in total_por_ubicacion.items() if v > 0])
    col3.metric("📍 Por Ubicación", resumen_text if resumen_text else "Sin datos")
    
    # ========== BOTONES ==========
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 3])
    
    with col1:
        if st.button("💾 Guardar Conteo", type="primary", use_container_width=True):
            observacion = st.text_input("Observación (opcional)", key="conc_observacion")
            
            # Convertir tabla de doble entrada a formato largo
            registros = []
            for _, row in edited_df.iterrows():
                codigo = row['codigo']
                descripcion = row['descripcion']
                for ubicacion in columnas_mostrar:
                    cantidad = row.get(ubicacion, 0)
                    if cantidad > 0:
                        registros.append({
                            'codigo': codigo,
                            'descripcion': descripcion,
                            'ubicacion': ubicacion,
                            'cantidad': cantidad
                        })
            
            if registros:
                df_guardar = pd.DataFrame(registros)
                registros_guardados = guardar_conteo_fisico(
                    df_guardar,
                    fecha_conteo,
                    usuario=st.session_state.get('usuario', 'admin'),
                    observacion=observacion
                )
                st.success(f"✅ Conteo guardado correctamente ({registros_guardados} registros)")
                st.balloons()
                st.rerun()
            else:
                st.warning("⚠️ No hay datos de conteo para guardar (todas las cantidades son 0)")
    
    with col2:
        if st.button("🔄 Recalcular", use_container_width=True):
            st.rerun()
    
    with col3:
        if st.button("📊 Exportar Excel", use_container_width=True):
            exportar_excel(edited_df, fecha_conteo)


def exportar_excel(df, fecha):
    """Exporta el conteo a Excel"""
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=f'Conteo_{fecha.strftime("%Y%m%d")}', index=False)
        
        st.download_button(
            label="📥 Descargar Excel",
            data=output.getvalue(),
            file_name=f"Conteo_Stock_{fecha.strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="conc_download"
        )
        
    except Exception as e:
        st.error(f"❌ Error al exportar: {str(e)}")


def mostrar_historico():
    """Muestra el histórico de conteos"""
    
    st.markdown("### 📜 Histórico de Conteos")
    
    # ========== FILTROS ==========
    col1, col2 = st.columns(2)
    
    with col1:
        ubicaciones = obtener_ubicaciones()
        ubicacion_filtro = st.selectbox(
            "Ubicación",
            options=["TODAS"] + ubicaciones,
            key="hist_ubicacion"
        )
    
    with col2:
        fechas = obtener_fechas_conteo(
            None if ubicacion_filtro == "TODAS" else ubicacion_filtro
        )
        if fechas:
            opciones_fechas = [row['fecha'] for row in fechas]
            fecha_seleccionada = st.selectbox(
                "Fecha",
                options=opciones_fechas,
                key="hist_fecha"
            )
        else:
            st.info("No hay conteos registrados")
            return
    
    # ========== CARGAR DATOS ==========
    if fecha_seleccionada:
        detalle = obtener_conteo_por_fecha(
            fecha_seleccionada,
            None if ubicacion_filtro == "TODAS" else ubicacion_filtro
        )
        
        if detalle:
            df = pd.DataFrame(detalle)
            
            # Crear tabla pivote (doble entrada)
            pivot = df.pivot_table(
                index=['codigo', 'descripcion'],
                columns='ubicacion',
                values='cantidad',
                fill_value=0
            ).reset_index()
            
            # Reordenar columnas
            todas_ubicaciones = obtener_ubicaciones()
            for ubicacion in todas_ubicaciones:
                if ubicacion not in pivot.columns:
                    pivot[ubicacion] = 0
            
            # Calcular total
            pivot['TOTAL'] = pivot[todas_ubicaciones].sum(axis=1)
            
            st.markdown(f"#### 📋 Conteo del {fecha_seleccionada}")
            
            # Configurar columnas
            column_config = {
                'codigo': st.column_config.TextColumn('Código', width='small'),
                'descripcion': st.column_config.TextColumn('Descripción', width='medium'),
                'TOTAL': st.column_config.NumberColumn('TOTAL', width='small')
            }
            for ubicacion in todas_ubicaciones:
                column_config[ubicacion] = st.column_config.NumberColumn(ubicacion, width='small')
            
            st.dataframe(
                pivot,
                column_config=column_config,
                use_container_width=True,
                hide_index=True
            )
            
            # Botón para cargar este conteo en la pestaña actual
            if st.button("📥 Cargar este conteo para editar"):
                st.session_state['conc_fecha'] = datetime.strptime(fecha_seleccionada, "%Y-%m-%d")
                st.rerun()