import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

import numpy as np
import logging

from utils.styles import apply_custom_styles
from utils.api_client import (
    fetch_from_api,
    load_movimientos_general,
    load_movimientos_detalles,
    load_metros_general,
    load_metros_detalles,
    load_stock_from_api
)

# ============================================
# FUNCIÓN PARA CREAR TABLAS HTML
# ============================================

def crear_tabla_html(df, titulo=None, columnas_estrechas=None):
    """Crea una tabla HTML personalizada sin scroll"""
    
    if df.empty:
        return '<p style="text-align:center; color:#6c757d; padding:20px;">ℹ️ No hay datos para mostrar</p>'
    
    columnas = df.columns.tolist()
    
    html = ""
    
    if titulo:
        html += f'<p style="font-size:14px; font-weight:600; color:#2c3e50; margin:10px 0 5px 0;">{titulo}</p>'
    
    html += '<div style="display:flex; justify-content:center; width:100%; overflow:visible;">'
    html += '<table style="border-collapse:collapse; border:2px solid #2c3e50; font-family:Segoe UI, Arial, sans-serif; font-size:12px; min-width:300px; max-width:100%; margin:0 auto;">'
    
    # Encabezados
    html += '<thead>'
    html += '<tr style="background:linear-gradient(135deg, #2c3e50 0%, #34495e 100%);">'
    for col in columnas:
        html += f'<th style="color:#ffffff; font-weight:bold; font-size:11px; text-align:center; padding:6px 10px; border:1px solid #1a252f; text-transform:uppercase; letter-spacing:0.5px; white-space:nowrap;">{col}</th>'
    html += '</tr>'
    html += '</thead>'
    
    # Cuerpo
    html += '<tbody>'
    for idx, row in df.iterrows():
        bg_color = '#f8f9fa' if idx % 2 == 1 else '#ffffff'
        html += f'<tr style="background-color:{bg_color};">'
        
        for col in columnas:
            valor = row[col]
            
            # Estilo según columna
            if col == 'Equipo_Brazo':
                estilo = 'text-align:left; font-weight:600; color:#1a5276; white-space:nowrap;'
            elif col == 'Familia':
                estilo = 'text-align:left; font-weight:600;'
            elif col == 'Fecha_Inicio' or col == 'Fecha_Fin':
                estilo = 'text-align:center;'
            elif isinstance(valor, (int, float)):
                estilo = 'text-align:right;'
            else:
                estilo = 'text-align:left;'
            
            # Formatear valores
            if isinstance(valor, (int, float)):
                if col in ['Metros', 'Rendimiento']:
                    valor_display = f'{valor:,.2f}'
                else:
                    valor_display = f'{valor:,.0f}'
            else:
                valor_display = valor
            
            html += f'<td style="padding:5px 10px; border:1px solid #bdc3c7; color:#2c3e50; font-size:12px; {estilo}">{valor_display}</td>'
        
        html += '</tr>'
    html += '</tbody>'
    
    html += '</table>'
    html += '</div>'
    
    return html

# Aplicar estilos personalizados
apply_custom_styles()
# Configurar logging para mostrar en terminal
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de página

st.title("🚜 Equipos - Rendimiento y Consumo")



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
            if 'equipo' in row and row['equipo']:
                row['equipo'] = row['equipo'].strip()
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
            if 'equipo' in row and row['equipo']:
                row['equipo'] = row['equipo'].strip()
    return data

@st.cache_data(ttl=300)
def load_metros_detalles():
    return fetch_from_api("metros-detalles")

# ============================================
# FUNCIÓN: HISTÓRICO CON EQUIPO-BRAZO
# ============================================

