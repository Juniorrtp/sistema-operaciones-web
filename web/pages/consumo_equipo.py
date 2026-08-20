import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os
from collections import defaultdict  # 🔥 IMPORTANTE: Agregar esta línea

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.consumo_equipo import (
    obtener_filtros_consumo, obtener_consumo_equipo,
    obtener_entregas_descripcion, obtener_metros_equipo,
    obtener_resumen_compania, FAMILIAS
)

COLORES = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f']


def mostrar():
    """Página de Consumo por Equipo"""
    
    st.subheader("📊 Consumo de Aceros por Equipo")
    
    # ========== FILTROS ==========
    tipos, companias = obtener_filtros_consumo()
    
    col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1.5, 1])
    
    with col1:
        fecha_desde = st.date_input(
            "Fecha Desde",
            value=datetime.now() - timedelta(days=180),
            key="ce_fecha_desde"
        )
    
    with col2:
        fecha_hasta = st.date_input(
            "Fecha Hasta",
            value=datetime.now(),
            key="ce_fecha_hasta"
        )
    
    with col3:
        tipo_seleccionado = st.selectbox("Tipo Perforación", options=tipos, key="ce_tipo")
    
    with col4:
        compania_seleccionada = st.selectbox("Compañía", options=companias, key="ce_compania")
    
    with col5:
        if st.button("🔍 Actualizar", type="primary", use_container_width=True):
            st.rerun()
    
    # Preparar filtros
    desde = fecha_desde.strftime("%Y-%m-%d")
    hasta = fecha_hasta.strftime("%Y-%m-%d")
    tipo = None if tipo_seleccionado == "TODOS" else tipo_seleccionado
    compania = None if compania_seleccionada == "TODAS" else compania_seleccionada
    
    # ========== PESTAÑAS ==========
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Consumo por Equipo",
        "📦 Entregas por Descripción",
        "📏 Metros por Equipo",
        "🏢 Resumen por Compañía"
    ])
    
    with tab1:
        mostrar_consumo_equipo(desde, hasta, tipo, compania)
    
    with tab2:
        mostrar_entregas_descripcion(desde, hasta, tipo, compania)
    
    with tab3:
        mostrar_metros_equipo(desde, hasta, tipo, compania)
    
    with tab4:
        mostrar_resumen_compania(desde, hasta, tipo)


def mostrar_consumo_equipo(desde, hasta, tipo, compania):
    """Muestra gráficos de consumo por equipo por familia"""
    
    st.markdown("### 📊 Consumo por Equipo por Familia")
    
    datos = obtener_consumo_equipo(desde, hasta, tipo, compania)
    
    if not datos:
        st.info("No hay datos para los filtros seleccionados")
        return
    
    # Procesar datos por familia
    datos_por_familia = defaultdict(lambda: defaultdict(float))
    for row in datos:
        familia = row['familia'] or "OTROS"
        equipo = row['equipo']
        consumo = row['total_consumo'] or 0
        datos_por_familia[familia][equipo] = consumo
    
    # Mostrar gráficos en grid 2x2
    cols = st.columns(2)
    col_idx = 0
    
    for familia in FAMILIAS:
        familia_encontrada = None
        for key in datos_por_familia.keys():
            if familia.upper() == key.upper() or familia.upper() in key.upper():
                familia_encontrada = key
                break
        
        if familia_encontrada and datos_por_familia[familia_encontrada]:
            equipos_consumo = datos_por_familia[familia_encontrada]
            equipos_ordenados = sorted(equipos_consumo.items(), key=lambda x: x[1], reverse=True)[:10]
            
            if equipos_ordenados:
                df = pd.DataFrame(equipos_ordenados, columns=['Equipo', 'Consumo'])
                
                fig = px.bar(
                    df,
                    x='Consumo',
                    y='Equipo',
                    orientation='h',
                    title=f'{familia} - Consumo por Equipo',
                    color='Consumo',
                    color_continuous_scale='Blues',
                    text='Consumo'
                )
                fig.update_layout(
                    height=350,
                    margin=dict(l=10, r=10, t=40, b=10),
                    xaxis_title="Cantidad",
                    yaxis_title="",
                    coloraxis_showscale=False
                )
                fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
                
                with cols[col_idx % 2]:
                    st.plotly_chart(fig, use_container_width=True)
                col_idx += 1
        else:
            with cols[col_idx % 2]:
                st.info(f"No hay datos para {familia}")
            col_idx += 1


