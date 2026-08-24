import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
import numpy as np

from utils.styles import apply_custom_styles

# Aplicar estilos personalizados
apply_custom_styles()

# ============================================
# CONFIGURACIÓN DE PÁGINA
# ============================================

st.title("📊 Dashboard - Resumen Ejecutivo")
st.markdown("---")

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
# FUNCIONES DE PROCESAMIENTO
# ============================================

def get_eficiencia_global(año, mes, compania):
    """Calcula la eficiencia global promedio de la página de Rendimiento"""
    try:
        # Cargar datos necesarios
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
        
        if df_mov_gen_filtrado.empty:
            return 0
        
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
        
        if df_met_gen_filtrado.empty:
            return 0
        
        # Obtener tipos comunes
        tipos_mov = set(df_mov_gen_filtrado['tipo_perforacion'].dropna().unique())
        tipos_met = set(df_met_gen_filtrado['tipo_perforacion'].dropna().unique())
        tipos_comunes = list(tipos_mov.intersection(tipos_met))
        
        if not tipos_comunes:
            return 0
        
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
            return 0
        
        # Crear diccionario de objetivos
        obj_dict = {}
        for obj in objetivos:
            tipo = obj.get('Tipo Perforacion', '')
            familia = obj.get('Acero', '')
            objetivo_val = obj.get('Objetivo', 0)
            obj_dict[(tipo, familia)] = objetivo_val
        
        # Obtener familias
        familias = df_mov_det_filtrado['familia'].dropna().unique()
        
        if len(familias) == 0:
            return 0
        
        # Calcular eficiencias
        eficiencias = []
        
        for tipo in tipos_comunes:
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
                
                if eficiencia > 0:
                    eficiencias.append(eficiencia)
        
        if not eficiencias:
            return 0
        
        return sum(eficiencias) / len(eficiencias)
        
    except Exception as e:
        return 0

def get_tendencia(año, mes, compania):
    """Calcula la tendencia vs mes anterior"""
    try:
        # Mapeo de meses
        meses_map = {
            'ENERO': 1, 'FEBRERO': 2, 'MARZO': 3, 'ABRIL': 4,
            'MAYO': 5, 'JUNIO': 6, 'JULIO': 7, 'AGOSTO': 8,
            'SEPTIEMBRE': 9, 'OCTUBRE': 10, 'NOVIEMBRE': 11, 'DICIEMBRE': 12
        }
        
        mes_actual_num = meses_map.get(mes.upper(), 1)
        mes_anterior_num = mes_actual_num - 1 if mes_actual_num > 1 else 12
        año_anterior = año if mes_actual_num > 1 else año - 1
        
        # Obtener mes anterior en texto
        meses_inv = {v: k for k, v in meses_map.items()}
        mes_anterior_texto = meses_inv.get(mes_anterior_num, 'ENERO')
        
        # Cargar metros generales
        df_met_gen = pd.DataFrame(load_metros_general())
        
        # Metros del mes actual
        df_actual = df_met_gen[
            (df_met_gen['ano'] == int(año)) &
            (df_met_gen['mes'] == mes.upper())
        ]
        
        if compania != "TODAS":
            df_actual = df_actual[df_actual['compania'] == compania.strip()]
        
        # Metros del mes anterior
        df_anterior = df_met_gen[
            (df_met_gen['ano'] == int(año_anterior)) &
            (df_met_gen['mes'] == mes_anterior_texto)
        ]
        
        if compania != "TODAS":
            df_anterior = df_anterior[df_anterior['compania'] == compania.strip()]
        
        # Obtener IDs de metros
        met_ids_actual = df_actual['id'].tolist()
        met_ids_anterior = df_anterior['id'].tolist()
        
        if not met_ids_actual or not met_ids_anterior:
            return 0
        
        # Obtener metros detalles
        df_met_det = pd.DataFrame(load_metros_detalles())
        
        df_met_det_actual = df_met_det[df_met_det['registro_id'].isin(met_ids_actual)]
        df_met_det_anterior = df_met_det[df_met_det['registro_id'].isin(met_ids_anterior)]
        
        total_actual = df_met_det_actual['total_mp'].sum()
        total_anterior = df_met_det_anterior['total_mp'].sum()
        
        if total_anterior == 0:
            return 0
        
        return ((total_actual - total_anterior) / total_anterior) * 100
        
    except Exception as e:
        return 0