@st.cache_data(ttl=600)
def process_historico_brazos(equipo_seleccionado, meses_atras=12, año_filtro=None):
    """Procesa el histórico de un equipo con todos sus brazos"""
    
    familias_target = ['SHANK', 'ACOPLES', 'BARRAS']
    
    logger.info(f"🔍 HISTÓRICO - Equipo: {equipo_seleccionado}, Meses atrás: {meses_atras}, Año: {año_filtro}")
    
    # Cargar datos
    mov_detalles = load_movimientos_detalles()
    met_detalles = load_metros_detalles()
    
    # Filtrar movimientos generales (SALIDA) para el equipo específico
    df_mov_gen = pd.DataFrame(load_movimientos_general())
    
    df_mov_gen_filtrado = df_mov_gen[
        (df_mov_gen['movimiento'] == 'SALIDA') &
        (df_mov_gen['equipo'] == equipo_seleccionado)
    ]
    
    if año_filtro and año_filtro != "TODOS":
        df_mov_gen_filtrado = df_mov_gen_filtrado[df_mov_gen_filtrado['ano'] == int(año_filtro)]
    
    if meses_atras:
        fecha_corte = datetime.now() - timedelta(days=meses_atras * 30)
        df_mov_gen_filtrado = df_mov_gen_filtrado[
            pd.to_datetime(df_mov_gen_filtrado['fecha']) >= fecha_corte
        ]
    
    if df_mov_gen_filtrado.empty:
        logger.warning(f"⚠️ No hay movimientos para el equipo {equipo_seleccionado}")
        return {}
    
    logger.info(f"📊 Movimientos encontrados: {len(df_mov_gen_filtrado)}")
    
    # Obtener movimientos IDs
    mov_ids = df_mov_gen_filtrado['id'].tolist()
    
    # Obtener detalles de movimientos
    df_mov_det = pd.DataFrame(mov_detalles)
    df_mov_det_filtrado = df_mov_det[
        (df_mov_det['entrega_id'].isin(mov_ids)) &
        (df_mov_det['familia'].str.upper().isin(familias_target))
    ]
    
    if df_mov_det_filtrado.empty:
        logger.warning(f"⚠️ No hay detalles para el equipo {equipo_seleccionado}")
        return {}
    
    # UNIR con generales para obtener fecha
    df_mov_det_filtrado = df_mov_det_filtrado.merge(
        df_mov_gen_filtrado[['id', 'fecha']],
        left_on='entrega_id',
        right_on='id',
        how='left'
    )
    
    # Crear columna equipo_brazo
    df_mov_det_filtrado['equipo_brazo'] = df_mov_det_filtrado.apply(
        lambda row: f"{equipo_seleccionado}-{row['brazo']}" if pd.notna(row.get('brazo')) and row['brazo'] != '' else equipo_seleccionado,
        axis=1
    )
    
    df_mov_det_filtrado = df_mov_det_filtrado.sort_values('fecha')
    
    # Cargar metros
    df_met_gen = pd.DataFrame(load_metros_general())
    df_met_gen_filtrado = df_met_gen[df_met_gen['equipo'] == equipo_seleccionado]
    
    if df_met_gen_filtrado.empty:
        logger.warning(f"⚠️ No hay metros para el equipo {equipo_seleccionado}")
        return {}
    
    df_met_det = pd.DataFrame(met_detalles)
    met_ids = df_met_gen_filtrado['id'].tolist()
    df_met_det_filtrado = df_met_det[df_met_det['registro_id'].isin(met_ids)]
    
    # Obtener todas las combinaciones equipo_brazo
    combinaciones = df_mov_det_filtrado['equipo_brazo'].unique()
    
    resultados = {}
    
    for combinacion in combinaciones:
        df_combinacion = df_mov_det_filtrado[df_mov_det_filtrado['equipo_brazo'] == combinacion]
        
        for familia in familias_target:
            df_familia = df_combinacion[
                df_combinacion['familia'].str.upper() == familia
            ]
            
            if df_familia.empty:
                continue
            
            fechas = df_familia['fecha'].unique()
            fechas = sorted(fechas)
            
            historico = []
            
            for i, fecha_ini in enumerate(fechas):
                if i < len(fechas) - 1:
                    fecha_fin = fechas[i + 1]
                else:
                    fecha_fin = datetime.now().date()
                
                df_met_rango = df_met_gen_filtrado[
                    (pd.to_datetime(df_met_gen_filtrado['fecha']) >= pd.to_datetime(fecha_ini)) &
                    (pd.to_datetime(df_met_gen_filtrado['fecha']) < pd.to_datetime(fecha_fin))
                ]
                
                met_ids_rango = df_met_rango['id'].tolist()
                df_met_det_rango = df_met_det_filtrado[
                    df_met_det_filtrado['registro_id'].isin(met_ids_rango)
                ]
                
                metros = df_met_det_rango['total_mp'].sum()
                
                historico.append({
                    'Fecha_Inicio': fecha_ini,
                    'Fecha_Fin': fecha_fin,
                    'Metros': metros
                })
            
            if historico:
                key = f"{combinacion} - {familia}"
                resultados[key] = pd.DataFrame(historico)
    
    logger.info(f"✅ Histórico generado para {len(resultados)} combinaciones")
    
    return resultados

