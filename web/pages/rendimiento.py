import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.graficos import (
    obtener_rendimiento_aceros, obtener_tipos_perforacion_opciones,
    obtener_companias_opciones
)
from core.rendimiento_operador import (
    obtener_rendimiento_operadores, obtener_operadores_resumen,
    normalizar_tipo
)

MESES_LISTA = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
               "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]


def mostrar():
    """Página de Rendimiento de Aceros con pestañas"""
    
    st.subheader("📊 Rendimiento de Aceros")
    
    # ========== FILTROS ==========
    with st.expander("🔍 Filtros", expanded=True):
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ano_actual = datetime.now().year
            anos = [str(ano) for ano in range(ano_actual, ano_actual - 5, -1)]
            ano_seleccionado = st.selectbox("Año", options=anos, key="rend_ano")
        
        with col2:
            mes_seleccionado = st.selectbox("Mes", options=MESES_LISTA, key="rend_mes")
        
        with col3:
            companias = obtener_companias_opciones()
            compania_seleccionada = st.selectbox(
                "Compañía",
                options=["Todas"] + companias,
                key="rend_compania"
            )
        
        if st.button("🔍 Actualizar", type="primary", use_container_width=True):
            st.rerun()
    
    # Preparar filtros
    compania = None if compania_seleccionada == "Todas" else compania_seleccionada
    
    # ========== PESTAÑAS ==========
    tab1, tab2 = st.tabs(["📊 Rendimiento General", "👤 Rendimiento por Operador (BROCAS)"])
    
    with tab1:
        mostrar_rendimiento_general(ano_seleccionado, mes_seleccionado, compania)
    
    with tab2:
        mostrar_rendimiento_operadores(ano_seleccionado, mes_seleccionado, compania)