def get_kpis_dashboard(año, mes, compania):
    """Calcula todos los KPIs del dashboard"""
    
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
    eficiencia = get_eficiencia_global(año, mes, compania)
    
    # Tendencia
    tendencia = get_tendencia(año, mes, compania)
    
    return {
        'total_metros': total_metros,
        'total_consumo': total_consumo,
        'equipos_activos': equipos_activos,
        'eficiencia': eficiencia,
        'tendencia': tendencia,
        'dias_mes': len(df_met_filtrado['fecha'].unique()) if not df_met_filtrado.empty else 0
    }

def get_top_consumos(año, mes, compania, limit=5):
    """Obtiene los top consumos del mes"""
    try:
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
        
        # Agrupar por código y descripción
        agrupado = df_mov_det_filtrado.groupby(['codigo', 'descripcion']).agg({
            'cantidad': lambda x: x.abs().sum()
        }).reset_index()
        
        agrupado = agrupado.sort_values('cantidad', ascending=False).head(limit)
        
        # Obtener última fecha de entrega para cada código
        fechas = df_mov_det_filtrado.groupby('codigo')['fecha'].max().reset_index()
        agrupado = agrupado.merge(fechas, on='codigo', how='left')
        
        return agrupado
        
    except Exception as e:
        return pd.DataFrame()

def get_consumo_por_familia(año, mes, compania):
    """Obtiene consumo por familia"""
    try:
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
        
        # Agrupar por familia
        agrupado = df_mov_det_filtrado.groupby('familia').agg({
            'cantidad': lambda x: x.abs().sum()
        }).reset_index()
        
        return agrupado
        
    except Exception as e:
        return pd.DataFrame()

def get_stock_critico(limit=5):
    """Obtiene los aceros con stock crítico (los 5 con menor stock)"""
    try:
        stock_data = load_stock_from_api()
        
        # Cargar aceros para obtener el mínimo
        aceros = fetch_from_api("aceros")
        minimos = {a.get('codigo', ''): a.get('minimo', 10) for a in aceros}
        
        # Filtrar solo productos con stock > 0
        items = []
        for item in stock_data:
            codigo = item.get('codigo', '')
            stock = item.get('stock', 0)
            if stock > 0:
                minimo = minimos.get(codigo, 10)
                if stock < minimo:
                    items.append({
                        'codigo': codigo,
                        'stock': stock,
                        'minimo': minimo
                    })
        
        # Ordenar por stock ascendente (menor primero)
        items = sorted(items, key=lambda x: x['stock'])[:limit]
        
        return pd.DataFrame(items)
        
    except Exception as e:
        return pd.DataFrame()

def get_rendimiento_compania(año, mes, compania):
    """Obtiene rendimiento por compañía"""
    try:
        if compania != "TODAS":
            # Si está filtrada una compañía, mostrar solo esa
            companias = [compania]
        else:
            # Si no, obtener todas
            df_mov = pd.DataFrame(load_movimientos_general())
            companias = sorted(df_mov['compania'].dropna().unique())
        
        resultados = []
        
        for comp in companias:
            # Metros
            df_met_gen = pd.DataFrame(load_metros_general())
            df_met_filtrado = df_met_gen[
                (df_met_gen['ano'] == int(año)) &
                (df_met_gen['mes'] == mes.upper()) &
                (df_met_gen['compania'] == comp)
            ]
            
            met_ids = df_met_filtrado['id'].tolist()
            df_met_det = pd.DataFrame(load_metros_detalles())
            df_met_det_filtrado = df_met_det[df_met_det['registro_id'].isin(met_ids)]
            
            metros = df_met_det_filtrado['total_mp'].sum()
            
            # Consumo
            df_mov_gen = pd.DataFrame(load_movimientos_general())
            df_mov_filtrado = df_mov_gen[
                (df_mov_gen['ano'] == int(año)) &
                (df_mov_gen['mes'] == mes.upper()) &
                (df_mov_gen['movimiento'] == 'SALIDA') &
                (df_mov_gen['compania'] == comp)
            ]
            
            mov_ids = df_mov_filtrado['id'].tolist()
            df_mov_det = pd.DataFrame(load_movimientos_detalles())
            df_mov_det_filtrado = df_mov_det[df_mov_det['entrega_id'].isin(mov_ids)]
            
            consumo = df_mov_det_filtrado['cantidad'].abs().sum()
            
            eficiencia = metros / consumo if consumo > 0 else 0
            
            resultados.append({
                'Compañía': comp,
                'Metros': metros,
                'Consumo': consumo,
                'Eficiencia': eficiencia
            })
        
        return pd.DataFrame(resultados)
        
    except Exception as e:
        return pd.DataFrame()