@st.cache_data(ttl=300)
def process_estado_actual():
    """Procesa el estado actual - Última entrega de cada equipo"""
    
    familias_target = ['SHANK', 'ACOPLES', 'BARRAS', 'RIMADORAS']
    
    logger.info("🔍 PROCESANDO ESTADO ACTUAL (SIN FILTROS)")
    
    # Cargar datos
    mov_detalles = load_movimientos_detalles()
    met_detalles = load_metros_detalles()
    
    # Filtrar movimientos generales (SOLO SALIDA)
    df_mov_gen = pd.DataFrame(load_movimientos_general())
    df_mov_gen_filtrado = df_mov_gen[df_mov_gen['movimiento'] == 'SALIDA']
    
    if df_mov_gen_filtrado.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # Obtener detalles de movimientos
    df_mov_det = pd.DataFrame(mov_detalles)
    mov_ids = df_mov_gen_filtrado['id'].tolist()
    df_mov_det_filtrado = df_mov_det[df_mov_det['entrega_id'].isin(mov_ids)]
    
    # 🔥 CORREGIDO: Renombrar tipo_perforacion del general ANTES del merge
    df_mov_gen_para_merge = df_mov_gen_filtrado[['id', 'equipo', 'fecha', 'tipo_perforacion']].copy()
    df_mov_gen_para_merge = df_mov_gen_para_merge.rename(columns={
        'tipo_perforacion': 'tipo_perf_general'  # 🔥 Renombrar para evitar conflicto
    })
    
    df_mov_det_filtrado = df_mov_det_filtrado.merge(
        df_mov_gen_para_merge,
        left_on='entrega_id',
        right_on='id',
        how='left'
    )
    
    # 🔥 Usar la columna renombrada como tipo_perforacion
    if 'tipo_perf_general' in df_mov_det_filtrado.columns:
        df_mov_det_filtrado['tipo_perforacion'] = df_mov_det_filtrado['tipo_perf_general']
    elif 'tipo_perforacion_y' in df_mov_det_filtrado.columns:
        df_mov_det_filtrado['tipo_perforacion'] = df_mov_det_filtrado['tipo_perforacion_y']
    else:
        df_mov_det_filtrado['tipo_perforacion'] = 'GENERAL'
    
    # Filtrar familias target
    df_mov_det_filtrado = df_mov_det_filtrado[
        df_mov_det_filtrado['familia'].str.upper().isin(familias_target)
    ]
    
    if df_mov_det_filtrado.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # Crear equipo_brazo
    df_mov_det_filtrado['equipo_brazo'] = df_mov_det_filtrado.apply(
        lambda row: f"{row['equipo']}-{row['brazo']}" if pd.notna(row.get('brazo')) and row['brazo'] != '' else row['equipo'],
        axis=1
    )
    
    # 🔍 DEBUG: Verificar tipos_perforacion
    print("=" * 60)
    print("🔍 DEBUG: Tipos de perforación encontrados")
    print(f"Tipos únicos: {df_mov_det_filtrado['tipo_perforacion'].unique()}")
    print("=" * 60)
    
    # Agrupar
    entregas_recientes = df_mov_det_filtrado.groupby(
        ['equipo_brazo', 'familia', 'tipo_perforacion', 'equipo']
    ).agg({
        'fecha': 'max',
        'cantidad': lambda x: x.abs().sum()
    }).reset_index()
    
    entregas_recientes = entregas_recientes.rename(columns={'fecha': 'fecha_ultima_entrega'})
    
    # Cargar metros
    df_met_gen = pd.DataFrame(load_metros_general())
    
    if df_met_gen.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # 🔥 Renombrar tipo_perforacion de metros también para evitar conflicto
    df_met_det = pd.DataFrame(met_detalles)
    met_ids = df_met_gen['id'].tolist()
    df_met_det_filtrado = df_met_det[df_met_det['registro_id'].isin(met_ids)]
    
    # 🔥 Crear diccionario de tipo_perforacion por ID de metros
    tipo_por_met_id = dict(zip(df_met_gen['id'], df_met_gen['tipo_perforacion']))
    
    # Calcular metros
    resultados = []
    
    for _, row in entregas_recientes.iterrows():
        equipo_brazo = row['equipo_brazo']
        equipo_base = row['equipo']
        familia = row['familia']
        tipo_perf = row['tipo_perforacion']
        fecha_ultima = row['fecha_ultima_entrega']
        cantidad = row['cantidad']
        
        # 🔥 Filtrar metros por equipo, tipo y fecha
        met_ids_equipo = df_met_gen[
            (df_met_gen['equipo'] == equipo_base) &
            (df_met_gen['tipo_perforacion'] == tipo_perf) &
            (pd.to_datetime(df_met_gen['fecha']) >= pd.to_datetime(fecha_ultima))
        ]['id'].tolist()
        
        print(f"🔍 {equipo_brazo} | {familia} | {tipo_perf} | Última: {fecha_ultima} | IDs: {len(met_ids_equipo)}")
        
        df_met_equipo = df_met_det_filtrado[
            df_met_det_filtrado['registro_id'].isin(met_ids_equipo)
        ]
        
        if familia.upper() == 'RIMADORAS':
            metros = df_met_equipo['mp_rimado'].sum()
        else:
            metros = df_met_equipo['total_mp'].sum()
        
        print(f"   📊 Metros: {metros:.2f}")
        
        resultados.append({
            'Equipo_Brazo': equipo_brazo,
            'Familia': familia,
            'Tipo_Perforacion': tipo_perf,
            'Cantidad': cantidad,
            'Metros': metros,
            'Rendimiento': metros / cantidad if cantidad > 0 else 0,
            'Fecha_Ultima_Entrega': fecha_ultima
        })
    
    if not resultados:
        return pd.DataFrame(), pd.DataFrame()
    
    df_resultado = pd.DataFrame(resultados)
    
    # Agrupar
    df_resultado_agrupado = df_resultado.groupby(['Equipo_Brazo', 'Familia']).agg({
        'Metros': 'sum'
    }).reset_index()
    
    tabla_pivot = df_resultado_agrupado.pivot_table(
        index='Equipo_Brazo',
        columns='Familia',
        values='Metros',
        fill_value=0
    ).reset_index()
    
    for familia in familias_target:
        if familia not in tabla_pivot.columns:
            tabla_pivot[familia] = 0
    
    columnas_orden = ['Equipo_Brazo'] + familias_target
    tabla_pivot = tabla_pivot[columnas_orden]
    
    return tabla_pivot, df_resultado