def mostrar_entregas_descripcion(desde, hasta, tipo, compania):
    """Muestra tabla de entregas por descripción"""
    
    st.markdown("### 📦 Entregas por Descripción")
    
    datos = obtener_entregas_descripcion(desde, hasta, tipo, compania)
    
    if not datos:
        st.info("No hay datos para los filtros seleccionados")
        return
    
    # Procesar datos
    descripciones_data = {}
    for row in datos:
        desc = row['descripcion'] or "SIN DESCRIPCIÓN"
        compania_nombre = row['compania'] or "SIN COMPAÑÍA"
        equipo = row['equipo'] or "SIN EQUIPO"
        total = row['total_entregado'] or 0
        
        if desc not in descripciones_data:
            descripciones_data[desc] = {}
        
        key = f"{compania_nombre}\n{equipo}"
        descripciones_data[desc][key] = total
    
    # Calcular totales y ordenar
    totales_desc = {}
    for desc, valores in descripciones_data.items():
        totales_desc[desc] = sum(valores.values())
    
    descripciones_top = sorted(totales_desc.keys(), key=lambda x: totales_desc[x], reverse=True)[:30]
    
    # Obtener todas las claves (compañía/equipo)
    all_keys = set()
    for desc in descripciones_top:
        all_keys.update(descripciones_data[desc].keys())
    all_keys = sorted(all_keys)
    
    # Construir DataFrame
    data = []
    for desc in descripciones_top:
        row = {'Descripción': desc}
        for key in all_keys:
            row[key] = descripciones_data[desc].get(key, 0)
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Configurar columnas
    column_config = {'Descripción': st.column_config.TextColumn('Descripción', width='large')}
    for key in all_keys:
        column_config[key] = st.column_config.NumberColumn(key)
    
    st.dataframe(
        df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        height=500
    )


def mostrar_metros_equipo(desde, hasta, tipo, compania):
    """Muestra tabla y gráfico de metros por equipo"""
    
    st.markdown("### 📏 Metros por Equipo")
    
    datos_tabla, datos_grafico = obtener_metros_equipo(desde, hasta, tipo, compania)
    
    if not datos_tabla:
        st.info("No hay datos para los filtros seleccionados")
        return
    
    # ===== TABLA =====
    equipos_data = defaultdict(lambda: defaultdict(float))
    fechas_set = set()
    
    for row in datos_tabla:
        equipo = row['equipo'] or "SIN EQUIPO"
        fecha = row['fecha']
        total = row['total_mp'] or 0
        equipos_data[equipo][fecha] = total
        fechas_set.add(fecha)
    
    fechas_list = sorted(fechas_set)
    equipos_list = sorted(equipos_data.keys())
    
    # Limitar para no saturar
    if len(equipos_list) > 20:
        equipos_list = equipos_list[:20]
    if len(fechas_list) > 20:
        fechas_list = fechas_list[-20:]
    
    # Construir DataFrame
    data = []
    for equipo in equipos_list:
        row = {'Equipo': equipo}
        for fecha in fechas_list:
            valor = equipos_data[equipo].get(fecha, 0)
            row[fecha] = int(valor) if valor > 0 else 0
        data.append(row)
    
    df = pd.DataFrame(data)
    
    # Configurar columnas
    column_config = {'Equipo': st.column_config.TextColumn('Equipo')}
    for fecha in fechas_list:
        column_config[fecha] = st.column_config.NumberColumn(fecha)
    
    st.dataframe(
        df,
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        height=400
    )
    
    # ===== GRÁFICO =====
    st.markdown("### 📊 Resumen de Metros por Equipo")
    
    if datos_grafico:
        df_graf = pd.DataFrame(datos_grafico[:15])
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='MP Producción',
            x=df_graf['equipo'],
            y=df_graf['mp_produccion'],
            marker_color='#1f77b4'
        ))
        fig.add_trace(go.Bar(
            name='MP Rimado',
            x=df_graf['equipo'],
            y=df_graf['mp_rimado'],
            marker_color='#ff7f0e'
        ))
        fig.add_trace(go.Bar(
            name='Total MP',
            x=df_graf['equipo'],
            y=df_graf['total_mp'],
            marker_color='#2ca02c'
        ))
        
        fig.update_layout(
            title='Metros por Equipo - Producción, Rimado y Total',
            xaxis_title='Equipo',
            yaxis_title='Metros',
            height=400,
            margin=dict(l=10, r=10, t=40, b=10),
            barmode='group'
        )
        
        st.plotly_chart(fig, use_container_width=True)


def mostrar_resumen_compania(desde, hasta, tipo):
    """Muestra resumen de metros por compañía"""
    
    st.markdown("### 🏢 Resumen de Metros por Compañía")
    
    datos = obtener_resumen_compania(desde, hasta, tipo)
    
    if not datos:
        st.info("No hay datos para los filtros seleccionados")
        return
    
    df = pd.DataFrame(datos)
    df = df[df['total_metros'] > 0]
    
    if df.empty:
        st.info("No hay datos de metros por compañía")
        return
    
    # Gráfico
    fig = px.bar(
        df,
        x='compania',
        y='total_metros',
        title='Metros por Compañía',
        color='total_metros',
        color_continuous_scale='Purples',
        text='total_metros',
        labels={'compania': 'Compañía', 'total_metros': 'Metros'}
    )
    fig.update_layout(
        height=400,
        margin=dict(l=10, r=10, t=40, b=10),
        coloraxis_showscale=False
    )
    fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
    
    # Tabla de datos
    st.dataframe(
        df,
        column_config={
            'compania': 'Compañía',
            'total_metros': st.column_config.NumberColumn('Total Metros')
        },
        use_container_width=True,
        hide_index=True
    )