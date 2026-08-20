import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sys
import os
import tempfile
from core.exportar_pdf import generar_reporte_pdf

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.reporte_gerencial import (
    obtener_resumen_general,
    obtener_metros_por_tipo,
    obtener_consumo_por_familia,
    obtener_top_equipos_por_tipo,
    obtener_rendimiento_por_equipo,
    obtener_rendimiento_operadores_brocas,
    obtener_stock_critico
)
from core.exportar_pdf import generar_reporte_pdf


def mostrar():
    """Página de Reporte Gerencial"""
    
    st.subheader("📊 Reporte Gerencial Integral")
    
    # ========== FILTROS ==========
    col1, col2, col3 = st.columns([2, 2, 1])
    
    with col1:
        fecha_desde = st.date_input(
            "Fecha Desde",
            value=datetime.now() - timedelta(days=30),
            key="rg_fecha_desde"
        )
    
    with col2:
        fecha_hasta = st.date_input(
            "Fecha Hasta",
            value=datetime.now(),
            key="rg_fecha_hasta"
        )
    
    with col3:
        if st.button("🔄 Generar", type="primary", use_container_width=True):
            st.rerun()
    
    desde = fecha_desde.strftime("%Y-%m-%d")
    hasta = fecha_hasta.strftime("%Y-%m-%d")
    
    # ========== CARGAR DATOS ==========
    with st.spinner("Generando reporte..."):
        resumen = obtener_resumen_general(desde, hasta)
        metros_tipo = obtener_metros_por_tipo(desde, hasta)
        consumo_familia = obtener_consumo_por_familia(desde, hasta)
        top_equipos = obtener_top_equipos_por_tipo(desde, hasta, 3)
        rendimiento_equipos = obtener_rendimiento_por_equipo(desde, hasta)
        operadores = obtener_rendimiento_operadores_brocas(desde, hasta)
        stock_critico = obtener_stock_critico(5)
    
    # ========== 1. RESUMEN EJECUTIVO ==========
    st.markdown("### 📈 Resumen Ejecutivo")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            "📏 Total Metros",
            f"{resumen['metros']['total_metros']:,.0f}"
        )
    
    with col2:
        st.metric(
            "🔩 Total Consumos",
            f"{resumen['consumos']['total_consumo']:,.0f}"
        )
    
    with col3:
        eficiencia = resumen['metros']['total_metros'] / resumen['consumos']['total_consumo'] if resumen['consumos']['total_consumo'] > 0 else 0
        st.metric(
            "⚡ Eficiencia Global",
            f"{eficiencia:.2f} m/unidad"
        )
    
    with col4:
        st.metric(
            "🚜 Equipos Activos",
            f"{resumen['equipos']['total_equipos']:.0f}"
        )
    
    with col5:
        st.metric(
            "👥 Operadores",
            f"{resumen['operadores']['total_operadores']:.0f}"
        )
    
    st.markdown("---")
    
    # ========== 2. METROS POR TIPO + CONSUMO POR FAMILIA ==========
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📊 Metros por Tipo de Perforación")
        if metros_tipo:
            df = pd.DataFrame(metros_tipo)
            fig = px.bar(
                df,
                x='tipo',
                y='total_mp',
                title='',
                color='total_mp',
                color_continuous_scale='Blues',
                text='total_mp',
                labels={'tipo': 'Tipo', 'total_mp': 'Metros'}
            )
            fig.update_layout(height=300, coloraxis_showscale=False)
            fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos")
    
    with col2:
        st.markdown("### 📊 Consumo por Familia")
        if consumo_familia:
            df = pd.DataFrame(consumo_familia)
            fig = px.pie(
                df,
                values='total_consumo',
                names='familia',
                title=''
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos")
    
    st.markdown("---")
    
    # ========== 3. TOP EQUIPOS POR TIPO ==========
    st.markdown("### 🏗️ Top Equipos por Tipo de Perforación")
    
    if top_equipos:
        for tipo, equipos in top_equipos.items():
            if equipos:
                st.markdown(f"#### 🔹 {tipo}")
                df = pd.DataFrame(equipos)
                fig = px.bar(
                    df,
                    x='equipo',
                    y='total_mp',
                    title='',
                    color='total_mp',
                    color_continuous_scale='Greens',
                    text='total_mp',
                    labels={'equipo': 'Equipo', 'total_mp': 'Metros'}
                )
                fig.update_layout(height=250, coloraxis_showscale=False)
                fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos")
    
    st.markdown("---")
    
    # ========== 4. RENDIMIENTO POR EQUIPO ==========
    st.markdown("### 📋 Rendimiento por Equipo")
    st.caption("Metros por unidad consumida - Ordenado por rendimiento total")
    
    if rendimiento_equipos:
        equipos_ordenados = []
        for equipo, familias in rendimiento_equipos.items():
            if 'TOTAL' in familias:
                equipos_ordenados.append({
                    'equipo': equipo,
                    'rendimiento': familias['TOTAL']['rendimiento']
                })
        
        equipos_ordenados = sorted(equipos_ordenados, key=lambda x: x['rendimiento'], reverse=True)
        
        for eq in equipos_ordenados[:10]:
            equipo = eq['equipo']
            familias = rendimiento_equipos[equipo]
            
            with st.container():
                st.markdown(f"#### 🚜 {equipo} (Rendimiento: {familias['TOTAL']['rendimiento']:.2f} m/unidad)")
                
                df_familias = pd.DataFrame([
                    {
                        'Familia': f,
                        'Metros': d['metros'],
                        'Consumo': d['consumo'],
                        'Rendimiento': d['rendimiento']
                    }
                    for f, d in familias.items() if f != 'TOTAL'
                ])
                
                if not df_familias.empty:
                    st.dataframe(
                        df_familias,
                        column_config={
                            'Familia': 'Familia',
                            'Metros': 'Metros',
                            'Consumo': 'Consumo',
                            'Rendimiento': st.column_config.NumberColumn('Rendimiento', format="%.2f")
                        },
                        use_container_width=True,
                        hide_index=True
                    )
                st.divider()
    else:
        st.info("No hay datos")
    
    st.markdown("---")
    
    # ========== 5. RENDIMIENTO OPERADORES BROCAS ==========
    st.markdown("### 👷 Rendimiento de BROCAS por Operador")
    
    if operadores:
        for tipo, guardias in operadores.items():
            st.markdown(f"#### 🔹 {tipo}")
            
            for guardia, ops in guardias.items():
                st.markdown(f"**🛡️ Guardia {guardia}**")
                
                df = pd.DataFrame(ops)
                df = df.sort_values('rendimiento', ascending=False)
                
                st.dataframe(
                    df,
                    column_config={
                        'operador': 'Operador',
                        'brocas': 'Brocas',
                        'metros': 'Metros',
                        'rendimiento': st.column_config.NumberColumn('Rendimiento', format="%.2f")
                    },
                    use_container_width=True,
                    hide_index=True
                )
            
            st.divider()
    else:
        st.info("No hay datos")
    
    st.markdown("---")
    
    # ========== 6. STOCK CRÍTICO ==========
    st.markdown("### ⚠️ Stock Crítico")
    st.caption(f"Productos con stock menor o igual a 5 unidades")
    
    if stock_critico:
        df = pd.DataFrame(stock_critico)
        st.dataframe(
            df,
            column_config={
                'codigo': 'Código',
                'descripcion': 'Descripción',
                'stock': st.column_config.NumberColumn('Stock', format="%.0f")
            },
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("✅ No hay productos con stock crítico")
    
    # ========== BOTÓN EXPORTAR PDF ==========
    st.markdown("---")
    if st.button("📄 Exportar PDF", type="primary"):
        with st.spinner("Generando PDF..."):
            try:
                pdf_path = generar_reporte_pdf(
                    desde, hasta, resumen, metros_tipo, consumo_familia,
                    top_equipos, rendimiento_equipos, operadores, stock_critico
                )
                
                with open(pdf_path, 'rb') as f:
                    pdf_data = f.read()
                
                st.download_button(
                    label="📥 Descargar PDF",
                    data=pdf_data,
                    file_name=f"Reporte_Gerencial_{desde}_{hasta}.pdf",
                    mime="application/pdf"
                )
                st.success("✅ PDF generado correctamente")
                
                # Limpiar archivo temporal
                os.unlink(pdf_path)
                
            except Exception as e:
                st.error(f"❌ Error al generar PDF: {str(e)}")
                import traceback
                st.code(traceback.format_exc())