def get_rendimiento_equipos(año, mes, compania, limit=10):
    """Obtiene rendimiento por equipos (top 10)"""
    try:
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
        
        # Agrupar por equipo
        # Primero obtener equipo desde metros_general
        df_met_filtrado['metros'] = df_met_filtrado['id'].apply(
            lambda x: df_met_det_filtrado[df_met_det_filtrado['registro_id'] == x]['total_mp'].sum()
        )
        
        agrupado = df_met_filtrado.groupby('equipo').agg({
            'metros': 'sum'
        }).reset_index()
        
        agrupado = agrupado.sort_values('metros', ascending=False).head(limit)
        
        return agrupado
        
    except Exception as e:
        return pd.DataFrame()

# ============================================
# FILTROS
# ============================================

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

# Último mes con datos
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
# FILTROS EN UNA SOLA LÍNEA
# ============================================

st.markdown("---")
col_f1, col_f2, col_f3, col_f4 = st.columns([1, 1, 1, 0.8])

with col_f1:
    if ultimo_ano and ultimo_ano in años_disponibles:
        idx_ano = años_disponibles.index(ultimo_ano)
    else:
        idx_ano = len(años_disponibles) - 1 if años_disponibles else 0
    
    año_seleccionado = st.selectbox(
        "📅 Año",
        años_disponibles,
        index=idx_ano,
        key="año_dashboard"
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
        key="mes_dashboard"
    )

with col_f3:
    compania_seleccionada = st.selectbox(
        "🏢 Compañía",
        ["TODAS"] + list(companias_disponibles),
        key="compania_dashboard"
    )

with col_f4:
    if st.button("🔄 Actualizar", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

st.markdown("---")

# ============================================
# SECCIÓN 1: KPIs
# ============================================

with st.spinner("Calculando indicadores..."):
    kpis = get_kpis_dashboard(año_seleccionado, mes_seleccionado, compania_seleccionada)

col_k1, col_k2, col_k3, col_k4, col_k5 = st.columns(5)

with col_k1:
    st.metric(
        label="📏 Total Metros",
        value=f"{kpis['total_metros']:,.2f} m"
    )

with col_k2:
    st.metric(
        label="📦 Consumo Total",
        value=f"{kpis['total_consumo']:,.0f}"
    )

with col_k3:
    st.metric(
        label="🚜 Equipos Activos",
        value=f"{kpis['equipos_activos']}"
    )

with col_k4:
    st.metric(
        label="🎯 Eficiencia Global",
        value=f"{kpis['eficiencia']:.1f}%"
    )

with col_k5:
    tendencia_color = "normal" if kpis['tendencia'] >= 0 else "inverse"
    st.metric(
        label="📈 Tendencia vs Mes Anterior",
        value=f"{kpis['tendencia']:+.1f}%",
        delta=f"{kpis['tendencia']:+.1f}%",
        delta_color=tendencia_color
    )

st.markdown("---")

# ============================================
# SECCIÓN 2: GRÁFICOS
# ============================================

# Gráfico 1: Evolución de Metros
st.subheader("📈 Evolución de Metros")

# Cargar datos de evolución
df_met_gen = pd.DataFrame(load_metros_general())
df_met_filtrado = df_met_gen[
    (df_met_gen['ano'] == int(año_seleccionado)) &
    (df_met_gen['mes'] == mes_seleccionado.upper())
]

if compania_seleccionada != "TODAS":
    df_met_filtrado = df_met_filtrado[df_met_filtrado['compania'] == compania_seleccionada.strip()]

if not df_met_filtrado.empty:
    # Calcular metros por fecha
    df_met_det = pd.DataFrame(load_metros_detalles())
    
    evolucion = []
    for _, row in df_met_filtrado.iterrows():
        met_id = row['id']
        total_mp = df_met_det[df_met_det['registro_id'] == met_id]['total_mp'].sum()
        evolucion.append({
            'fecha': row['fecha'],
            'metros': total_mp
        })
    
    df_evolucion = pd.DataFrame(evolucion)
    df_evolucion = df_evolucion.groupby('fecha')['metros'].sum().reset_index()
    df_evolucion = df_evolucion.sort_values('fecha')
    
    if not df_evolucion.empty:
        fig_evolucion = px.line(
            df_evolucion,
            x='fecha',
            y='metros',
            title=f"Evolución de Metros - {mes_seleccionado} {año_seleccionado}",
            labels={'fecha': 'Fecha', 'metros': 'Metros (m)'},
            markers=True
        )
        fig_evolucion.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=400
        )
        st.plotly_chart(fig_evolucion, use_container_width=True)
    else:
        st.info("ℹ️ No hay datos de evolución para los filtros seleccionados")
