import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
import io

from utils.styles import apply_custom_styles
from utils.api_client import (
    fetch_from_api,
    load_movimientos_general,
    load_movimientos_detalles,
    load_metros_general,
    load_metros_detalles,
    load_stock_from_api,
    load_objetivos,
    load_aceros
)

# Aplicar estilos personalizados
apply_custom_styles()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        if columnas_estrechas and col in columnas_estrechas:
            html += f'<th style="color:#ffffff; font-weight:bold; font-size:11px; text-align:center; padding:5px 8px; border:1px solid #1a252f; text-transform:uppercase; letter-spacing:0.5px; white-space:nowrap; min-width:60px;">{col}</th>'
        else:
            html += f'<th style="color:#ffffff; font-weight:bold; font-size:11px; text-align:center; padding:5px 10px; border:1px solid #1a252f; text-transform:uppercase; letter-spacing:0.5px; white-space:nowrap;">{col}</th>'
    html += '</tr>'
    html += '</thead>'
    
    # Cuerpo
    html += '<tbody>'
    for idx, row in df.iterrows():
        bg_color = '#f8f9fa' if idx % 2 == 1 else '#ffffff'
        html += f'<tr style="background-color:{bg_color};">'
        
        for col in columnas:
            valor = row[col]
            
            if col == 'Guardia':
                estilo = 'text-align:center; font-weight:600;'
            elif col == 'Familia':
                estilo = 'text-align:left; font-weight:500;'
            elif isinstance(valor, (int, float)):
                estilo = 'text-align:right;'
            else:
                estilo = 'text-align:left;'
            
            if isinstance(valor, (int, float)):
                if col in ['Metros', 'Rendimiento', 'Objetivo']:
                    valor_display = f'{valor:,.2f}'
                else:
                    valor_display = f'{valor:,.0f}'
            else:
                valor_display = valor
            
            if columnas_estrechas and col in columnas_estrechas:
                html += f'<td style="padding:4px 6px; border:1px solid #bdc3c7; color:#2c3e50; font-size:12px; text-align:center; {estilo}">{valor_display}</td>'
            else:
                html += f'<td style="padding:5px 10px; border:1px solid #bdc3c7; color:#2c3e50; font-size:12px; {estilo}">{valor_display}</td>'
        
        html += '</tr>'
    html += '</tbody>'
    
    html += '</table>'
    html += '</div>'
    
    return html

# ============================================
# FUNCIONES DE PROCESAMIENTO
# ============================================

