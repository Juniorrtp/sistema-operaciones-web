import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import requests
import numpy as np
from utils.styles import apply_custom_styles

# ✅ Importar cliente de API
from utils.api_client import (
    fetch_from_api,
    load_movimientos_general,
    load_movimientos_detalles,
    load_metros_general,
    load_metros_detalles,
    load_objetivos
)
apply_custom_styles()
# Ocultar elementos de Streamlit



# ============================================
# CARGA DE DATOS CON CACHÉ Y LIMPIEZA
# ============================================

@st.cache_data(ttl=300)
def load_movimientos_general(fecha_desde=None, fecha_hasta=None):
    params = {"limit": 5000}
    if fecha_desde:
        params["fecha_desde"] = fecha_desde
    if fecha_hasta:
        params["fecha_hasta"] = fecha_hasta
    
    data = fetch_from_api("movimientos", params)
    
    if data:
        for row in data:
            if 'compania' in row and row['compania']:
                row['compania'] = row['compania'].strip()
            if 'tipo_perforacion' in row and row['tipo_perforacion']:
                row['tipo_perforacion'] = row['tipo_perforacion'].strip()
            if 'mes' in row and row['mes']:
                row['mes'] = row['mes'].strip().upper()
            if 'movimiento' in row and row['movimiento']:
                row['movimiento'] = row['movimiento'].strip().upper()
    return data

@st.cache_data(ttl=300)
def load_movimientos_detalles():
    return fetch_from_api("detalles-movimientos")

@st.cache_data(ttl=300)
def load_metros_general(fecha_desde=None, fecha_hasta=None):
    params = {"limit": 5000}
    if fecha_desde:
        params["fecha_desde"] = fecha_desde
    if fecha_hasta:
        params["fecha_hasta"] = fecha_hasta
    
    data = fetch_from_api("metros", params)
    
    if data:
        for row in data:
            if 'compania' in row and row['compania']:
                row['compania'] = row['compania'].strip()
            if 'tipo_perforacion' in row and row['tipo_perforacion']:
                row['tipo_perforacion'] = row['tipo_perforacion'].strip()
            if 'mes' in row and row['mes']:
                row['mes'] = row['mes'].strip().upper()
    return data

@st.cache_data(ttl=300)
def load_metros_detalles():
    return fetch_from_api("metros-detalles")

@st.cache_data(ttl=3600)
def load_objetivos():
    return fetch_from_api("objetivos")

# ============================================
# FUNCIÓN PRINCIPAL - RENDIMIENTO ACEROS
# ============================================