@st.cache_data(ttl=300)
def process_tabla_mes(año, mes, compania):
    """Procesa la tabla del mes con número de entregas y rendimiento"""
    
    familias_target = ['SHANK', 'ACOPLES', 'BARRAS', 'RIMADORAS']
    
    logger.info(f"🔍 TABLA DEL MES - Año: {año}, Mes: {mes}, Compañía: {compania}")
    
    # Cargar datos
    mov_detalles = load_movimientos_detalles()
    met_detalles = load_metros_detalles()
    
    # Filtrar movimientos generales (SALIDA)
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
    
    if df_mov_gen_filtrado.empty:
        logger.warning("⚠️ No hay movimientos SALIDA para los filtros")
        return pd.DataFrame(), pd.DataFrame()
    
    logger.info(f"📊 Movimientos SALIDA: {len(df_mov_gen_filtrado)}")
    
    # Obtener detalles de movimientos
    df_mov_det = pd.DataFrame(mov_detalles)
    mov_ids = df_mov_gen_filtrado['id'].tolist()
    df_mov_det_filtrado = df_mov_det[df_mov_det['entrega_id'].isin(mov_ids)]
    
    # UNIR CON GENERALES PARA OBTENER EQUIPO
    df_mov_det_filtrado = df_mov_det_filtrado.merge(
        df_mov_gen_filtrado[['id', 'equipo', 'compania']],
        left_on='entrega_id',
        right_on='id',
        how='left'
    )
    
    df_mov_det_filtrado = df_mov_det_filtrado[
        df_mov_det_filtrado['familia'].str.upper().isin(familias_target)
    ]
    
    if df_mov_det_filtrado.empty:
        logger.warning("⚠️ No hay detalles con familias target")
        return pd.DataFrame(), pd.DataFrame()
    
    # Crear equipo_brazo
    df_mov_det_filtrado['equipo_brazo'] = df_mov_det_filtrado.apply(
        lambda row: f"{row['equipo']}-{row['brazo']}" if pd.notna(row.get('brazo')) and row['brazo'] != '' else row['equipo'],
        axis=1
    )
    
    # 🔥 CORREGIDO: Usar 'entrega_id' para contar (es el ID que tenemos)
    # O crear un contador manual
    entregas_mes = df_mov_det_filtrado.groupby(['equipo_brazo', 'familia']).agg({
        'cantidad': lambda x: x.abs().sum(),
        'entrega_id': 'count'  # 🔥 Usamos 'entrega_id' en lugar de 'id'
    }).reset_index()
    
    entregas_mes = entregas_mes.rename(columns={'entrega_id': 'num_entregas'})
    
    # Calcular metros del mes
    df_met_gen = pd.DataFrame(load_metros_general())
    
    df_met_gen_filtrado = df_met_gen[
        (df_met_gen['ano'] == año_int) &
        (df_met_gen['mes'] == mes_clean)
    ]
    
    if compania != "TODAS":
        df_met_gen_filtrado = df_met_gen_filtrado[
            df_met_gen_filtrado['compania'] == compania.strip()
        ]
    
    if df_met_gen_filtrado.empty:
        logger.warning("⚠️ No hay metros para los filtros")
        return pd.DataFrame(), pd.DataFrame()
    
    df_met_det = pd.DataFrame(met_detalles)
    met_ids = df_met_gen_filtrado['id'].tolist()
    df_met_det_filtrado = df_met_det[df_met_det['registro_id'].isin(met_ids)]
    
    # Calcular metros por equipo y familia
    resultados = []
    
    for _, row in entregas_mes.iterrows():
        equipo_brazo = row['equipo_brazo']
        familia = row['familia']
        cantidad = row['cantidad']
        num_entregas = row['num_entregas']
        
        equipo_base = equipo_brazo.split('-')[0]
        
        met_ids_equipo = df_met_gen_filtrado[
            df_met_gen_filtrado['equipo'] == equipo_base
        ]['id'].tolist()
        
        df_met_equipo = df_met_det_filtrado[
            df_met_det_filtrado['registro_id'].isin(met_ids_equipo)
        ]
        
        if familia.upper() == 'RIMADORAS':
            metros = df_met_equipo['mp_rimado'].sum()
        else:
            metros = df_met_equipo['total_mp'].sum()
        
        rendimiento = metros / cantidad if cantidad > 0 else 0
        
        resultados.append({
            'Equipo_Brazo': equipo_brazo,
            'Familia': familia,
            'Num_Entregas': num_entregas,
            'Rendimiento': rendimiento
        })
    
    if not resultados:
        return pd.DataFrame(), pd.DataFrame()
    
    df_resultado = pd.DataFrame(resultados)
    
    pivot_entregas = df_resultado.pivot_table(
        index='Equipo_Brazo',
        columns='Familia',
        values='Num_Entregas',
        fill_value=0
    ).reset_index()
    
    pivot_rendimiento = df_resultado.pivot_table(
        index='Equipo_Brazo',
        columns='Familia',
        values='Rendimiento',
        fill_value=0
    ).reset_index()
    
    for familia in familias_target:
        if familia not in pivot_entregas.columns:
            pivot_entregas[familia] = 0
        if familia not in pivot_rendimiento.columns:
            pivot_rendimiento[familia] = 0
    
    columnas_orden = ['Equipo_Brazo'] + familias_target
    
    return pivot_entregas[columnas_orden], pivot_rendimiento[columnas_orden]