def get_kpis_reporte(fecha_desde, fecha_hasta, año=None, mes=None, compania="TODAS"):
    """Calcula KPIs para el reporte - Eficiencia y Cumplimiento desde Rendimiento"""
    
    # Total Metros
    df_met_gen = pd.DataFrame(load_metros_general())
    df_met_filtrado = df_met_gen[
        (df_met_gen['ano'] == int(año)) &
        (df_met_gen['mes'] == mes.upper())
    ]
    
    if compania != "TODAS":
        df_met_filtrado = df_met_filtrado[df_met_filtrado['compania'] == compania.strip()]
    
    met_ids = df_met_filtrado['id'].tolist()
    df_met_det = pd.DataFrame(load_metros_detalles())
    df_met_det_filtrado = df_met_det[df_met_det['registro_id'].isin(met_ids)]
    total_metros = df_met_det_filtrado['total_mp'].sum()
    
    # Consumo Total
    df_mov_gen = pd.DataFrame(load_movimientos_general())
    df_mov_filtrado = df_mov_gen[
        (df_mov_gen['ano'] == int(año)) &
        (df_mov_gen['mes'] == mes.upper()) &
        (df_mov_gen['movimiento'] == 'SALIDA')
    ]
    
    if compania != "TODAS":
        df_mov_filtrado = df_mov_filtrado[df_mov_filtrado['compania'] == compania.strip()]
    
    mov_ids = df_mov_filtrado['id'].tolist()
    df_mov_det = pd.DataFrame(load_movimientos_detalles())
    df_mov_det_filtrado = df_mov_det[df_mov_det['entrega_id'].isin(mov_ids)]
    total_consumo = df_mov_det_filtrado['cantidad'].abs().sum()
    
    # Equipos Activos
    equipos_activos = len(df_met_filtrado['equipo'].dropna().unique())
    
    # ============================================
    # 🔥 NUEVO: Calcular Eficiencia Global desde Rendimiento
    # ============================================
    
    eficiencia = 0
    cumplimiento = 0
    
    try:
        # Usar la misma lógica que process_rendimiento_aceros
        objetivos = load_objetivos()
        
        # Crear diccionario de objetivos
        obj_dict = {}
        for obj in objetivos:
            tipo = obj.get('Tipo Perforacion', '')
            familia = obj.get('Acero', '')
            objetivo_val = obj.get('Objetivo', 0)
            if objetivo_val is None:
                objetivo_val = 0
            obj_dict[(tipo, familia)] = objetivo_val
        
        # Obtener familias y tipos
        df_mov_det = pd.DataFrame(load_movimientos_detalles())
        mov_ids = df_mov_filtrado['id'].tolist()
        df_mov_det_filtrado = df_mov_det[df_mov_det['entrega_id'].isin(mov_ids)]
        df_mov_det_filtrado['cantidad'] = df_mov_det_filtrado['cantidad'].abs()
        
        # Obtener metros detalles
        met_ids = df_met_filtrado['id'].tolist()
        df_met_det_filtrado = df_met_det[df_met_det['registro_id'].isin(met_ids)]
        
        # Obtener tipos comunes
        tipos_mov = set(df_mov_filtrado['tipo_perforacion'].dropna().unique())
        tipos_met = set(df_met_filtrado['tipo_perforacion'].dropna().unique())
        tipos_comunes = list(tipos_mov.intersection(tipos_met))
        
        # Calcular eficiencias por tipo/familia
        eficiencias = []
        cumplimientos = []
        
        for tipo in tipos_comunes:
            # Metros para este tipo
            met_tipo = df_met_filtrado[df_met_filtrado['tipo_perforacion'] == tipo]
            met_ids_tipo = met_tipo['id'].tolist()
            df_met_tipo = df_met_det_filtrado[df_met_det_filtrado['registro_id'].isin(met_ids_tipo)]
            
            # Movimientos para este tipo
            df_mov_tipo = df_mov_filtrado[df_mov_filtrado['tipo_perforacion'] == tipo]
            mov_ids_tipo = df_mov_tipo['id'].tolist()
            df_mov_tipo_det = df_mov_det_filtrado[df_mov_det_filtrado['entrega_id'].isin(mov_ids_tipo)]
            
            # Familias
            familias = df_mov_tipo_det['familia'].dropna().unique()
            
            for familia in familias:
                cantidad = df_mov_tipo_det[df_mov_tipo_det['familia'] == familia]['cantidad'].sum()
                
                if familia.upper() == 'RIMADORAS':
                    metros = df_met_tipo['mp_rimado'].sum()
                else:
                    metros = df_met_tipo['total_mp'].sum()
                
                rendimiento = metros / cantidad if cantidad > 0 else 0
                objetivo = obj_dict.get((tipo, familia), 0)
                
                if objetivo > 0:
                    eficiencia_val = (rendimiento / objetivo * 100)
                    eficiencias.append(eficiencia_val)
                    cumplimientos.append(eficiencia_val)  # Cumplimiento = eficiencia (porcentaje)
        
        # Promedios
        if eficiencias:
            eficiencia = sum(eficiencias) / len(eficiencias)
        if cumplimientos:
            cumplimiento = sum(cumplimientos) / len(cumplimientos)
            
    except Exception as e:
        # Si falla, usar valores por defecto
        eficiencia = (total_metros / total_consumo) if total_consumo > 0 else 0
        cumplimiento = (total_metros / 1000 * 100) if total_metros > 0 else 0
    
    # Stock Crítico
    stock_data = load_stock_from_api()
    aceros = fetch_from_api("aceros")
    
    minimos = {}
    for a in aceros:
        codigo = a.get('codigo', '')
        minimo = a.get('minimo', 10)
        if minimo is None or not isinstance(minimo, (int, float)):
            minimo = 10
        minimos[codigo] = minimo
    
    stock_critico = 0
    for item in stock_data:
        codigo = item.get('codigo', '')
        stock = item.get('stock', 0)
        minimo = minimos.get(codigo, 10)
        if stock is None:
            stock = 0
        if minimo is None:
            minimo = 10
        if stock < minimo and stock > 0:
            stock_critico += 1
    
    return {
        'total_metros': total_metros,
        'total_consumo': total_consumo,
        'equipos_activos': equipos_activos,
        'eficiencia': eficiencia,
        'stock_critico': stock_critico,
        'cumplimiento': cumplimiento,
        'dias_mes': len(df_met_filtrado['fecha'].unique()) if not df_met_filtrado.empty else 0
    }