@st.cache_data(ttl=300)
def process_rendimiento_aceros(año, mes, compania, tipos_perf):
    """Procesa datos de rendimiento de aceros"""
    
    # Cargar datos
    mov_detalles = load_movimientos_detalles()
    met_detalles = load_metros_detalles()
    objetivos = load_objetivos()
    
    # Filtrar movimientos generales
    df_mov_gen = pd.DataFrame(load_movimientos_general())
    
    año_int = int(año)
    mes_clean = mes.strip().upper()
    
    df_mov_gen_filtrado = df_mov_gen[
        (df_mov_gen['ano'] == año_int) &
        (df_mov_gen['mes'] == mes_clean) &
        (df_mov_gen['movimiento'] == 'SALIDA')
    ]
    
    if compania != "TODAS":
        df_mov_gen_filtrado = df_mov_gen_filtrado[
            df_mov_gen_filtrado['compania'] == compania.strip()
        ]
    
    # Filtrar metros generales
    df_met_gen = pd.DataFrame(load_metros_general())
    
    df_met_gen_filtrado = df_met_gen[
        (df_met_gen['ano'] == año_int) &
        (df_met_gen['mes'] == mes_clean)
    ]
    
    if compania != "TODAS":
        df_met_gen_filtrado = df_met_gen_filtrado[
            df_met_gen_filtrado['compania'] == compania.strip()
        ]
    
    # Obtener tipos comunes
    tipos_mov = set(df_mov_gen_filtrado['tipo_perforacion'].dropna().unique())
    tipos_met = set(df_met_gen_filtrado['tipo_perforacion'].dropna().unique())
    tipos_comunes = list(tipos_mov.intersection(tipos_met))
    
    if not tipos_perf or (isinstance(tipos_perf, list) and len(tipos_perf) == 0):
        tipos_a_usar = tipos_comunes
    else:
        if isinstance(tipos_perf, str):
            tipos_perf = [tipos_perf]
        tipos_a_usar = [t for t in tipos_perf if t in tipos_comunes]
        
        if not tipos_a_usar:
            return pd.DataFrame()
    
    if not tipos_a_usar:
        return pd.DataFrame()
    
    # Aplicar filtro de tipos
    df_mov_gen_filtrado = df_mov_gen_filtrado[df_mov_gen_filtrado['tipo_perforacion'].isin(tipos_a_usar)]
    df_met_gen_filtrado = df_met_gen_filtrado[df_met_gen_filtrado['tipo_perforacion'].isin(tipos_a_usar)]
    
    if df_mov_gen_filtrado.empty or df_met_gen_filtrado.empty:
        return pd.DataFrame()
    
    # Procesar movimientos detalles
    df_mov_det = pd.DataFrame(mov_detalles)
    mov_ids = df_mov_gen_filtrado['id'].tolist()
    df_mov_det_filtrado = df_mov_det[df_mov_det['entrega_id'].isin(mov_ids)]
    df_mov_det_filtrado['cantidad'] = df_mov_det_filtrado['cantidad'].abs()
    
    # Procesar metros detalles
    df_met_det = pd.DataFrame(met_detalles)
    met_ids = df_met_gen_filtrado['id'].tolist()
    df_met_det_filtrado = df_met_det[df_met_det['registro_id'].isin(met_ids)]
    
    if df_mov_det_filtrado.empty or df_met_det_filtrado.empty:
        return pd.DataFrame()
    
    # Crear diccionario de objetivos
    obj_dict = {}
    for obj in objetivos:
        tipo = obj.get('Tipo Perforacion', '')
        familia = obj.get('Acero', '')
        objetivo_val = obj.get('Objetivo', 0)
        obj_dict[(tipo, familia)] = objetivo_val
    
    # Obtener familias únicas
    familias = df_mov_det_filtrado['familia'].dropna().unique()
    
    if len(familias) == 0:
        return pd.DataFrame()
    
    # Preparar resultados
    resultados = []
    
    for tipo in tipos_a_usar:
        met_tipo = df_met_gen_filtrado[df_met_gen_filtrado['tipo_perforacion'] == tipo]
        met_ids_tipo = met_tipo['id'].tolist()
        df_met_tipo = df_met_det_filtrado[df_met_det_filtrado['registro_id'].isin(met_ids_tipo)]
        
        df_mov_tipo = df_mov_gen_filtrado[df_mov_gen_filtrado['tipo_perforacion'] == tipo]
        mov_ids_tipo = df_mov_tipo['id'].tolist()
        df_mov_tipo_det = df_mov_det_filtrado[df_mov_det_filtrado['entrega_id'].isin(mov_ids_tipo)]
        
        for familia in familias:
            cantidad = df_mov_tipo_det[df_mov_tipo_det['familia'] == familia]['cantidad'].sum()
            
            if familia.upper() == 'RIMADORAS':
                metros = df_met_tipo['mp_rimado'].sum()
            else:
                metros = df_met_tipo['total_mp'].sum()
            
            rendimiento = metros / cantidad if cantidad > 0 else 0
            objetivo = obj_dict.get((tipo, familia), 0)
            eficiencia = (rendimiento / objetivo * 100) if objetivo > 0 else 0
            
            resultados.append({
                'Tipo_Perforacion': tipo,
                'Familia': familia,
                'Cantidad': cantidad,
                'Metros': metros,
                'Rendimiento': rendimiento,
                'Objetivo': objetivo,
                'Eficiencia': eficiencia
            })
    
    if not resultados:
        return pd.DataFrame()
    
    return pd.DataFrame(resultados)

