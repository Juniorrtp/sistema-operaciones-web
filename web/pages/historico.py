import streamlit as st
import pandas as pd
import plotly.express as px
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from core.historico import (
    obtener_companias, obtener_equipos_por_compania,
    obtener_objetivos, obtener_ultimo_mes_ano,
    obtener_brazos_equipo, calcular_estado_actual,
    calcular_rendimiento_mes, obtener_historico_equipo
)

TIPOS_ACERO = ["SHANK", "ACOPLES", "BARRAS", "RIMADORAS", "BROCAS"]
FAMILIA_MAP = {
    "SHANK": "SHANK",
    "COUPLING": "ACOPLES",
    "BARRA": "BARRAS",
    "RIMADORAS": "RIMADORAS",
    "BROCAS": "BROCAS"
}


def mostrar():
    """Página de Histórico - Estado Actual y Histórico de Consumo"""
    
    st.subheader("📊 Histórico de Consumo")
    
    tab1, tab2 = st.tabs(["📊 Estado Actual de Aceros", "📜 Histórico de Consumo"])
    
    with tab1:
        mostrar_estado_actual()
    
    with tab2:
        mostrar_historico_consumo()


def mostrar_estado_actual():
    """Muestra estado actual de aceros por equipo y brazo - Agrupado por tipo"""
    
    st.markdown("### 📊 Estado Actual de Aceros por Equipo y Brazo")
    
    # ========== FILTROS ==========
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        companias = obtener_companias()
        compania_seleccionada = st.selectbox(
            "Compañía",
            options=["TODAS"] + companias,
            key="estado_compania"
        )
    
    with col2:
        brazo_opciones = ["TODOS", "BRAZO 1", "BRAZO 2", "SIN BRAZO"]
        brazo_seleccionado = st.selectbox(
            "Brazo",
            options=brazo_opciones,
            key="estado_brazo"
        )
    
    with col3:
        if st.button("🔄 Actualizar", type="primary", use_container_width=True):
            st.rerun()
    
    # Preparar filtros
    compania_filtro = None if compania_seleccionada == "TODAS" else compania_seleccionada
    brazo_filtro = None if brazo_seleccionado == "TODOS" else (
        "" if brazo_seleccionado == "SIN BRAZO" else brazo_seleccionado
    )
    
    # ========== CARGAR DATOS ==========
    equipos = obtener_equipos_por_compania(compania_filtro)
    objetivos = obtener_objetivos()
    ultimo_ano, ultimo_mes = obtener_ultimo_mes_ano()
    
    if not equipos:
        st.info("No hay equipos para la compañía seleccionada")
        return
    
    # Estructuras para las dos tablas
    datos_actual = {}
    datos_mes = {}
    
    for row in equipos:
        equipo = row['equipo']
        tipo_perf = row['tipo_perforacion'] or "SIN TIPO"
        
        brazos = obtener_brazos_equipo(equipo)
        
        for brazo in brazos:
            if brazo_filtro is not None and brazo != brazo_filtro:
                continue
            
            clave = f"{equipo}_{brazo}" if brazo else equipo
            brazo_label = brazo if brazo else "ÚNICO"
            
            if clave not in datos_actual:
                datos_actual[clave] = {
                    "tipo": tipo_perf,
                    "equipo": equipo,
                    "brazo": brazo_label,
                    "brazo_raw": brazo
                }
                datos_mes[clave] = {
                    "tipo": tipo_perf,
                    "equipo": equipo,
                    "brazo": brazo_label,
                    "brazo_raw": brazo
                }
            
            for tipo_acero in TIPOS_ACERO:
                familia = FAMILIA_MAP.get(tipo_acero, tipo_acero)
                
                objetivo_clave = (tipo_perf.upper(), familia.upper())
                objetivo = objetivos.get(objetivo_clave, 0)
                
                if tipo_acero == "BARRA" and "TALADROS LARGOS" in tipo_perf.upper():
                    objetivo *= 10
                
                # Estado Actual
                estado = calcular_estado_actual(equipo, brazo, familia, objetivo, ultimo_ano, ultimo_mes)
                datos_actual[clave][tipo_acero] = {
                    'metros': estado['metros'],
                    'objetivo': estado['objetivo'],
                    'porcentaje': estado['porcentaje'],
                    'estado': estado['estado']
                }
                
                # Rendimiento del Mes
                metros_mes, consumo_mes, rendimiento, eficiencia = calcular_rendimiento_mes(
                    equipo, brazo, familia, tipo_acero, objetivo, ultimo_ano, ultimo_mes
                )
                datos_mes[clave][tipo_acero] = {
                    'metros': metros_mes,
                    'consumo': consumo_mes,
                    'rendimiento': rendimiento,
                    'eficiencia': eficiencia,
                    'objetivo': objetivo
                }
    
    if not datos_actual:
        st.info("No hay datos para los filtros seleccionados")
        return
    
    # ========== TABLA 1: ESTADO ACTUAL (Agrupado por tipo) ==========
    st.markdown("### 📋 Estado Actual")
    st.caption("💡 Muestra: **Metros | Porcentaje**")
    
    # Agrupar por tipo
    agrupado_actual = {}
    for clave, info in datos_actual.items():
        tipo = info.get("tipo", "OTRO")
        if tipo not in agrupado_actual:
            agrupado_actual[tipo] = []
        agrupado_actual[tipo].append((clave, info))
    
    # Crear una tabla por cada tipo
    for tipo_perf in sorted(agrupado_actual.keys()):
        st.markdown(f"#### 🔹 {tipo_perf}")
        
        rows_actual = []
        for clave, info in sorted(agrupado_actual[tipo_perf]):
            equipo = info['equipo']
            brazo = info['brazo']
            texto_equipo = f"{equipo}\n({brazo})" if brazo != "ÚNICO" else equipo
            
            row = {'Equipo': texto_equipo}
            for tipo_acero in TIPOS_ACERO:
                dato = info.get(tipo_acero, {'porcentaje': 0, 'estado': 'SIN DATOS', 'metros': 0})
                # 🔥 Mostrar: Metros | Porcentaje
                if dato['estado'] == "SIN DATOS" or dato['porcentaje'] == 0:
                    row[tipo_acero] = "-"
                else:
                    row[tipo_acero] = f"{dato['metros']:.0f} | {dato['porcentaje']:.0f}%"
            
            rows_actual.append(row)
        
        df_actual = pd.DataFrame(rows_actual)
        st.dataframe(df_actual, use_container_width=True, hide_index=True)
        st.divider()
    
    # ========== TABLA 2: RENDIMIENTO DEL MES ==========
    if ultimo_ano and ultimo_mes:
        st.markdown(f"### 📋 Rendimiento del Último Mes ({ultimo_mes} {ultimo_ano})")
        st.caption("💡 Muestra: **Cantidad | Eficiencia**")
        
        # Agrupar por tipo
        agrupado_mes = {}
        for clave, info in datos_mes.items():
            tipo = info.get("tipo", "OTRO")
            if tipo not in agrupado_mes:
                agrupado_mes[tipo] = []
            agrupado_mes[tipo].append((clave, info))
        
        for tipo_perf in sorted(agrupado_mes.keys()):
            st.markdown(f"#### 🔹 {tipo_perf}")
            
            rows_mes = []
            for clave, info in sorted(agrupado_mes[tipo_perf]):
                equipo = info['equipo']
                brazo = info['brazo']
                texto_equipo = f"{equipo}\n({brazo})" if brazo != "ÚNICO" else equipo
                
                row = {'Equipo': texto_equipo}
                for tipo_acero in TIPOS_ACERO:
                    dato = info.get(tipo_acero, {'consumo': 0, 'eficiencia': 0, 'objetivo': 0})
                    
                    if dato['consumo'] > 0 and dato['objetivo'] > 0:
                        row[tipo_acero] = f"{dato['consumo']:.0f} | {dato['eficiencia']:.0f}%"
                    elif dato['consumo'] > 0:
                        row[tipo_acero] = f"{dato['consumo']:.0f} | Sin objetivo"
                    else:
                        row[tipo_acero] = "Sin consumo"
                
                rows_mes.append(row)
            
            df_mes = pd.DataFrame(rows_mes)
            st.dataframe(df_mes, use_container_width=True, hide_index=True)
            st.divider()
    else:
        st.info("No hay datos de mes anterior")