@st.cache_data(ttl=300)
def process_consumo_equipo(fecha_desde, fecha_hasta, año=None, mes=None, compania="TODAS"):
    """Procesa consumo por equipo - Familia, Cantidad, Metros, Rendimiento, Objetivo"""
    
    familias_target = ['SHANK', 'ACOPLES', 'BARRAS', 'RIMADORAS']
    
    # Cargar datos
    mov_detalles = load_movimientos_detalles()
    met_detalles = load_metros_detalles()
    mov_general = load_movimientos_general(fecha_desde, fecha_hasta)
    objetivos = load_objetivos()
    
    if not mov_general or not mov_detalles:
        return {}
    
    df_mov_gen = pd.DataFrame(mov_general)
    df_mov_det = pd.DataFrame(mov_detalles)
    df_met_det = pd.DataFrame(met_detalles)
    
    # Filtrar movimientos generales
    if año and mes:
        df_mov_gen = df_mov_gen[
            (df_mov_gen['ano'] == int(año)) &
            (df_mov_gen['mes'] == mes.upper())
        ]
    
    if fecha_desde and fecha_hasta:
        df_mov_gen = df_mov_gen[
            (pd.to_datetime(df_mov_gen['fecha']) >= pd.to_datetime(fecha_desde)) &
            (pd.to_datetime(df_mov_gen['fecha']) <= pd.to_datetime(fecha_hasta))
        ]
    
    if compania != "TODAS":
        df_mov_gen = df_mov_gen[df_mov_gen['compania'] == compania.strip()]
    
    if df_mov_gen.empty:
        return {}
    
    # Obtener IDs de movimientos
    mov_ids = df_mov_gen['id'].tolist()
    
    # Filtrar detalles de movimientos
    df_mov_det_filtrado = df_mov_det[df_mov_det['entrega_id'].isin(mov_ids)]
    
    if df_mov_det_filtrado.empty:
        return {}
    
    # 🔥 CORREGIDO: Unir con generales
    df_mov_det_filtrado = df_mov_det_filtrado.merge(
        df_mov_gen[['id', 'equipo', 'tipo_perforacion']],
        left_on='entrega_id',
        right_on='id',
        how='left'
    )
    
    # Filtrar solo familias target
    df_mov_det_filtrado = df_mov_det_filtrado[
        df_mov_det_filtrado['familia'].str.upper().isin(familias_target)
    ]
    
    if df_mov_det_filtrado.empty:
        return {}
    
    # 🔥 CORREGIDO: Usar 'tipo_perforacion_y' que es la que viene de df_mov_gen
    # O simplemente renombrar para simplificar
    if 'tipo_perforacion_y' in df_mov_det_filtrado.columns:
        df_mov_det_filtrado['tipo_perforacion'] = df_mov_det_filtrado['tipo_perforacion_y']
    elif 'tipo_perforacion_x' in df_mov_det_filtrado.columns:
        df_mov_det_filtrado['tipo_perforacion'] = df_mov_det_filtrado['tipo_perforacion_x']
    else:
        df_mov_det_filtrado['tipo_perforacion'] = 'GENERAL'
    
    # Crear diccionario de objetivos
    obj_dict = {}
    for obj in objetivos:
        tipo = obj.get('Tipo Perforacion', '')
        familia = obj.get('Acero', '')
        objetivo_val = obj.get('Objetivo', 0)
        if objetivo_val is None:
            objetivo_val = 0
        obj_dict[(tipo, familia)] = objetivo_val
    
    # Obtener metros por equipo y familia
    df_met_gen = pd.DataFrame(load_metros_general())
    
    if año and mes:
        df_met_gen = df_met_gen[
            (df_met_gen['ano'] == int(año)) &
            (df_met_gen['mes'] == mes.upper())
        ]
    
    if fecha_desde and fecha_hasta:
        df_met_gen = df_met_gen[
            (pd.to_datetime(df_met_gen['fecha']) >= pd.to_datetime(fecha_desde)) &
            (pd.to_datetime(df_met_gen['fecha']) <= pd.to_datetime(fecha_hasta))
        ]
    
    if compania != "TODAS":
        df_met_gen = df_met_gen[df_met_gen['compania'] == compania.strip()]
    
    met_ids = df_met_gen['id'].tolist()
    df_met_det_filtrado = df_met_det[df_met_det['registro_id'].isin(met_ids)]
    
    # 🔥 CORREGIDO: Agrupar por tipo_perforacion (la nueva columna), equipo, familia
    agrupado = df_mov_det_filtrado.groupby(['tipo_perforacion', 'equipo', 'familia']).agg({
        'cantidad': lambda x: x.abs().sum()
    }).reset_index()
    
    # Calcular metros por equipo
    resultados = {}
    
    tipos = agrupado['tipo_perforacion'].unique()
    
    for tipo in tipos:
        df_tipo = agrupado[agrupado['tipo_perforacion'] == tipo]
        resultados[tipo] = {}
        
        for equipo in df_tipo['equipo'].unique():
            df_equipo = df_tipo[df_tipo['equipo'] == equipo]
            
            # Obtener metros para este equipo
            met_ids_equipo = df_met_gen[df_met_gen['equipo'] == equipo]['id'].tolist()
            df_met_equipo = df_met_det_filtrado[df_met_det_filtrado['registro_id'].isin(met_ids_equipo)]
            
            total_mp_equipo = df_met_equipo['total_mp'].sum()
            mp_rimado_equipo = df_met_equipo['mp_rimado'].sum()
            
            filas = []
            for _, row in df_equipo.iterrows():
                familia = row['familia']
                cantidad = row['cantidad']
                
                if familia.upper() == 'RIMADORAS':
                    metros = mp_rimado_equipo
                else:
                    metros = total_mp_equipo
                
                rendimiento = metros / cantidad if cantidad > 0 else 0
                objetivo = obj_dict.get((tipo, familia), 0)
                
                filas.append({
                    'Familia': familia,
                    'Cantidad': cantidad,
                    'Metros': metros,
                    'Rendimiento': rendimiento,
                    'Objetivo': objetivo
                })
            
            if filas:
                resultados[tipo][equipo] = pd.DataFrame(filas)
    
    return resultados


