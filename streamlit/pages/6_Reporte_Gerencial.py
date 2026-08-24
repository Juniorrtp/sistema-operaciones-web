import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import logging
import io
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

from utils.styles import apply_custom_styles

# Aplicar estilos personalizados
apply_custom_styles()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# FUNCIONES DE CONEXIÓN A API
# ============================================

@st.cache_resource
def get_api_session():
    session = requests.Session()
    return session

def fetch_from_api(endpoint, params=None):
    try:
        base_url = st.secrets.get("API_URL", "https://sistema-operaciones-web.onrender.com")
        url = f"{base_url}/api/{endpoint}"
        response = get_api_session().get(url, params=params, timeout=60)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"❌ Error al conectar con la API: {e}")
        return []

# ============================================
# CARGA DE DATOS CON CACHÉ
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
            if 'estado' in row and row['estado']:
                row['estado'] = row['estado'].strip().upper()
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

@st.cache_data(ttl=600)
def load_stock_from_api():
    return fetch_from_api("stock")

@st.cache_data(ttl=3600)
def load_objetivos():
    return fetch_from_api("objetivos")

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
        # Ancho más estrecho para columnas específicas
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
            
            # Estilo según columna
            if col == 'Guardia':
                estilo = 'text-align:center; font-weight:600;'
            elif col == 'Familia':
                estilo = 'text-align:left; font-weight:500;'
            elif isinstance(valor, (int, float)):
                estilo = 'text-align:right;'
            else:
                estilo = 'text-align:left;'
            
            # Formatear valores
            if isinstance(valor, (int, float)):
                if col in ['Metros', 'Rendimiento', 'Objetivo']:
                    valor_display = f'{valor:,.2f}'
                else:
                    valor_display = f'{valor:,.0f}'
            else:
                valor_display = valor
            
            # Ancho para columnas estrechas
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
    """Calcula KPIs para el reporte"""
    
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
    
    # Eficiencia Global
    eficiencia = (total_metros / total_consumo) if total_consumo > 0 else 0
    
    # Stock Crítico
    stock_data = load_stock_from_api()
    aceros = fetch_from_api("aceros")
    
    # 🔧 CORREGIDO: Manejar valores None en minimo
    minimos = {}
    for a in aceros:
        codigo = a.get('codigo', '')
        minimo = a.get('minimo', 10)
        # Si minimo es None o no es un número, usar 10 como default
        if minimo is None or not isinstance(minimo, (int, float)):
            minimo = 10
        minimos[codigo] = minimo
    
    stock_critico = 0
    for item in stock_data:
        codigo = item.get('codigo', '')
        stock = item.get('stock', 0)
        minimo = minimos.get(codigo, 10)
        # Asegurar que stock y minimo son números
        if stock is None:
            stock = 0
        if minimo is None:
            minimo = 10
        if stock < minimo and stock > 0:
            stock_critico += 1
    
    # Cumplimiento de Metas (ejemplo con objetivo de 1000m)
    objetivo_mensual = 1000
    cumplimiento = (total_metros / objetivo_mensual * 100) if objetivo_mensual > 0 else 0
    
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
    
    # 🔧 CORREGIDO: Unir con generales para obtener columnas faltantes
    # Asegurar que traemos todas las columnas necesarias
    columnas_necesarias = ['id', 'equipo', 'tipo_perforacion']
    # Verificar que las columnas existen en df_mov_gen
    columnas_existentes = [col for col in columnas_necesarias if col in df_mov_gen.columns]
    
    if not columnas_existentes:
        return {}
    
    df_mov_det_filtrado = df_mov_det_filtrado.merge(
        df_mov_gen[columnas_existentes],
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
    
    # 🔧 VERIFICAR: Mostrar columnas disponibles si hay error
    # logger.info(f"Columnas en df_mov_det_filtrado: {df_mov_det_filtrado.columns.tolist()}")
    
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
    
    # 🔧 CORREGIDO: Verificar que las columnas existen antes de agrupar
    columnas_agrupar = ['tipo_perforacion', 'equipo', 'familia']
    columnas_existentes_agrupar = [col for col in columnas_agrupar if col in df_mov_det_filtrado.columns]
    
    if not columnas_existentes_agrupar:
        return {}
    
    # Agrupar por tipo_perforacion, equipo, familia
    agrupado = df_mov_det_filtrado.groupby(columnas_existentes_agrupar).agg({
        'cantidad': lambda x: x.abs().sum()
    }).reset_index()
    
    # 🔧 CORREGIDO: Si 'tipo_perforacion' no existe, usar un valor por defecto
    if 'tipo_perforacion' not in agrupado.columns:
        agrupado['tipo_perforacion'] = 'GENERAL'
    
    # Calcular metros por equipo
    resultados = {}
    
    for tipo in agrupado['tipo_perforacion'].unique():
        df_tipo = agrupado[agrupado['tipo_perforacion'] == tipo]
        resultados[tipo] = {}
        
        for equipo in df_tipo['equipo'].unique():
            df_equipo = df_tipo[df_tipo['equipo'] == equipo]
            
            # Obtener metros para este equipo
            met_ids_equipo = df_met_gen[df_met_gen['equipo'] == equipo]['id'].tolist()
            df_met_equipo = df_met_det_filtrado[df_met_det_filtrado['registro_id'].isin(met_ids_equipo)]
            
            filas = []
            for _, row in df_equipo.iterrows():
                familia = row['familia']
                cantidad = row['cantidad']
                
                # Calcular metros según familia
                if familia.upper() == 'RIMADORAS':
                    metros = df_met_equipo['mp_rimado'].sum()
                else:
                    metros = df_met_equipo['total_mp'].sum()
                
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
    """Procesa consumo de BROCAS por operador - solo Cantidad"""
    
    mov_detalles = load_movimientos_detalles()
    mov_general = load_movimientos_general(fecha_desde, fecha_hasta)
    
    if not mov_general or not mov_detalles:
        return {}
    
    df_mov_gen = pd.DataFrame(mov_general)
    df_mov_det = pd.DataFrame(mov_detalles)
    
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
    
    # 🔧 CORREGIDO: Unir con generales para obtener columnas faltantes
    # Verificar qué columnas existen en df_mov_gen
    columnas_necesarias = ['id', 'operador', 'guardia', 'tipo_perforacion']
    columnas_existentes = [col for col in columnas_necesarias if col in df_mov_gen.columns]
    
    if not columnas_existentes:
        return {}
    
    df_mov_det_filtrado = df_mov_det_filtrado.merge(
        df_mov_gen[columnas_existentes],
        left_on='entrega_id',
        right_on='id',
        how='left'
    )
    
    # Filtrar solo BROCAS
    df_mov_det_filtrado = df_mov_det_filtrado[
        df_mov_det_filtrado['familia'].str.upper() == 'BROCAS'
    ]
    
    if df_mov_det_filtrado.empty:
        return {}
    
    # 🔧 CORREGIDO: Verificar columnas antes de agrupar
    columnas_agrupar = ['tipo_perforacion', 'guardia', 'operador']
    columnas_existentes_agrupar = [col for col in columnas_agrupar if col in df_mov_det_filtrado.columns]
    
    if not columnas_existentes_agrupar:
        return {}
    
    # Agrupar por tipo_perforacion, guardia, operador
    agrupado = df_mov_det_filtrado.groupby(columnas_existentes_agrupar).agg({
        'cantidad': lambda x: x.abs().sum()
    }).reset_index()
    agrupado = agrupado.rename(columns={'cantidad': 'Cantidad'})
    
    # 🔧 CORREGIDO: Si 'tipo_perforacion' no existe, usar un valor por defecto
    if 'tipo_perforacion' not in agrupado.columns:
        agrupado['tipo_perforacion'] = 'GENERAL'
    
    # Ordenar por guardia y cantidad
    if 'guardia' in agrupado.columns and 'Cantidad' in agrupado.columns:
        agrupado = agrupado.sort_values(['tipo_perforacion', 'guardia', 'Cantidad'], ascending=[True, True, False])
    
    # Agrupar por tipo_perforacion
    tipos = agrupado['tipo_perforacion'].unique()
    resultados = {}
    
    for tipo in tipos:
        df_tipo = agrupado[agrupado['tipo_perforacion'] == tipo]
        # Seleccionar columnas disponibles
        columnas_resultado = []
        for col in ['guardia', 'operador', 'Cantidad']:
            if col in df_tipo.columns:
                columnas_resultado.append(col)
        
        if columnas_resultado:
            resultados[tipo] = df_tipo[columnas_resultado]
    
    return resultados


@st.cache_data(ttl=300)
def process_metros_tipo(fecha_desde, fecha_hasta, año=None, mes=None, compania="TODAS"):
    """Procesa metros por tipo_perforacion"""
    
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
    else:
        df_mov_gen = df_mov_gen[df_mov_gen['movimiento'] == 'SALIDA']
    
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
    """Obtiene evolución de metros por día"""
    
    df_met_gen = pd.DataFrame(load_metros_general())
    
    if año and mes:
        df_met_gen = df_met_gen[
            (df_met_gen['ano'] == int(año)) &
            (df_met_gen['mes'] == mes.upper())
        ]
    else:
        df_met_gen = df_met_gen
    
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
    
    evolucion = []
    for _, row in df_met_gen.iterrows():
        met_id = row['id']
        total_mp = df_met_det_filtrado[df_met_det_filtrado['registro_id'] == met_id]['total_mp'].sum()
        evolucion.append({
            'fecha': row['fecha'],
            'metros': total_mp
        })
    
    df_evolucion = pd.DataFrame(evolucion)
    df_evolucion = df_evolucion.groupby('fecha')['metros'].sum().reset_index()
    df_evolucion = df_evolucion.sort_values('fecha')
    
    return df_evolucion

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

st.subheader(f"📋 Reporte Gerencial - {mes_seleccionado} {año_seleccionado}")
st.caption(f"📅 Período: {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}")

# Resumen Ejecutivo
resumen = f"""
📊 **Resumen Ejecutivo:** Durante el mes de {mes_seleccionado} {año_seleccionado}, 
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
    st.metric("⚠️ Stock Crítico", f"{kpis['stock_critico']}", delta="⚠️ Revisar")

st.markdown("---")

# ============================================
# SECCIÓN 3: ANÁLISIS DE RENDIMIENTO
# ============================================

st.subheader("📈 Análisis de Rendimiento")

# 3.1 Evolución de Metros
st.markdown("**📈 Evolución de Metros**")

df_evolucion = get_evolucion_metros(
    fecha_inicio, fecha_fin, año_seleccionado, mes_seleccionado, "TODAS"
)

if not df_evolucion.empty:
    fig_evolucion = px.line(
        df_evolucion,
        x='fecha',
        y='metros',
        title=f"Evolución Diaria - {mes_seleccionado} {año_seleccionado}",
        labels={'fecha': 'Fecha', 'metros': 'Metros (m)'},
        markers=True
    )
    fig_evolucion.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        height=350
    )
    st.plotly_chart(fig_evolucion, use_container_width=True)

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

# 3.3 Top 5 Aceros Consumidos
st.markdown("**🏆 Top 5 Aceros Consumidos**")

df_top = get_top_consumos(
    fecha_inicio, fecha_fin, año_seleccionado, mes_seleccionado, "TODAS", 5
)

if not df_top.empty:
    # Mostrar solo código y cantidad
    df_top_display = df_top[['codigo', 'descripcion', 'cantidad']].copy()
    df_top_display.columns = ['Código', 'Descripción', 'Cantidad']
    
    html_top = crear_tabla_html(df_top_display, titulo="")
    st.markdown(html_top, unsafe_allow_html=True)
else:
    st.info("ℹ️ No hay datos de consumo")

st.markdown("---")

# ============================================
# SECCIÓN 4: CONSUMO POR EQUIPO (por Tipo Perforación)
# ============================================

st.subheader("🔧 Consumo por Familia, Tipo Perforación y Equipo")

with st.spinner("Procesando consumo por equipo..."):
    consumo_equipo = process_consumo_equipo(
        fecha_inicio, fecha_fin, año_seleccionado, mes_seleccionado, "TODAS"
    )

if consumo_equipo:
    for tipo in sorted(consumo_equipo.keys()):
        st.markdown(f"**📌 {tipo}**")
        
        # Crear columnas para los equipos (2 por fila)
        equipos = list(consumo_equipo[tipo].keys())
        for i in range(0, len(equipos), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                idx = i + j
                if idx < len(equipos):
                    equipo = equipos[idx]
                    df = consumo_equipo[tipo][equipo]
                    
                    if not df.empty:
                        # Formatear columnas para mostrar
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

# ============================================
# SECCIÓN 5: CONSUMO DE BROCAS POR OPERADOR (3 columnas)
# ============================================

st.subheader("👷 Consumo de BROCAS por Operador")

with st.spinner("Procesando consumo de BROCAS..."):
    consumo_brocas = process_consumo_brocas_operador(
        fecha_inicio, fecha_fin, año_seleccionado, mes_seleccionado, "TODAS"
    )

if consumo_brocas:
    # Mostrar en 3 columnas
    tipos = list(consumo_brocas.keys())
    for i in range(0, len(tipos), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            idx = i + j
            if idx < len(tipos):
                tipo = tipos[idx]
                df = consumo_brocas[tipo]
                
                if not df.empty:
                    # Formatear
                    df_display = df.copy()
                    df_display['Cantidad'] = df_display['Cantidad'].apply(lambda x: f"{x:,.0f}")
                    
                    with col:
                        html_table = crear_tabla_html(
                            df_display,
                            titulo=f"🔧 {tipo}",
                            columnas_estrechas=['Guardia', 'Operador', 'Cantidad']
                        )
                        st.markdown(html_table, unsafe_allow_html=True)
else:
    st.info("ℹ️ No hay datos de consumo de BROCAS")

st.markdown("---")

# ============================================
# SECCIÓN 6: METROS POR TIPO PERFORACIÓN
# ============================================

st.subheader("📏 Metros por Tipo Perforación")

if not df_metros_tipo.empty:
    df_metros_display = df_metros_tipo.copy()
    df_metros_display['% Rimado'] = df_metros_display['% Rimado'].apply(lambda x: f"{x:.1f}%")
    df_metros_display['MP Total'] = df_metros_display['MP Total'].apply(lambda x: f"{x:,.2f}")
    df_metros_display['MP Rimado'] = df_metros_display['MP Rimado'].apply(lambda x: f"{x:,.2f}")
    
    html_metros = crear_tabla_html(df_metros_display, titulo="📊 Resumen de Metros")
    st.markdown(html_metros, unsafe_allow_html=True)

# ============================================
# PIE DE PÁGINA
# ============================================

st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.caption(f"📅 Reporte generado: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    st.caption(f"📊 Datos filtrados: {fecha_inicio.strftime('%d/%m/%Y')} - {fecha_fin.strftime('%d/%m/%Y')}")