@st.cache_data(ttl=600)
def process_historico(equipo_seleccionado, meses_atras=12, año_filtro=None):
    """Procesa el histórico de un equipo específico"""
    
    familias_target = ['SHANK', 'ACOPLES', 'BARRAS']
    
    logger.info(f"🔍 HISTÓRICO - Equipo: {equipo_seleccionado}, Meses atrás: {meses_atras}, Año: {año_filtro}")
    
    # Cargar datos
    mov_detalles = load_movimientos_detalles()
    met_detalles = load_metros_detalles()
    
    # Filtrar movimientos generales (SALIDA) para el equipo específico
    df_mov_gen = pd.DataFrame(load_movimientos_general())
    
    df_mov_gen_filtrado = df_mov_gen[
        (df_mov_gen['movimiento'] == 'SALIDA') &
        (df_mov_gen['equipo'] == equipo_seleccionado)
    ]
    
    if año_filtro and año_filtro != "TODOS":
        df_mov_gen_filtrado = df_mov_gen_filtrado[df_mov_gen_filtrado['ano'] == int(año_filtro)]
    
    if meses_atras:
        fecha_corte = datetime.now() - timedelta(days=meses_atras * 30)
        df_mov_gen_filtrado = df_mov_gen_filtrado[
            pd.to_datetime(df_mov_gen_filtrado['fecha']) >= fecha_corte
        ]
    
    if df_mov_gen_filtrado.empty:
        logger.warning(f"⚠️ No hay movimientos para el equipo {equipo_seleccionado}")
        return {}
    
    logger.info(f"📊 Movimientos encontrados: {len(df_mov_gen_filtrado)}")
    
    # Obtener movimientos IDs
    mov_ids = df_mov_gen_filtrado['id'].tolist()
    
    # Obtener detalles de movimientos
    df_mov_det = pd.DataFrame(mov_detalles)
    df_mov_det_filtrado = df_mov_det[
        (df_mov_det['entrega_id'].isin(mov_ids)) &
        (df_mov_det['familia'].str.upper().isin(familias_target))
    ]
    
    if df_mov_det_filtrado.empty:
        logger.warning(f"⚠️ No hay detalles para el equipo {equipo_seleccionado}")
        return {}
    
    # Crear columna de fecha para ordenar
    df_mov_det_filtrado = df_mov_det_filtrado.merge(
        df_mov_gen_filtrado[['id', 'fecha']],
        left_on='entrega_id',
        right_on='id',
        how='left'
    )
    
    df_mov_det_filtrado = df_mov_det_filtrado.sort_values('fecha')
    
    # Cargar metros
    df_met_gen = pd.DataFrame(load_metros_general())
    df_met_gen_filtrado = df_met_gen[df_met_gen['equipo'] == equipo_seleccionado]
    
    if df_met_gen_filtrado.empty:
        logger.warning(f"⚠️ No hay metros para el equipo {equipo_seleccionado}")
        return {}
    
    df_met_det = pd.DataFrame(met_detalles)
    met_ids = df_met_gen_filtrado['id'].tolist()
    df_met_det_filtrado = df_met_det[df_met_det['registro_id'].isin(met_ids)]
    
    # Procesar por cada familia
    resultados = {}
    
    for familia in familias_target:
        df_familia = df_mov_det_filtrado[
            df_mov_det_filtrado['familia'].str.upper() == familia
        ]
        
        if df_familia.empty:
            continue
        
        fechas = df_familia['fecha'].unique()
        fechas = sorted(fechas)
        
        historico = []
        
        for i, fecha_ini in enumerate(fechas):
            if i < len(fechas) - 1:
                fecha_fin = fechas[i + 1]
            else:
                fecha_fin = datetime.now().date()
            
            df_met_rango = df_met_gen_filtrado[
                (pd.to_datetime(df_met_gen_filtrado['fecha']) >= pd.to_datetime(fecha_ini)) &
                (pd.to_datetime(df_met_gen_filtrado['fecha']) < pd.to_datetime(fecha_fin))
            ]
            
            met_ids_rango = df_met_rango['id'].tolist()
            df_met_det_rango = df_met_det_filtrado[
                df_met_det_filtrado['registro_id'].isin(met_ids_rango)
            ]
            
            metros = df_met_det_rango['total_mp'].sum()
            
            historico.append({
                'Fecha_Inicio': fecha_ini,
                'Fecha_Fin': fecha_fin,
                'Metros': metros
            })
        
        if historico:
            resultados[familia] = pd.DataFrame(historico)
    
    logger.info(f"✅ Histórico generado para {len(resultados)} familias")
    
    return resultados