@st.cache_data(ttl=300)
def process_consumo_brocas_operador(fecha_desde, fecha_hasta, año=None, mes=None, compania="TODAS"):
    """Procesa consumo de BROCAS por operador - con Metros y Rendimiento"""
    
    # Cargar datos
    mov_detalles = load_movimientos_detalles()
    met_detalles = load_metros_detalles()
    mov_general = load_movimientos_general(fecha_desde, fecha_hasta)
    
    if not mov_general or not mov_detalles:
        return {}
    
    df_mov_gen = pd.DataFrame(mov_general)
    df_mov_det = pd.DataFrame(mov_detalles)
    df_met_det = pd.DataFrame(met_detalles)
    
    # Filtrar movimientos generales
    if año and mes:
        df_mov_gen = df_mov_gen[
            (df_mov_gen['ano'] == int(año)) &
            (df_mov_gen['mes'] == mes.upper())
        ]
    
    if fecha_desde and fecha_hasta:
        df_mov_gen = df_mov_gen[
            (pd.to_datetime(df_mov_gen['fecha']) >= pd.to_datetime(fecha_desde)) &
            (pd.to_datetime(df_mov_gen['fecha']) <= pd.to_datetime(fecha_hasta))
        ]
    
    if compania != "TODAS":
        df_mov_gen = df_mov_gen[df_mov_gen['compania'] == compania.strip()]
    
    if df_mov_gen.empty:
        return {}
    
    # Obtener IDs de movimientos
    mov_ids = df_mov_gen['id'].tolist()
    
    # Filtrar detalles de movimientos
    df_mov_det_filtrado = df_mov_det[df_mov_det['entrega_id'].isin(mov_ids)]
    
    if df_mov_det_filtrado.empty:
        return {}
    
    # Unir con generales para obtener operador, guardia, tipo_perforacion
    df_mov_det_filtrado = df_mov_det_filtrado.merge(
        df_mov_gen[['id', 'operador', 'guardia', 'tipo_perforacion']],
        left_on='entrega_id',
        right_on='id',
        how='left'
    )
    
    # Renombrar tipo_perforacion
    if 'tipo_perforacion_y' in df_mov_det_filtrado.columns:
        df_mov_det_filtrado['tipo_perforacion'] = df_mov_det_filtrado['tipo_perforacion_y']
    elif 'tipo_perforacion_x' in df_mov_det_filtrado.columns:
        df_mov_det_filtrado['tipo_perforacion'] = df_mov_det_filtrado['tipo_perforacion_x']
    else:
        df_mov_det_filtrado['tipo_perforacion'] = 'GENERAL'
    
    # Filtrar solo BROCAS
    df_mov_det_filtrado = df_mov_det_filtrado[
        df_mov_det_filtrado['familia'].str.upper() == 'BROCAS'
    ]
    
    if df_mov_det_filtrado.empty:
        return {}
    
    # 🔥 CORREGIDO: Agrupar movimientos por tipo_perforacion, guardia, operador
    agrupado_mov = df_mov_det_filtrado.groupby(['tipo_perforacion', 'guardia', 'operador']).agg({
        'cantidad': lambda x: x.abs().sum()
    }).reset_index()
    agrupado_mov = agrupado_mov.rename(columns={'cantidad': 'Cantidad'})
    
    # 🔥 CORREGIDO: Obtener metros POR OPERADOR desde metros_general
    df_met_gen = pd.DataFrame(load_metros_general())
    
    if año and mes:
        df_met_gen = df_met_gen[
            (df_met_gen['ano'] == int(año)) &
            (df_met_gen['mes'] == mes.upper())
        ]
    
    if fecha_desde and fecha_hasta:
        df_met_gen = df_met_gen[
            (pd.to_datetime(df_met_gen['fecha']) >= pd.to_datetime(fecha_desde)) &
            (pd.to_datetime(df_met_gen['fecha']) <= pd.to_datetime(fecha_hasta))
        ]
    
    if compania != "TODAS":
        df_met_gen = df_met_gen[df_met_gen['compania'] == compania.strip()]
    
    # 🔥 Verificar si operador existe en metros_general
    if 'operador' not in df_met_gen.columns:
        # Si no existe, asignar 0 metros a todos
        agrupado_mov['Metros'] = 0
        agrupado_mov['Rendimiento'] = 0
    else:
        # Obtener IDs de metros
        met_ids = df_met_gen['id'].tolist()
        df_met_det_filtrado = df_met_det[df_met_det['registro_id'].isin(met_ids)]
        
        # Unir metros con operador
        df_met_det_filtrado = df_met_det_filtrado.merge(
            df_met_gen[['id', 'operador']],
            left_on='registro_id',
            right_on='id',
            how='left'
        )
        
        # 🔥 CORREGIDO: Agrupar metros por operador
        agrupado_met = df_met_det_filtrado.groupby(['operador']).agg({
            'total_mp': 'sum'
        }).reset_index()
        agrupado_met = agrupado_met.rename(columns={'total_mp': 'Metros'})
        
        # 🔥 Unir movimientos y metros por operador
        agrupado = agrupado_mov.merge(
            agrupado_met,
            on=['operador'],
            how='left'
        )
        agrupado['Metros'] = agrupado['Metros'].fillna(0)
        
        # Calcular Rendimiento
        agrupado['Rendimiento'] = agrupado.apply(
            lambda row: row['Metros'] / row['Cantidad'] if row['Cantidad'] > 0 else 0,
            axis=1
        )
        
        # Ordenar
        agrupado = agrupado.sort_values(['tipo_perforacion', 'guardia', 'Rendimiento'], ascending=[True, True, False])
    
    # Agrupar por tipo_perforacion
    tipos = agrupado['tipo_perforacion'].unique()
    resultados = {}
    
    for tipo in tipos:
        df_tipo = agrupado[agrupado['tipo_perforacion'] == tipo]
        
        guardias = df_tipo['guardia'].unique()
        resultados[tipo] = {}
        
        for guardia in guardias:
            df_guardia = df_tipo[df_tipo['guardia'] == guardia]
            resultados[tipo][guardia] = df_guardia[['operador', 'Cantidad', 'Metros', 'Rendimiento']]
    
    return resultados