# ============================================
# FUNCIÓN PRINCIPAL - RENDIMIENTO OPERADORES
# ============================================



@st.cache_data(ttl=300)
def process_rendimiento_operadores(año, mes, compania, tipos_perf):
    """Procesa datos de rendimiento de operadores"""
    
    # Cargar datos
    mov_detalles = load_movimientos_detalles()
    met_detalles = load_metros_detalles()
    objetivos = load_objetivos()
    
    # Filtrar movimientos generales
    df_mov_gen = pd.DataFrame(load_movimientos_general())
    
    año_int = int(año)
    mes_clean = mes.strip().upper()
    
    df_mov_gen_filtrado = df_mov_gen[
        (df_mov_gen['ano'] == año_int) &
        (df_mov_gen['mes'] == mes_clean) &
        (df_mov_gen['movimiento'] == 'SALIDA')
    ]
    
    if compania != "TODAS":
        df_mov_gen_filtrado = df_mov_gen_filtrado[
            df_mov_gen_filtrado['compania'] == compania.strip()
        ]
    
    # Filtrar metros generales
    df_met_gen = pd.DataFrame(load_metros_general())
    
    df_met_gen_filtrado = df_met_gen[
        (df_met_gen['ano'] == año_int) &
        (df_met_gen['mes'] == mes_clean)
    ]
    
    if compania != "TODAS":
        df_met_gen_filtrado = df_met_gen_filtrado[
            df_met_gen_filtrado['compania'] == compania.strip()
        ]
    
    # Obtener tipos comunes
    tipos_mov = set(df_mov_gen_filtrado['tipo_perforacion'].dropna().unique())
    tipos_met = set(df_met_gen_filtrado['tipo_perforacion'].dropna().unique())
    tipos_comunes = list(tipos_mov.intersection(tipos_met))
    
    if not tipos_perf or (isinstance(tipos_perf, list) and len(tipos_perf) == 0):
        tipos_a_usar = tipos_comunes
    else:
        if isinstance(tipos_perf, str):
            tipos_perf = [tipos_perf]
        tipos_a_usar = [t for t in tipos_perf if t in tipos_comunes]
        
        if not tipos_a_usar:
            return pd.DataFrame()
    
    if not tipos_a_usar:
        return pd.DataFrame()
    
    # Aplicar filtro de tipos
    df_mov_gen_filtrado = df_mov_gen_filtrado[df_mov_gen_filtrado['tipo_perforacion'].isin(tipos_a_usar)]
    df_met_gen_filtrado = df_met_gen_filtrado[df_met_gen_filtrado['tipo_perforacion'].isin(tipos_a_usar)]
    
    if df_mov_gen_filtrado.empty or df_met_gen_filtrado.empty:
        return pd.DataFrame()
    
    # Procesar movimientos detalles (SOLO BROCAS)
    df_mov_det = pd.DataFrame(mov_detalles)
    
    # 🔥 CREAR UN DICCIONARIO PARA RELACIONAR entrega_id CON operador
    # Primero, crear un diccionario de operadores por ID de movimiento
    operador_por_id = dict(zip(df_mov_gen_filtrado['id'], df_mov_gen_filtrado['operador']))
    guardia_por_id = dict(zip(df_mov_gen_filtrado['id'], df_mov_gen_filtrado['guardia']))
    
    # Filtrar detalles SOLO BROCAS
    mov_ids = df_mov_gen_filtrado['id'].tolist()
    df_mov_det_filtrado = df_mov_det[
        (df_mov_det['entrega_id'].isin(mov_ids)) &
        (df_mov_det['familia'].str.upper() == 'BROCAS')
    ].copy()
    
    # Asignar operador y guardia a cada detalle
    df_mov_det_filtrado['operador'] = df_mov_det_filtrado['entrega_id'].map(operador_por_id)
    df_mov_det_filtrado['guardia'] = df_mov_det_filtrado['entrega_id'].map(guardia_por_id)
    df_mov_det_filtrado['cantidad'] = df_mov_det_filtrado['cantidad'].abs()
    
    # Procesar metros detalles
    df_met_det = pd.DataFrame(met_detalles)
    met_ids = df_met_gen_filtrado['id'].tolist()
    df_met_det_filtrado = df_met_det[df_met_det['registro_id'].isin(met_ids)]
    
    # Asignar operador a metros detalles (usando metros_general)
    operador_met_por_id = dict(zip(df_met_gen_filtrado['id'], df_met_gen_filtrado['operador']))
    df_met_det_filtrado['operador'] = df_met_det_filtrado['registro_id'].map(operador_met_por_id)
    
    if df_mov_det_filtrado.empty or df_met_det_filtrado.empty:
        return pd.DataFrame()
    
    # Crear diccionario de objetivos
    obj_dict = {}
    for obj in objetivos:
        tipo = obj.get('Tipo Perforacion', '')
        familia = obj.get('Acero', '')
        objetivo_val = obj.get('Objetivo', 0)
        obj_dict[(tipo, familia)] = objetivo_val
    
    # Agrupar por tipo_perforacion, guardia, operador
    resultados = []
    
    for tipo in tipos_a_usar:
        # Filtrar metros por tipo y operador
        df_met_tipo = df_met_gen_filtrado[df_met_gen_filtrado['tipo_perforacion'] == tipo]
        met_ids_tipo = df_met_tipo['id'].tolist()
        df_met_tipo_det = df_met_det_filtrado[df_met_det_filtrado['registro_id'].isin(met_ids_tipo)]
        
        # Filtrar movimientos por tipo
        df_mov_tipo = df_mov_gen_filtrado[df_mov_gen_filtrado['tipo_perforacion'] == tipo]
        mov_ids_tipo = df_mov_tipo['id'].tolist()
        df_mov_tipo_det = df_mov_det_filtrado[df_mov_det_filtrado['entrega_id'].isin(mov_ids_tipo)]
        
        # Obtener operadores únicos de este tipo
        operadores_tipo = df_mov_tipo_det['operador'].dropna().unique()
        
        for operador in operadores_tipo:
            # 🔥 CANTIDAD: Filtrar por operador específico
            cantidad = df_mov_tipo_det[df_mov_tipo_det['operador'] == operador]['cantidad'].sum()
            
            # 🔥 METROS: Filtrar por operador específico
            metros = df_met_tipo_det[df_met_tipo_det['operador'] == operador]['total_mp'].sum()
            
            # Obtener guardia de este operador (tomar la primera que aparezca)
            guardia = df_mov_tipo_det[df_mov_tipo_det['operador'] == operador]['guardia'].iloc[0] if not df_mov_tipo_det[df_mov_tipo_det['operador'] == operador].empty else 'SIN GUARDIA'
            
            rendimiento = metros / cantidad if cantidad > 0 else 0
            objetivo = obj_dict.get((tipo, 'BROCAS'), 0)
            eficiencia = (rendimiento / objetivo * 100) if objetivo > 0 else 0
            
            resultados.append({
                'Tipo_Perforacion': tipo,
                'Guardia': guardia,
                'Operador': operador,
                'Cantidad': cantidad,
                'Metros': metros,
                'Rendimiento': rendimiento,
                'Objetivo': objetivo,
                'Eficiencia': eficiencia
            })
    
    if not resultados:
        return pd.DataFrame()
    
    return pd.DataFrame(resultados)