def mostrar_historico_consumo():
    """Muestra histórico de consumo por equipo - Mejor presentación"""
    
    st.markdown("### 📜 Histórico de Consumo por Equipo")
    
    # ========== FILTROS ==========
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        from core.historico import obtener_equipos_por_compania
        equipos = obtener_equipos_por_compania()
        opciones_equipos = ["-- Seleccione --"] + sorted(set(e['equipo'] for e in equipos))
        equipo_seleccionado = st.selectbox(
            "Equipo",
            options=opciones_equipos,
            key="historico_equipo"
        )
    
    with col2:
        from core.database import get_db
        db = get_db()
        anos = db.execute_query("SELECT DISTINCT ano FROM movimiento_general WHERE ano IS NOT NULL ORDER BY ano DESC")
        opciones_anos = ["-- Todos --"] + [str(row[0]) for row in anos]
        ano_seleccionado = st.selectbox(
            "Año",
            options=opciones_anos,
            key="historico_ano"
        )
    
    with col3:
        if st.button("📥 Cargar", type="primary", use_container_width=True):
            st.rerun()
    
    if equipo_seleccionado == "-- Seleccione --":
        st.info("Selecciona un equipo para ver su histórico")
        return
    
    # ========== CARGAR DATOS ==========
    ano = None if ano_seleccionado == "-- Todos --" else int(ano_seleccionado)
    historico = obtener_historico_equipo(equipo_seleccionado, ano)
    
    if not historico:
        st.info(f"No hay datos históricos para el equipo {equipo_seleccionado}")
        return
    
    # ========== MOSTRAR TABLAS MEJORADAS ==========
    st.markdown(f"### 📋 Histórico - {equipo_seleccionado}")
    
    for familia, datos in sorted(historico.items()):
        if not datos:
            continue
        
        # Mostrar cada familia en su propio contenedor
        with st.container():
            st.markdown(f"#### 🔧 {familia}")
            
            df = pd.DataFrame(datos)
            
            # 🔥 Mejorar presentación
            st.dataframe(
                df,
                column_config={
                    'fecha_cambio': st.column_config.DateColumn('Fecha Cambio', width='small'),
                    'fecha_fin': st.column_config.DateColumn('Fecha Fin', width='small'),
                    'metros_perforados': st.column_config.NumberColumn('Metros Perf.', format="%.0f"),
                    'estado': st.column_config.TextColumn('Estado', width='small'),
                    'ano': st.column_config.NumberColumn('Año', width='small')
                },
                use_container_width=True,
                hide_index=True
            )
            
            # 🔥 Gráfico de metros por cambio
            if len(datos) > 1:
                fig = px.bar(
                    df,
                    x='fecha_cambio',
                    y='metros_perforados',
                    title=f'Metros Perforados por Cambio - {familia}',
                    color='estado',
                    color_discrete_map={'ABIERTO': '#ffc107', 'CERRADO': '#28a745'},
                    labels={'fecha_cambio': 'Fecha Cambio', 'metros_perforados': 'Metros'},
                    text='metros_perforados'
                )
                fig.update_layout(
                    height=250,
                    margin=dict(l=10, r=10, t=40, b=10),
                    xaxis_tickangle=-45
                )
                fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
                st.plotly_chart(fig, use_container_width=True)
            
            st.divider()