@st.cache_data(ttl=300)
def process_metros_tipo(fecha_desde, fecha_hasta, año=None, mes=None, compania="TODAS"):
    """Procesa metros por tipo_perforacion"""
    
    # 🔥 Usar funciones importadas de api_client
    met_detalles = load_metros_detalles()
    met_general = load_metros_general(fecha_desde, fecha_hasta)
    
    if not met_general or not met_detalles:
        return pd.DataFrame()
    
    df_met_gen = pd.DataFrame(met_general)
    df_met_det = pd.DataFrame(met_detalles)
    
    if año and mes:
        df_met_gen = df_met_gen[
            (df_met_gen['ano'] == int(año)) &
            (df_met_gen['mes'] == mes.upper())
        ]
    
    if fecha_desde and fecha_hasta:
        df_met_gen = df_met_gen[
            (pd.to_datetime(df_met_gen['fecha']) >= pd.to_datetime(fecha_desde)) &
            (pd.to_datetime(df_met_gen['fecha']) <= pd.to_datetime(fecha_hasta))
        ]
    
    if compania != "TODAS":
        df_met_gen = df_met_gen[df_met_gen['compania'] == compania.strip()]
    
    if df_met_gen.empty:
        return pd.DataFrame()
    
    met_ids = df_met_gen['id'].tolist()
    df_met_det_filtrado = df_met_det[df_met_det['registro_id'].isin(met_ids)]
    
    if df_met_det_filtrado.empty:
        return pd.DataFrame()
    
    df_met_det_filtrado = df_met_det_filtrado.merge(
        df_met_gen[['id', 'tipo_perforacion']],
        left_on='registro_id',
        right_on='id',
        how='left'
    )
    
    resultado = df_met_det_filtrado.groupby('tipo_perforacion').agg({
        'total_mp': 'sum',
        'mp_rimado': 'sum'
    }).reset_index()
    
    resultado['% Rimado'] = (resultado['mp_rimado'] / resultado['total_mp'] * 100).fillna(0)
    
    resultado = resultado.rename(columns={
        'tipo_perforacion': 'Tipo Perforación',
        'total_mp': 'MP Total',
        'mp_rimado': 'MP Rimado'
    })
    
    return resultado