def mostrar_rendimiento_general(ano, mes, compania):
    """Muestra rendimiento general de aceros"""
    
    resultados = obtener_rendimiento_aceros(ano, mes, compania)
    
    if not resultados:
        st.info("No hay datos para los filtros seleccionados")
        return
    
    # Métricas
    total_familias = sum(len(datos) for datos in resultados.values())
    total_eficiencia = 0
    sobre_objetivo = 0
    bajo_80 = 0
    tipos_count = len(resultados)
    
    for tipo_perf, datos in resultados.items():
        for dato in datos:
            eficiencia = dato['eficiencia']
            if eficiencia > 0:
                total_eficiencia += eficiencia
                if eficiencia >= 100:
                    sobre_objetivo += 1
                elif eficiencia < 80:
                    bajo_80 += 1
    
    eficiencia_prom = total_eficiencia / total_familias if total_familias > 0 else 0
    
    # Métricas en una fila
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📊 Total Familias", total_familias)
    col2.metric("📈 Eficiencia Promedio", f"{eficiencia_prom:.1f}%")
    col3.metric("✅ Sobre Objetivo", sobre_objetivo)
    col4.metric("⚠️ Bajo 80%", bajo_80)
    col5.metric("📌 Tipos Perforación", tipos_count)
    
    # Tablas por tipo
    st.markdown("---")
    st.markdown("### 📋 Detalle por Tipo de Perforación")
    
    tipos = sorted(resultados.keys())
    tabs = st.tabs(tipos)
    
    for tab, tipo in zip(tabs, tipos):
        with tab:
            datos_tipo = sorted(resultados[tipo], key=lambda x: x['eficiencia'], reverse=True)
            df = pd.DataFrame(datos_tipo)
            
            st.dataframe(
                df,
                column_config={
                    'familia': 'Familia',
                    'entregado': 'Entregado',
                    'metros': 'Metros',
                    'rendimiento': 'Rendimiento',
                    'objetivo': 'Objetivo',
                    'eficiencia': st.column_config.NumberColumn('Eficiencia', format="%.1f%%")
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Gráfico de eficiencia
            fig = px.bar(
                df,
                x='familia',
                y='eficiencia',
                title=f'Eficiencia por Familia - {tipo}',
                color='eficiencia',
                color_continuous_scale=['red', 'yellow', 'green'],
                text=df['eficiencia'].apply(lambda x: f"{x:.1f}%"),
                labels={'familia': 'Familia', 'eficiencia': 'Eficiencia (%)'}
            )
            fig.update_layout(
                height=350,
                margin=dict(l=10, r=10, t=40, b=10),
                coloraxis_showscale=False
            )
            fig.update_traces(textposition='outside')
            st.plotly_chart(fig, use_container_width=True)


def mostrar_rendimiento_operadores(ano, mes, compania):
    """Muestra rendimiento de BROCAS por operador - Clasificado por tipo y guardia"""
    
    if compania is None:
        st.warning("⚠️ Selecciona una compañía específica para ver rendimiento por operador")
        return
    
    datos = obtener_rendimiento_operadores(ano, mes, compania)
    
    if not datos:
        st.info("No hay datos de BROCAS para los filtros seleccionados")
        return
    
    # ========== MÉTRICAS ==========
    total_operadores = sum(len(ops) for guardias in datos.values() for ops in guardias.values())
    total_brocas = sum(op['entregado'] for guardias in datos.values() for ops in guardias.values() for op in ops)
    total_metros = sum(op['metros'] for guardias in datos.values() for ops in guardias.values() for op in ops)
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("👥 Operadores", total_operadores)
    col2.metric("🔩 Brocas", f"{total_brocas:.0f}")
    col3.metric("📏 Metros", f"{total_metros:.0f}")
    col4.metric("📌 Tipos", len(datos))
    
    # ========== PESTAÑAS POR TIPO ==========
    st.markdown("---")
    st.markdown("### 👤 Rendimiento de BROCAS por Operador")
    
    tipos = sorted(datos.keys())
    tabs = st.tabs([f"🚜 {t}" for t in tipos])
    
    for tab, tipo in zip(tabs, tipos):
        with tab:
            guardias_data = datos[tipo]
            
            # Resumen por tipo
            total_brocas_tipo = sum(op['entregado'] for ops in guardias_data.values() for op in ops)
            total_metros_tipo = sum(op['metros'] for ops in guardias_data.values() for op in ops)
            rend_prom = total_metros_tipo / total_brocas_tipo if total_brocas_tipo > 0 else 0
            
            st.caption(f"📊 Total: {len(guardias_data)} guardias | 🔩 {total_brocas_tipo:.0f} brocas | 📏 {total_metros_tipo:.0f} metros | ⚡ Rend: {rend_prom:.1f}")
            
            # Tabla por guardia
            for guardia in sorted(guardias_data.keys(), key=lambda x: int(x) if x.isdigit() else 0):
                operadores = guardias_data[guardia]
                
                st.markdown(f"#### 🛡️ Guardia {guardia}")
                
                df = pd.DataFrame(operadores)
                df = df.sort_values('eficiencia', ascending=False)
                
                st.dataframe(
                    df,
                    column_config={
                        'operador': 'Operador',
                        'entregado': 'Brocas',
                        'metros': 'Metros',
                        'rendimiento': 'Rendimiento',
                        'objetivo': 'Objetivo',
                        'eficiencia': st.column_config.NumberColumn('Eficiencia', format="%.1f%%")
                    },
                    use_container_width=True,
                    hide_index=True
                )
                
                # Gráfico de eficiencia por operador
                fig = px.bar(
                    df,
                    x='operador',
                    y='eficiencia',
                    title=f'Eficiencia - Guardia {guardia}',
                    color='eficiencia',
                    color_continuous_scale=['red', 'yellow', 'green'],
                    text=df['eficiencia'].apply(lambda x: f"{x:.1f}%"),
                    labels={'operador': 'Operador', 'eficiencia': 'Eficiencia (%)'}
                )
                fig.update_layout(
                    height=300,
                    margin=dict(l=10, r=10, t=40, b=10),
                    coloraxis_showscale=False,
                    xaxis_tickangle=-45
                )
                fig.update_traces(textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
                
                st.divider()
    
    # ========== RESUMEN GENERAL POR GUARDIA ==========
    st.markdown("---")
    st.markdown("### 📊 Resumen General por Guardia")
    
    resumen_guardias = {}
    for tipo, guardias in datos.items():
        for guardia, operadores in guardias.items():
            if guardia not in resumen_guardias:
                resumen_guardias[guardia] = {
                    'operadores': 0,
                    'brocas': 0,
                    'metros': 0,
                    'mejor_efi': 0
                }
            resumen_guardias[guardia]['operadores'] += len(operadores)
            resumen_guardias[guardia]['brocas'] += sum(op['entregado'] for op in operadores)
            resumen_guardias[guardia]['metros'] += sum(op['metros'] for op in operadores)
            mejor = max(op['eficiencia'] for op in operadores) if operadores else 0
            resumen_guardias[guardia]['mejor_efi'] = max(resumen_guardias[guardia]['mejor_efi'], mejor)
    
    df_resumen = pd.DataFrame([
        {
            'Guardia': g,
            'Operadores': d['operadores'],
            'Brocas': d['brocas'],
            'Metros': d['metros'],
            'Mejor Eficiencia': d['mejor_efi']
        }
        for g, d in sorted(resumen_guardias.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0)
    ])
    
    st.dataframe(df_resumen, use_container_width=True, hide_index=True)