with st.spinner("Cargando datos..."):
    movimientos_data = load_movimientos_general()
    df_mov = pd.DataFrame(movimientos_data)

# Obtener valores disponibles
if not df_mov.empty:
    años_disponibles = sorted(df_mov['ano'].unique())
    meses_disponibles = sorted(df_mov['mes'].unique())
    companias_disponibles = sorted(df_mov['compania'].dropna().unique())
    equipos_disponibles = sorted(df_mov['equipo'].dropna().unique())
    
    # Último mes con datos de SALIDA
    df_mov_salida = df_mov[df_mov['movimiento'] == 'SALIDA']
    if not df_mov_salida.empty:
        df_mov_salida['fecha_dt'] = pd.to_datetime(df_mov_salida['fecha'])
        ultima_fecha = df_mov_salida['fecha_dt'].max()
        ultimo_mes = ultima_fecha.strftime('%B').upper()
        ultimo_ano = ultima_fecha.year
    else:
        ultimo_mes = None
        ultimo_ano = None
else:
    años_disponibles = [2024, 2025, 2026]
    meses_disponibles = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
                         'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    companias_disponibles = []
    equipos_disponibles = []
    ultimo_mes = None
    ultimo_ano = None


st.title("🚜 Equipos - Rendimiento y Consumo")

