import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.graficos import (
    obtener_consumo_equipo, obtener_metros_equipo,
    obtener_resumen_compania, obtener_movimientos_mensuales,
    obtener_top_productos, obtener_tipos_perforacion_opciones,
    obtener_companias_opciones
)

# Familias para gráficos
FAMILIAS = ["SHANK", "ACOPLES", "BARRAS", "BROCAS", "RIMADORAS"]
COLORES = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']


def mostrar():
    """Página de Dashboard con gráficos"""
    
    st.subheader("📊 Dashboard - Análisis de Consumo y Metros")
    
    # ========== FILTROS ==========
    with st.expander("🔍 Filtros", expanded=True):
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            fecha_desde = st.date_input(
                "Fecha Desde",
                value=datetime.now() - timedelta(days=180),
                key="dash_fecha_desde"
            )
        
        with col2:
            fecha_hasta = st.date_input(
                "Fecha Hasta",
                value=datetime.now(),
                key="dash_fecha_hasta"
            )
        
        with col3:
            tipos = obtener_tipos_perforacion_opciones()
            tipo_seleccionado = st.selectbox(
                "Tipo Perforación",
                options=["TODOS"] + tipos,
                key="dash_tipo"
            )
        
        with col4:
            companias = obtener_companias_opciones()
            compania_seleccionada = st.selectbox(
                "Compañía",
                options=["TODAS"] + companias,
                key="dash_compania"
            )
        
        if st.button("🔍 Actualizar", type="primary", use_container_width=True):
            st.rerun()
    
    # Preparar filtros
    desde = fecha_desde.strftime("%Y-%m-%d")
    hasta = fecha_hasta.strftime("%Y-%m-%d")
    tipo = None if tipo_seleccionado == "TODOS" else tipo_seleccionado
    compania = None if compania_seleccionada == "TODAS" else compania_seleccionada
    
    # ========== KPI ==========
    st.markdown("### 📈 Resumen General")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Movimientos", "Cargando...")
    with col2:
        st.metric("📏 Total Metros", "Cargando...")
    with col3:
        st.metric("📥 Ingresos", "Cargando...")
    with col4:
        st.metric("📤 Salidas", "Cargando...")
    
    # ========== GRÁFICOS ==========
    st.markdown("---")
    st.markdown("### 📊 Consumo de Aceros por Equipo")
    
    # Cargar datos de consumo
    consumo_data = obtener_consumo_equipo(desde, hasta, tipo, compania)
    
    if consumo_data:
        # Procesar datos por familia
        datos_por_familia = {}
        for row in consumo_data:
            familia = row['familia'] or "OTROS"
            equipo = row['equipo']
            consumo = row['total_consumo'] or 0
            if familia not in datos_por_familia:
                datos_por_familia[familia] = {}
            datos_por_familia[familia][equipo] = consumo
        
        # Mostrar gráficos en grid 2x2
        cols = st.columns(2)
        col_idx = 0
        
        for familia in FAMILIAS:
            # Buscar familia en datos
            familia_encontrada = None
            for key in datos_por_familia.keys():
                if familia.upper() in key.upper() or key.upper() in familia.upper():
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
    else:
        st.info("No hay datos de consumo para los filtros seleccionados")
    
    # ========== METROS POR EQUIPO ==========
    st.markdown("---")
    st.markdown("### 📏 Metros por Equipo")
    
    metros_data = obtener_metros_equipo(desde, hasta, tipo, compania)
    
    if metros_data:
        df_metros = pd.DataFrame(metros_data)
        df_metros = df_metros.sort_values('total_mp', ascending=True).tail(15)
        
        fig = px.bar(
            df_metros,
            x='total_mp',
            y='equipo',
            orientation='h',
            title='Top 15 Equipos por Metros Perforados',
            color='total_mp',
            color_continuous_scale='Greens',
            text='total_mp',
            labels={'total_mp': 'Metros', 'equipo': 'Equipo'}
        )
        fig.update_layout(
            height=400,
            margin=dict(l=10, r=10, t=40, b=10),
            coloraxis_showscale=False
        )
        fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos de metros para los filtros seleccionados")
    
    # ========== RESUMEN POR COMPAÑÍA ==========
    st.markdown("---")
    st.markdown("### 🏢 Resumen por Compañía")
    
    resumen_data = obtener_resumen_compania(desde, hasta, tipo)
    
    if resumen_data:
        df_resumen = pd.DataFrame(resumen_data)
        df_resumen = df_resumen[df_resumen['total_metros'] > 0]
        
        fig = px.bar(
            df_resumen,
            x='compania',
            y='total_metros',
            title='Metros por Compañía',
            color='total_metros',
            color_continuous_scale='Purples',
            text='total_metros',
            labels={'compania': 'Compañía', 'total_metros': 'Metros'}
        )
        fig.update_layout(
            height=350,
            margin=dict(l=10, r=10, t=40, b=10),
            coloraxis_showscale=False
        )
        fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos de resumen por compañía")