# ============================================
# FILTROS EN LA PARTE SUPERIOR
# ============================================

st.title("🏆 Rendimiento - Aceros y Operadores")

# Cargar datos para filtros
with st.spinner("Cargando datos..."):
    movimientos_data = load_movimientos_general()
    metros_data = load_metros_general()
    
    df_mov = pd.DataFrame(movimientos_data)
    df_met = pd.DataFrame(metros_data)

# Obtener años disponibles
if not df_mov.empty:
    años_disponibles = sorted(df_mov['ano'].unique())
    meses_disponibles = sorted(df_mov['mes'].unique())
    companias_disponibles = sorted(df_mov['compania'].dropna().unique())
else:
    años_disponibles = [2024, 2025, 2026]
    meses_disponibles = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
                         'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    companias_disponibles = []

# ============================================
# FILTROS SUPERIORES (4 columnas)
# ============================================

st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    año_seleccionado = st.selectbox(
        "📅 Año",
        años_disponibles,
        index=len(años_disponibles)-1 if años_disponibles else 0,
        key="año_filtro"
    )

with col2:
    mes_seleccionado = st.selectbox(
        "📆 Mes",
        meses_disponibles,
        index=len(meses_disponibles)-1 if meses_disponibles else 0,
        key="mes_filtro"
    )