@st.cache_data(ttl=300)
def get_top_consumos(fecha_desde, fecha_hasta, año=None, mes=None, compania="TODAS", limit=5):
    """Obtiene los top consumos del período"""
    
    # 🔥 Usar funciones importadas de api_client
    mov_detalles = load_movimientos_detalles()
    mov_general = load_movimientos_general(fecha_desde, fecha_hasta)
    
    if not mov_general or not mov_detalles:
        return pd.DataFrame()
    
    df_mov_gen = pd.DataFrame(mov_general)
    df_mov_det = pd.DataFrame(mov_detalles)
    
    if año and mes:
        df_mov_gen = df_mov_gen[
            (df_mov_gen['ano'] == int(año)) &
            (df_mov_gen['mes'] == mes.upper()) &
            (df_mov_gen['movimiento'] == 'SALIDA')
        ]
    
    if fecha_desde and fecha_hasta:
        df_mov_gen = df_mov_gen[
            (pd.to_datetime(df_mov_gen['fecha']) >= pd.to_datetime(fecha_desde)) &
            (pd.to_datetime(df_mov_gen['fecha']) <= pd.to_datetime(fecha_hasta))
        ]
    
    if compania != "TODAS":
        df_mov_gen = df_mov_gen[df_mov_gen['compania'] == compania.strip()]
    
    if df_mov_gen.empty:
        return pd.DataFrame()
    
    mov_ids = df_mov_gen['id'].tolist()
    df_mov_det_filtrado = df_mov_det[df_mov_det['entrega_id'].isin(mov_ids)]
    
    agrupado = df_mov_det_filtrado.groupby(['codigo', 'descripcion']).agg({
        'cantidad': lambda x: x.abs().sum()
    }).reset_index()
    
    agrupado = agrupado.sort_values('cantidad', ascending=False).head(limit)
    
    return agrupado

@st.cache_data(ttl=300)
def get_evolucion_metros(fecha_desde, fecha_hasta, año=None, mes=None, compania="TODAS"):
    """Obtiene evolución de metros por día, separado por tipo_perforacion"""
    
    df_met_gen = pd.DataFrame(load_metros_general())
    
    if año and mes:
        df_met_gen = df_met_gen[
            (df_met_gen['ano'] == int(año)) &
            (df_met_gen['mes'] == mes.upper())
        ]
    
    if fecha_desde and fecha_hasta:
        df_met_gen = df_met_gen[
            (pd.to_datetime(df_met_gen['fecha']) >= pd.to_datetime(fecha_desde)) &
            (pd.to_datetime(df_met_gen['fecha']) <= pd.to_datetime(fecha_hasta))
        ]
    
    if compania != "TODAS":
        df_met_gen = df_met_gen[df_met_gen['compania'] == compania.strip()]
    
    if df_met_gen.empty:
        return pd.DataFrame()
    
    met_ids = df_met_gen['id'].tolist()
    df_met_det = pd.DataFrame(load_metros_detalles())
    df_met_det_filtrado = df_met_det[df_met_det['registro_id'].isin(met_ids)]
    
    # 🔥 Unir con tipo_perforacion
    df_met_det_filtrado = df_met_det_filtrado.merge(
        df_met_gen[['id', 'tipo_perforacion', 'fecha']],
        left_on='registro_id',
        right_on='id',
        how='left'
    )
    
    # 🔥 Agrupar por fecha y tipo_perforacion
    evolucion = df_met_det_filtrado.groupby(['fecha', 'tipo_perforacion']).agg({
        'total_mp': 'sum'
    }).reset_index()
    
    evolucion = evolucion.rename(columns={'total_mp': 'metros'})
    evolucion = evolucion.sort_values(['fecha', 'tipo_perforacion'])
    
    return evolucion
# ============================================
# FILTROS
# ============================================

st.title("📈 Reporte Gerencial")

# Cargar datos para filtros
with st.spinner("Cargando datos..."):
    movimientos_data = load_movimientos_general()
    df_mov = pd.DataFrame(movimientos_data)

if not df_mov.empty:
    años_disponibles = sorted(df_mov['ano'].unique())
    meses_disponibles = sorted(df_mov['mes'].unique())
    companias_disponibles = sorted(df_mov['compania'].dropna().unique())
else:
    años_disponibles = [2024, 2025, 2026]
    meses_disponibles = ['ENERO', 'FEBRERO', 'MARZO', 'ABRIL', 'MAYO', 'JUNIO',
                         'JULIO', 'AGOSTO', 'SEPTIEMBRE', 'OCTUBRE', 'NOVIEMBRE', 'DICIEMBRE']
    companias_disponibles = []

if not df_mov.empty:
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
    ultimo_mes = None
    ultimo_ano = None

# ============================================
# FILTROS
# ============================================

st.markdown("---")
col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns([1, 1, 1, 1, 0.8])

with col_f1:
    if ultimo_ano and ultimo_ano in años_disponibles:
        idx_ano = años_disponibles.index(ultimo_ano)
    else:
        idx_ano = len(años_disponibles) - 1 if años_disponibles else 0
    
    año_seleccionado = st.selectbox(
        "📅 Año",
        años_disponibles,
        index=idx_ano,
        key="año_reporte"
    )