else:
    st.info("ℹ️ No hay datos para los filtros seleccionados")

st.markdown("---")

# Gráficos en 2 columnas
col_g1, col_g2 = st.columns(2)

with col_g1:
    # Gráfico: Distribución por Tipo Perforación
    st.subheader("🔧 Distribución por Tipo Perforación")
    
    df_met_tipo = df_met_filtrado.groupby('tipo_perforacion').agg({
        'id': 'count'
    }).reset_index()
    df_met_tipo = df_met_tipo.rename(columns={'id': 'cantidad'})
    
    if not df_met_tipo.empty:
        fig_tipo = px.pie(
            df_met_tipo,
            values='cantidad',
            names='tipo_perforacion',
            title="Registros por Tipo Perforación",
            hole=0.3
        )
        fig_tipo.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=350
        )
        st.plotly_chart(fig_tipo, use_container_width=True)
    else:
        st.info("ℹ️ No hay datos")

with col_g2:
    # Gráfico: Consumo por Familia
    st.subheader("📊 Consumo por Familia")
    
    df_consumo_familia = get_consumo_por_familia(
        año_seleccionado,
        mes_seleccionado,
        compania_seleccionada
    )
    
    if not df_consumo_familia.empty:
        fig_consumo = px.bar(
            df_consumo_familia,
            x='familia',
            y='cantidad',
            title="Consumo por Familia",
            labels={'familia': 'Familia', 'cantidad': 'Cantidad'},
            color='cantidad',
            color_continuous_scale='Blues'
        )
        fig_consumo.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=350
        )
        st.plotly_chart(fig_consumo, use_container_width=True)
    else:
        st.info("ℹ️ No hay datos")

st.markdown("---")

# Gráficos en 2 columnas (segunda fila)
col_g3, col_g4 = st.columns(2)

with col_g3:
    # Gráfico: Rendimiento por Equipo
    st.subheader("🚜 Rendimiento por Equipo")
    
    df_rendimiento_equipos = get_rendimiento_equipos(
        año_seleccionado,
        mes_seleccionado,
        compania_seleccionada,
        limit=10
    )
    
    if not df_rendimiento_equipos.empty:
        fig_equipos = px.bar(
            df_rendimiento_equipos,
            x='metros',
            y='equipo',
            orientation='h',
            title="Top 10 Equipos por Metros",
            labels={'metros': 'Metros (m)', 'equipo': 'Equipo'},
            color='metros',
            color_continuous_scale='Viridis'
        )
        fig_equipos.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=350
        )
        st.plotly_chart(fig_equipos, use_container_width=True)
    else:
        st.info("ℹ️ No hay datos")