with col3:
    compania_seleccionada = st.selectbox(
        "🏢 Compañía",
        ["TODAS"] + list(companias_disponibles),
        key="compania_filtro"
    )

with col4:
    tipos_perf_disponibles = sorted(df_met['tipo_perforacion'].dropna().unique()) if not df_met.empty else []
    tipos_seleccionados = st.multiselect(
        "🔧 Tipo Perforación",
        options=tipos_perf_disponibles,
        default=tipos_perf_disponibles[:3] if len(tipos_perf_disponibles) > 3 else tipos_perf_disponibles,
        key="tipos_filtro"
    )

st.markdown("---")

# Botón actualizar al final de los filtros
col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
with col_btn2:
    if st.button("🔄 Actualizar Datos", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# ============================================
# MOSTRAR RESULTADOS
# ============================================

if tipos_seleccionados:
    
    tab1, tab2 = st.tabs(["🔩 Rendimiento de Aceros", "👷 Rendimiento de Operadores"])
    
    with tab1:
        st.subheader("📊 Rendimiento de Aceros por Familia")
        
        with st.spinner("Procesando datos de aceros..."):
            df_aceros = process_rendimiento_aceros(
                año_seleccionado,
                mes_seleccionado,
                compania_seleccionada,
                tipos_seleccionados
            )
        
        if not df_aceros.empty:
            # 🔥 TABLAS SEPARADAS POR TIPO DE PERFORACIÓN
            tipos_unicos = sorted(df_aceros['Tipo_Perforacion'].unique())
            
            for tipo in tipos_unicos:
                df_tipo = df_aceros[df_aceros['Tipo_Perforacion'] == tipo].copy()
                df_tipo = df_tipo.drop('Tipo_Perforacion', axis=1)
                
                st.markdown(f"### 📌 {tipo}")
                
                # Mostrar tabla
                st.dataframe(
                    df_tipo,
                    column_config={
                        "Familia": st.column_config.TextColumn("Familia"),
                        "Cantidad": st.column_config.NumberColumn("Cantidad (SALIDAS)", format="%.0f"),
                        "Metros": st.column_config.NumberColumn("Metros", format="%.2f"),
                        "Rendimiento": st.column_config.NumberColumn("Rendimiento (m/unidad)", format="%.2f"),
                        "Objetivo": st.column_config.NumberColumn("Objetivo", format="%.2f"),
                        "Eficiencia": st.column_config.NumberColumn("Eficiencia (%)", format="%.1f%%")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Gráfico de eficiencia para este tipo
                fig = px.bar(
                    df_tipo,
                    x='Familia',
                    y='Eficiencia',
                    color='Eficiencia',
                    color_continuous_scale='RdYlGn',
                    title=f"Eficiencia por Familia - {tipo}",
                    text=df_tipo['Eficiencia'].apply(lambda x: f"{x:.1f}%")
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=350,
                    margin=dict(l=0, r=0, t=40, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("---")
            
            # Resumen general
            st.subheader("📊 Resumen General por Tipo de Perforación")
            resumen_tipo = df_aceros.groupby('Tipo_Perforacion').agg({
                'Eficiencia': 'mean',
                'Rendimiento': 'mean',
                'Metros': 'sum'
            }).reset_index()
            
            cols = st.columns(min(len(resumen_tipo), 4))
            for idx, row in resumen_tipo.iterrows():
                with cols[idx % 4]:
                    st.metric(
                        label=f"📌 {row['Tipo_Perforacion']}",
                        value=f"{row['Eficiencia']:.1f}%",
                        delta=f"{row['Metros']:.0f} m"
                    )
            
        else:
            st.warning("No hay datos para los filtros seleccionados")
    
    with tab2:
        st.subheader("👷 Rendimiento de Operadores (BROCAS)")
        
        with st.spinner("Procesando datos de operadores..."):
            df_operadores = process_rendimiento_operadores(
                año_seleccionado,
                mes_seleccionado,
                compania_seleccionada,
                tipos_seleccionados
            )
        
        if not df_operadores.empty:
            # 🔥 TABLAS SEPARADAS POR TIPO DE PERFORACIÓN
            tipos_unicos = sorted(df_operadores['Tipo_Perforacion'].unique())
            
            for tipo in tipos_unicos:
                df_tipo = df_operadores[df_operadores['Tipo_Perforacion'] == tipo].copy()
                df_tipo = df_tipo.drop('Tipo_Perforacion', axis=1)
                df_tipo = df_tipo.sort_values(['Guardia', 'Eficiencia'], ascending=[True, False])
                
                st.markdown(f"### 📌 {tipo}")
                
                # Mostrar tabla
                st.dataframe(
                    df_tipo,
                    column_config={
                        "Guardia": st.column_config.TextColumn("Guardia"),
                        "Operador": st.column_config.TextColumn("Operador"),
                        "Cantidad": st.column_config.NumberColumn("Cantidad (BROCAS)", format="%.0f"),
                        "Metros": st.column_config.NumberColumn("Metros", format="%.2f"),
                        "Rendimiento": st.column_config.NumberColumn("Rendimiento (m/unidad)", format="%.2f"),
                        "Objetivo": st.column_config.NumberColumn("Objetivo", format="%.2f"),
                        "Eficiencia": st.column_config.NumberColumn("Eficiencia (%)", format="%.1f%%")
                    },
                    hide_index=True,
                    use_container_width=True
                )
                
                # Gráfico de ranking para este tipo
                fig = px.bar(
                    df_tipo,
                    x='Eficiencia',
                    y='Operador',
                    color='Guardia',
                    orientation='h',
                    title=f"Ranking de Operadores - {tipo}",
                    text=df_tipo['Eficiencia'].apply(lambda x: f"{x:.1f}%")
                )
                fig.update_traces(textposition='outside')
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=350,
                    margin=dict(l=0, r=0, t=40, b=0)
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("---")
            
            # Estadísticas generales
            st.subheader("📊 Estadísticas Generales")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Operadores", len(df_operadores['Operador'].unique()))
            with col2:
                st.metric("Eficiencia Promedio", f"{df_operadores['Eficiencia'].mean():.1f}%")
            with col3:
                st.metric("Total BROCAS", f"{df_operadores['Cantidad'].sum():.0f}")
            with col4:
                st.metric("Total Metros", f"{df_operadores['Metros'].sum():.2f}")
            
        else:
            st.warning("No hay datos de operadores para los filtros seleccionados")

else:
    st.info("👈 Selecciona al menos un Tipo de Perforación en los filtros para comenzar")