with col_f2:
    if ultimo_mes and ultimo_mes in meses_disponibles:
        idx_mes = meses_disponibles.index(ultimo_mes)
    else:
        idx_mes = len(meses_disponibles) - 1 if meses_disponibles else 0
    
    mes_seleccionado = st.selectbox(
        "📆 Mes",
        meses_disponibles,
        index=idx_mes,
        key="mes_reporte"
    )

with col_f3:
    fecha_inicio = st.date_input(
        "📅 Desde",
        value=datetime.now() - timedelta(days=30),
        key="fecha_inicio_reporte"
    )

with col_f4:
    fecha_fin = st.date_input(
        "📅 Hasta",
        value=datetime.now(),
        key="fecha_fin_reporte"
    )

with col_f5:
    if st.button("🔄 Generar", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# ============================================
# PROCESAR KPIs
# ============================================

with st.spinner("Calculando indicadores..."):
    kpis = get_kpis_reporte(
        fecha_inicio, fecha_fin, año_seleccionado, mes_seleccionado, "TODAS"
    )

# ============================================
# SECCIÓN 1: CABECERA
# ============================================

st.subheader(f"📋 Reporte Operativo - Rock Tools Peru - JRC - {mes_seleccionado} {año_seleccionado}")
st.caption(f"📅 Período: {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}")

# Resumen Ejecutivo
resumen = f"""
📊 **Resumen Operativo:** Durante el mes de {mes_seleccionado} {año_seleccionado}, 
se perforaron **{kpis['total_metros']:,.2f} metros** con un consumo total de **{kpis['total_consumo']:,.0f} unidades**.
La eficiencia global fue de **{kpis['eficiencia']:.2f} m/unidad**, con **{kpis['equipos_activos']} equipos activos**.
"""
st.markdown(resumen)
st.markdown("---")

# ============================================
# SECCIÓN 2: KPIs ESTRATÉGICOS
# ============================================

st.subheader("📊 KPIs Estratégicos")

col_k1, col_k2, col_k3, col_k4, col_k5, col_k6 = st.columns(6)

with col_k1:
    st.metric("📏 Metros", f"{kpis['total_metros']:,.2f}")

with col_k2:
    st.metric("📦 Consumo", f"{kpis['total_consumo']:,.0f}")

with col_k3:
    st.metric("🎯 Eficiencia", f"{kpis['eficiencia']:.2f}")

with col_k4:
    st.metric("📊 Cumplimiento", f"{kpis['cumplimiento']:.1f}%")

with col_k5:
    st.metric("🚜 Equipos", f"{kpis['equipos_activos']}")

with col_k6:
    st.metric("⚠️ Stock Crítico", f"{kpis['stock_critico']}")

st.markdown("---")

# ============================================
# SECCIÓN 3: ANÁLISIS DE RENDIMIENTO
# ============================================

st.subheader("📈 Análisis de Rendimiento")

# 3.1 Evolución de Metros
# 3.1 Evolución de Metros
st.markdown("**📈 Evolución de Metros por Tipo Perforación**")

df_evolucion = get_evolucion_metros(
    fecha_inicio, fecha_fin, año_seleccionado, mes_seleccionado, "TODAS"
)

if not df_evolucion.empty:
    # 🔥 Gráfico con líneas separadas por tipo_perforacion
    fig_evolucion = px.line(
        df_evolucion,
        x='fecha',
        y='metros',
        color='tipo_perforacion',
        title=f"Evolución de Metros por Tipo - {mes_seleccionado} {año_seleccionado}",
        labels={'fecha': 'Fecha', 'metros': 'Metros (m)', 'tipo_perforacion': 'Tipo Perforación'},
        markers=True
    )
    fig_evolucion.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5
        )
    )
    st.plotly_chart(fig_evolucion, use_container_width=True)
else:
    st.info("ℹ️ No hay datos de evolución")

# 3.2 Rendimiento por Tipo Perforación
st.markdown("**📊 Rendimiento por Tipo Perforación**")

df_metros_tipo = process_metros_tipo(
    fecha_inicio, fecha_fin, año_seleccionado, mes_seleccionado, "TODAS"
)

if not df_metros_tipo.empty:
    fig_tipo = px.bar(
        df_metros_tipo,
        x='Tipo Perforación',
        y='MP Total',
        title="Metros por Tipo Perforación",
        labels={'MP Total': 'Metros (m)', 'Tipo Perforación': ''},
        color='MP Total',
        color_continuous_scale='Blues'
    )
    fig_tipo.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=300
    )
    st.plotly_chart(fig_tipo, use_container_width=True)
else:
    st.info("ℹ️ No hay datos de metros por tipo")