tab1, tab2, tab3 = st.tabs(["📊 Estado Actual", "📋 Tabla del Mes", "📈 Histórico"])


with tab1:
    st.subheader("📊 Estado Actual - Metros por Equipo y Familia")
    st.caption("📌 Muestra los metros perforados desde la última entrega hasta hoy")
    
    with st.spinner("Procesando datos..."):
        df_estado, df_detalle = process_estado_actual()

        
        if not df_detalle.empty:
            st.write("### 📋 Detalle completo (df_detalle)")
            st.dataframe(df_detalle, use_container_width=True)
            
            st.write("### 📅 Fechas de última entrega por equipo")
            for equipo in df_detalle['Equipo_Brazo'].unique()[:10]:  # Primeros 10
                df_eq = df_detalle[df_detalle['Equipo_Brazo'] == equipo]
                st.write(f"**{equipo}:**")
                st.dataframe(df_eq[['Familia', 'Cantidad', 'Metros', 'Fecha_Ultima_Entrega']], hide_index=True)
        
        if not df_estado.empty:
            st.write("### 📊 Tabla pivoteada (df_estado)")
            st.dataframe(df_estado, use_container_width=True)


    
    
    if not df_estado.empty:
        # 🔥 TABLA HTML SIN SCROLL
        html_tabla = crear_tabla_html(df_estado, titulo="")
        st.markdown(html_tabla, unsafe_allow_html=True)
        
        # Resumen por familia
        st.subheader("📊 Resumen por Familia")
        col1, col2, col3, col4 = st.columns(4)
        
        for idx, familia in enumerate(['SHANK', 'ACOPLES', 'BARRAS', 'RIMADORAS']):
            total = df_estado[familia].sum() if familia in df_estado.columns else 0
            with [col1, col2, col3, col4][idx]:
                st.metric(f"Total {familia}", f"{total:,.2f} m")
        
        # Mostrar fecha de última actualización
        if not df_detalle.empty:
            ultima_fecha = df_detalle['Fecha_Ultima_Entrega'].max()
            st.caption(f"🕐 Última actualización basada en entregas hasta: {ultima_fecha}")
    else:
        st.warning("No hay datos disponibles")