with col_g4:
    # Top 5 Consumos
    st.subheader("🏆 Top 5 Consumos del Mes")
    
    df_top = get_top_consumos(
        año_seleccionado,
        mes_seleccionado,
        compania_seleccionada,
        limit=5
    )
    
    if not df_top.empty:
        # Mostrar tabla con columnas formateadas
        st.dataframe(
            df_top[['codigo', 'descripcion', 'cantidad', 'fecha']],
            column_config={
                'codigo': st.column_config.TextColumn('Código'),
                'descripcion': st.column_config.TextColumn('Descripción'),
                'cantidad': st.column_config.NumberColumn('Cantidad', format="%.0f"),
                'fecha': st.column_config.DateColumn('Última Entrega')
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("ℹ️ No hay datos")

st.markdown("---")

# ============================================
# SECCIÓN 3: TABLAS DE DETALLE
# ============================================

col_t1, col_t2 = st.columns(2)

with col_t1:
    # Stock Crítico (Top 5 menor)
    st.subheader("⚠️ Stock Crítico (Top 5 menor)")
    
    df_stock = get_stock_critico(limit=5)
    
    if not df_stock.empty:
        # Calcular estado
        df_stock['estado'] = df_stock.apply(
            lambda x: '🔴 CRÍTICO' if x['stock'] < x['minimo'] else '🟡 BAJO',
            axis=1
        )
        
        st.dataframe(
            df_stock,
            column_config={
                'codigo': st.column_config.TextColumn('Código'),
                'stock': st.column_config.NumberColumn('Stock', format="%.0f"),
                'minimo': st.column_config.NumberColumn('Mínimo', format="%.0f"),
                'estado': st.column_config.TextColumn('Estado')
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("ℹ️ No hay stock crítico")

with col_t2:
    # Rendimiento por Compañía
    st.subheader("🏢 Rendimiento por Compañía")
    
    df_rendimiento_comp = get_rendimiento_compania(
        año_seleccionado,
        mes_seleccionado,
        compania_seleccionada
    )
    
    if not df_rendimiento_comp.empty:
        st.dataframe(
            df_rendimiento_comp,
            column_config={
                'Compañía': st.column_config.TextColumn('Compañía'),
                'Metros': st.column_config.NumberColumn('Metros', format="%.2f"),
                'Consumo': st.column_config.NumberColumn('Consumo', format="%.0f"),
                'Eficiencia': st.column_config.NumberColumn('Eficiencia', format="%.2f")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("ℹ️ No hay datos")

st.markdown("---")

# ============================================
# SECCIÓN 4: RESUMEN EJECUTIVO
# ============================================

st.subheader("📅 Resumen del Período")

col_r1, col_r2, col_r3, col_r4 = st.columns(4)

with col_r1:
    st.markdown(f"""
        <div style="background:#f8f9fa; padding:15px; border-radius:10px; text-align:center; border-left:4px solid #4472C4;">
            <div style="font-size:12px; color:#6c757d;">📅 Mes Actual</div>
            <div style="font-size:18px; font-weight:bold; color:#1a252f;">{mes_seleccionado} {año_seleccionado}</div>
        </div>
    """, unsafe_allow_html=True)

with col_r2:
    promedio = kpis['total_metros'] / kpis['dias_mes'] if kpis['dias_mes'] > 0 else 0
    st.markdown(f"""
        <div style="background:#f8f9fa; padding:15px; border-radius:10px; text-align:center; border-left:4px solid #28a745;">
            <div style="font-size:12px; color:#6c757d;">📏 Promedio Diario</div>
            <div style="font-size:18px; font-weight:bold; color:#1a252f;">{promedio:.1f} m/día</div>
        </div>
    """, unsafe_allow_html=True)

with col_r3:
    # Equipo destacado
    df_equipos = get_rendimiento_equipos(
        año_seleccionado,
        mes_seleccionado,
        compania_seleccionada,
        limit=1
    )
    if not df_equipos.empty:
        equipo_destacado = df_equipos.iloc[0]['equipo']
    else:
        equipo_destacado = "N/A"
    
    st.markdown(f"""
        <div style="background:#f8f9fa; padding:15px; border-radius:10px; text-align:center; border-left:4px solid #ffc107;">
            <div style="font-size:12px; color:#6c757d;">🚜 Equipo Destacado</div>
            <div style="font-size:18px; font-weight:bold; color:#1a252f;">{equipo_destacado}</div>
        </div>
    """, unsafe_allow_html=True)

with col_r4:
    # Acero más consumido
    df_top = get_top_consumos(
        año_seleccionado,
        mes_seleccionado,
        compania_seleccionada,
        limit=1
    )
    if not df_top.empty:
        acero_top = df_top.iloc[0]['descripcion'][:30]
    else:
        acero_top = "N/A"
    
    st.markdown(f"""
        <div style="background:#f8f9fa; padding:15px; border-radius:10px; text-align:center; border-left:4px solid #dc3545;">
            <div style="font-size:12px; color:#6c757d;">📦 Acero más Consumido</div>
            <div style="font-size:18px; font-weight:bold; color:#1a252f;">{acero_top}</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ============================================
# PIE DE PÁGINA
# ============================================

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.caption(f"📅 Dashboard actualizado: {datetime.now().strftime('%Y-%m-%d %H:%M')}")