# 3.3 Top 5 Aceros Consumidos
st.markdown("Top 5 Aceros con mas consumos**")

df_top = get_top_consumos(
    fecha_inicio, fecha_fin, año_seleccionado, mes_seleccionado, "TODAS", 5
)

if not df_top.empty:
    df_top_display = df_top[['codigo', 'descripcion', 'cantidad']].copy()
    df_top_display.columns = ['Código', 'Descripción', 'Cantidad']
    
    html_top = crear_tabla_html(df_top_display, titulo="")
    st.markdown(html_top, unsafe_allow_html=True)
else:
    st.info("ℹ️ No hay datos de consumo")

st.markdown("---")

# ============================================
# SECCIÓN 4: CONSUMO POR EQUIPO
# ============================================

st.subheader("Analisis de rendimiento por Equipos")

with st.spinner("Procesando consumo por equipo..."):
    consumo_equipo = process_consumo_equipo(
        fecha_inicio, fecha_fin, año_seleccionado, mes_seleccionado, "TODAS"
    )

if consumo_equipo:
    for tipo in sorted(consumo_equipo.keys()):
        st.markdown(f"### 📌 {tipo}")
        
        equipos = list(consumo_equipo[tipo].keys())
        for i in range(0, len(equipos), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                idx = i + j
                if idx < len(equipos):
                    equipo = equipos[idx]
                    df = consumo_equipo[tipo][equipo]
                    
                    if not df.empty:
                        df_display = df.copy()
                        df_display['Cantidad'] = df_display['Cantidad'].apply(lambda x: f"{x:,.0f}")
                        df_display['Metros'] = df_display['Metros'].apply(lambda x: f"{x:,.2f}")
                        df_display['Rendimiento'] = df_display['Rendimiento'].apply(lambda x: f"{x:,.2f}")
                        df_display['Objetivo'] = df_display['Objetivo'].apply(lambda x: f"{x:,.2f}")
                        
                        with col:
                            html_table = crear_tabla_html(
                                df_display,
                                titulo=f"🚜 {equipo}"
                            )
                            st.markdown(html_table, unsafe_allow_html=True)
        
        st.markdown("---")
else:
    st.info("ℹ️ No hay datos de consumo por equipo")

# SECCIÓN 5: CONSUMO DE BROCAS POR OPERADOR
st.subheader("Rendimiento de brocas por Operador")

with st.spinner("Procesando consumo de BROCAS..."):
    consumo_brocas = process_consumo_brocas_operador(
        fecha_inicio, fecha_fin, año_seleccionado, mes_seleccionado, "TODAS"
    )

if consumo_brocas:
    for tipo in sorted(consumo_brocas.keys()):
        st.markdown(f"### 📌 {tipo}")
        
        guardias = list(consumo_brocas[tipo].keys())
        guardias_ordenadas = sorted(guardias)
        
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if j < len(guardias_ordenadas):
                guardia = guardias_ordenadas[j]
                df = consumo_brocas[tipo][guardia]
                
                if not df.empty:
                    # 🔥 Formatear columnas
                    df_display = df.copy()
                    df_display['Cantidad'] = df_display['Cantidad'].apply(lambda x: f"{x:,.0f}")
                    df_display['Metros'] = df_display['Metros'].apply(lambda x: f"{x:,.2f}")
                    df_display['Rendimiento'] = df_display['Rendimiento'].apply(lambda x: f"{x:,.2f}")
                    
                    with col:
                        html_table = crear_tabla_html(
                            df_display,
                            titulo=f"🛡️ Guardia: {guardia}",
                            columnas_estrechas=['operador', 'Cantidad', 'Metros', 'Rendimiento']
                        )
                        st.markdown(html_table, unsafe_allow_html=True)
        
        st.markdown("---")
else:
    st.info("ℹ️ No hay datos de consumo de BROCAS")

# ============================================
# SECCIÓN 6: METROS POR TIPO PERFORACIÓN
# ============================================

st.subheader("Resuemn de Metros por Tipo Perforación")

if not df_metros_tipo.empty:
    df_metros_display = df_metros_tipo.copy()
    df_metros_display['% Rimado'] = df_metros_display['% Rimado'].apply(lambda x: f"{x:.1f}%")
    df_metros_display['MP Total'] = df_metros_display['MP Total'].apply(lambda x: f"{x:,.2f}")
    df_metros_display['MP Rimado'] = df_metros_display['MP Rimado'].apply(lambda x: f"{x:,.2f}")
    
    html_metros = crear_tabla_html(df_metros_display, titulo="📊 Resumen de Metros")
    st.markdown(html_metros, unsafe_allow_html=True)
else:
    st.info("ℹ️ No hay datos de metros")

# ============================================
# PIE DE PÁGINA
# ============================================

st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.caption(f"📅 Reporte generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.caption(f"📊 Datos filtrados: {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}")