with tab2:
    st.subheader("📋 Tabla del Mes - Entregas y Rendimiento")
    
    # Filtros para la tabla del mes
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Usar último mes como default si existe
        if ultimo_ano and ultimo_ano in años_disponibles:
            idx_ano = años_disponibles.index(ultimo_ano)
        else:
            idx_ano = len(años_disponibles) - 1 if años_disponibles else 0
        
        año_tabla = st.selectbox(
            "📅 Año",
            años_disponibles,
            index=idx_ano,
            key="año_tabla_mes"
        )
    
    with col2:
        if ultimo_mes and ultimo_mes in meses_disponibles:
            idx_mes = meses_disponibles.index(ultimo_mes)
        else:
            idx_mes = len(meses_disponibles) - 1 if meses_disponibles else 0
        
        mes_tabla = st.selectbox(
            "📆 Mes",
            meses_disponibles,
            index=idx_mes,
            key="mes_tabla_mes"
        )
    
    with col3:
        compania_tabla = st.selectbox(
            "🏢 Compañía",
            ["TODAS"] + list(companias_disponibles),
            key="compania_tabla_mes"
        )
    
    if st.button("🔍 Generar Tabla del Mes", key="btn_tabla_mes"):
        with st.spinner("Procesando datos..."):
            df_entregas, df_rendimiento = process_tabla_mes(
                año_tabla,
                mes_tabla,
                compania_tabla
            )
        
        if not df_entregas.empty:
            st.markdown("### 📦 Número de Entregas")
            html_entregas = crear_tabla_html(df_entregas, titulo="")
            st.markdown(html_entregas, unsafe_allow_html=True)
            
            st.markdown("### 📊 Rendimiento (m/unidad)")
            st.dataframe(
                df_rendimiento,
                column_config={
                    "Equipo_Brazo": st.column_config.TextColumn("Equipo/Brazo"),
                    "SHANK": st.column_config.NumberColumn("SHANK", format="%.2f"),
                    "ACOPLES": st.column_config.NumberColumn("ACOPLES", format="%.2f"),
                    "BARRAS": st.column_config.NumberColumn("BARRAS", format="%.2f"),
                    "RIMADORAS": st.column_config.NumberColumn("RIMADORAS", format="%.2f")
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Gráfico
            df_rendimiento_melt = df_rendimiento.melt(
                id_vars=['Equipo_Brazo'],
                var_name='Familia',
                value_name='Rendimiento'
            )
            
            if not df_rendimiento_melt.empty and df_rendimiento_melt['Rendimiento'].sum() > 0:
                fig = px.bar(
                    df_rendimiento_melt,
                    x='Equipo_Brazo',
                    y='Rendimiento',
                    color='Familia',
                    barmode='group',
                    title="Rendimiento por Equipo y Familia",
                    labels={'Rendimiento': 'Rendimiento (m/unidad)', 'Equipo_Brazo': 'Equipo/Brazo'}
                )
                fig.update_layout(
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No hay datos para los filtros seleccionados")


with tab3:
    st.subheader("📈 Histórico de Equipos por Familia y Brazo")
    st.caption("📌 Muestra el histórico de metros perforados entre entregas para cada combinación Equipo-Brazo")
    
    # Filtros específicos para histórico
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if equipos_disponibles:
            equipo_historico = st.selectbox(
                "🚜 Seleccionar Equipo",
                equipos_disponibles,
                key="equipo_historico_tab3"
            )
        else:
            st.warning("No hay equipos disponibles")
            equipo_historico = None
    
    with col2:
        meses_opciones = {
            "Últimos 3 meses": 3,
            "Últimos 6 meses": 6,
            "Último año": 12,
            "Últimos 2 años": 24,
            "Todo": None
        }
        rango_seleccionado = st.selectbox(
            "📅 Rango de tiempo",
            list(meses_opciones.keys()),
            index=2,
            key="rango_historico_tab3"
        )
        meses_atras = meses_opciones[rango_seleccionado]
    
    with col3:
        años_historico = ["TODOS"] + [str(a) for a in años_disponibles]
        año_historico = st.selectbox(
            "📅 Año específico",
            años_historico,
            index=0,
            key="año_historico_tab3"
        )
    
    # Botón para generar histórico
    if equipo_historico is not None:
        if st.button("🔍 Generar Histórico", key="btn_historico_tab3"):
            with st.spinner("Generando histórico..."):
                historico_data = process_historico_brazos(
                    equipo_historico,
                    meses_atras,
                    año_historico if año_historico != "TODOS" else None
                )
            
            if historico_data:
                claves_ordenadas = sorted(historico_data.keys())
                
                for clave in claves_ordenadas:
                    df_hist = historico_data[clave]
                    
                    if not df_hist.empty:
                        partes = clave.split(" - ")
                        combinacion = partes[0]
                        familia = partes[1] if len(partes) > 1 else "General"

                                            # 🔥 TÍTULO CON FAMILIA BIEN VISIBLE
                        with st.expander(f"📌 {combinacion} — 🔧 Familia: {familia}", expanded=False):
                            # Formatear fechas
                            df_hist['Fecha_Inicio'] = pd.to_datetime(df_hist['Fecha_Inicio']).dt.date
                            df_hist['Fecha_Fin'] = pd.to_datetime(df_hist['Fecha_Fin']).dt.date
                            
                            # 🔥 Mostrar título de la familia dentro
                            st.markdown(f"### 🔧 Familia: **{familia}**")
                            st.caption(f"🚜 Equipo/Brazo: {combinacion}")
                            
                            # 🔥 TABLA HTML
                            html_hist = crear_tabla_html(df_hist, titulo="")
                            st.markdown(html_hist, unsafe_allow_html=True)

                            
                            if len(df_hist) > 1:
                                fig = px.line(
                                    df_hist,
                                    x='Fecha_Inicio',
                                    y='Metros',
                                    title=f"Evolución de Metros - {combinacion} - {familia}",
                                    markers=True,
                                    labels={'Metros': 'Metros', 'Fecha_Inicio': 'Fecha'}
                                )
                                fig.update_layout(
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    height=300
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                st.info("ℹ️ Solo hay un registro, no se puede generar gráfico de evolución")
            else:
                st.warning(f"No hay datos históricos para el equipo {equipo_historico}")
    else:
        st.info("ℹ️ No hay equipos disponibles para mostrar el histórico")