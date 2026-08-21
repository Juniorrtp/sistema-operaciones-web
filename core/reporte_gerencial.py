from core.database import get_db
from collections import defaultdict
from datetime import datetime


def obtener_resumen_general(desde, hasta):
    """Obtiene resumen general del período"""
    db = get_db()
    
    print(f"🔍 Consultando resumen desde: {desde} hasta: {hasta}")
    
    # Total metros
    query_metros = """
        SELECT 
            COALESCE(SUM(d.mp_produccion), 0) as total_produccion,
            COALESCE(SUM(d.mp_rimado), 0) as total_rimado,
            COALESCE(SUM(d.total_mp), 0) as total_metros
        FROM metros_detalles d
        JOIN metros_general g ON d.registro_id = g.id
        WHERE g.fecha BETWEEN ? AND ?
    """
    
    # Total consumos
    query_consumos = """
        SELECT 
            COALESCE(SUM(ABS(dea.cantidad)), 0) as total_consumo
        FROM movimiento_detalles dea
        JOIN movimiento_general ea ON dea.entrega_id = ea.id
        WHERE ea.movimiento = 'SALIDA'
            AND ea.fecha BETWEEN ? AND ?
            AND dea.cantidad < 0
    """
    
    # Total equipos activos
    query_equipos = """
        SELECT COUNT(DISTINCT equipo) as total_equipos
        FROM metros_general
        WHERE fecha BETWEEN ? AND ?
    """
    
    # Total operadores activos
    query_operadores = """
        SELECT COUNT(DISTINCT operador) as total_operadores
        FROM metros_general
        WHERE fecha BETWEEN ? AND ? AND operador IS NOT NULL AND operador != ''
    """
    
    try:
        metros = db.execute_query(query_metros, (desde, hasta))
        consumos = db.execute_query(query_consumos, (desde, hasta))
        equipos = db.execute_query(query_equipos, (desde, hasta))
        operadores = db.execute_query(query_operadores, (desde, hasta))
        
        # 🔥 CORREGIDO: Manejar resultados como diccionarios
        metros_data = {}
        if metros and len(metros) > 0:
            if isinstance(metros[0], dict):
                metros_data = metros[0]
            else:
                metros_data = {'total_produccion': 0, 'total_rimado': 0, 'total_metros': 0}
        else:
            metros_data = {'total_produccion': 0, 'total_rimado': 0, 'total_metros': 0}
        
        consumos_data = {}
        if consumos and len(consumos) > 0:
            if isinstance(consumos[0], dict):
                consumos_data = consumos[0]
            else:
                consumos_data = {'total_consumo': 0}
        else:
            consumos_data = {'total_consumo': 0}
        
        equipos_data = {}
        if equipos and len(equipos) > 0:
            if isinstance(equipos[0], dict):
                equipos_data = equipos[0]
            else:
                equipos_data = {'total_equipos': 0}
        else:
            equipos_data = {'total_equipos': 0}
        
        operadores_data = {}
        if operadores and len(operadores) > 0:
            if isinstance(operadores[0], dict):
                operadores_data = operadores[0]
            else:
                operadores_data = {'total_operadores': 0}
        else:
            operadores_data = {'total_operadores': 0}
        
        dias = (datetime.strptime(hasta, "%Y-%m-%d") - datetime.strptime(desde, "%Y-%m-%d")).days + 1
        
        return {
            'metros': metros_data,
            'consumos': consumos_data,
            'equipos': equipos_data,
            'operadores': operadores_data,
            'dias': dias
        }
        
    except Exception as e:
        print(f"❌ Error en obtener_resumen_general: {e}")
        import traceback
        traceback.print_exc()
        return {
            'metros': {'total_metros': 0},
            'consumos': {'total_consumo': 0},
            'equipos': {'total_equipos': 0},
            'operadores': {'total_operadores': 0},
            'dias': 0
        }


def obtener_metros_por_tipo(desde, hasta):
    """Obtiene metros perforados por tipo de perforación"""
    db = get_db()
    
    query = """
        SELECT 
            UPPER(TRIM(eq.tipo_perforacion)) as tipo,
            COALESCE(SUM(d.total_mp), 0) as total_mp
        FROM metros_detalles d
        JOIN metros_general g ON d.registro_id = g.id
        JOIN equipo eq ON g.equipo = eq.equipo
        WHERE g.fecha BETWEEN ? AND ?
        GROUP BY UPPER(TRIM(eq.tipo_perforacion))
        ORDER BY total_mp DESC
    """
    
    try:
        resultados = db.execute_query(query, (desde, hasta))
        return [dict(row) for row in resultados] if resultados else []
    except Exception as e:
        print(f"Error en obtener_metros_por_tipo: {e}")
        return []


def obtener_consumo_por_familia(desde, hasta):
    """Obtiene consumo de aceros por familia Y tipo de perforación"""
    db = get_db()
    
    query = """
        SELECT 
            UPPER(TRIM(eq.tipo_perforacion)) as tipo_perforacion,
            UPPER(TRIM(dea.familia)) as familia,
            COALESCE(SUM(ABS(dea.cantidad)), 0) as total_consumo
        FROM movimiento_detalles dea
        JOIN movimiento_general ea ON dea.entrega_id = ea.id
        JOIN equipo eq ON ea.equipo = eq.equipo
        WHERE ea.movimiento = 'SALIDA'
            AND ea.fecha BETWEEN ? AND ?
            AND dea.cantidad < 0
            AND dea.familia IS NOT NULL 
            AND TRIM(dea.familia) != ''
        GROUP BY UPPER(TRIM(eq.tipo_perforacion)), UPPER(TRIM(dea.familia))
        ORDER BY tipo_perforacion, total_consumo DESC
    """
    
    try:
        resultados = db.execute_query(query, (desde, hasta))
        return [dict(row) for row in resultados] if resultados else []
    except Exception as e:
        print(f"Error en obtener_consumo_por_familia: {e}")
        return []


def obtener_top_equipos_por_tipo(desde, hasta, top=3):
    """Obtiene top equipos por tipo de perforación"""
    db = get_db()
    
    query = """
        SELECT 
            UPPER(TRIM(eq.tipo_perforacion)) as tipo,
            g.equipo,
            COALESCE(SUM(d.total_mp), 0) as total_mp
        FROM metros_detalles d
        JOIN metros_general g ON d.registro_id = g.id
        JOIN equipo eq ON g.equipo = eq.equipo
        WHERE g.fecha BETWEEN ? AND ?
            AND g.equipo IS NOT NULL 
            AND g.equipo != ''
        GROUP BY UPPER(TRIM(eq.tipo_perforacion)), g.equipo
        HAVING COALESCE(SUM(d.total_mp), 0) > 0
        ORDER BY tipo, total_mp DESC
    """
    
    try:
        resultados = db.execute_query(query, (desde, hasta))
        
        tipo_equipos = defaultdict(list)
        for row in resultados:
            tipo = row.get('tipo')
            if tipo:
                tipo_equipos[tipo].append({
                    'equipo': row.get('equipo'),
                    'total_mp': row.get('total_mp', 0)
                })
        
        top_por_tipo = {}
        for tipo, equipos in tipo_equipos.items():
            top_por_tipo[tipo] = sorted(equipos, key=lambda x: x['total_mp'], reverse=True)[:top]
        
        return top_por_tipo
    except Exception as e:
        print(f"Error en obtener_top_equipos_por_tipo: {e}")
        return {}


def obtener_rendimiento_por_equipo(desde, hasta):
    """Obtiene rendimiento por equipo (metros / consumo) para cada familia"""
    db = get_db()
    
    # Consumo por equipo y familia
    query_consumo = """
        SELECT 
            ea.equipo,
            UPPER(TRIM(dea.familia)) as familia,
            COALESCE(SUM(ABS(dea.cantidad)), 0) as consumo
        FROM movimiento_detalles dea
        JOIN movimiento_general ea ON dea.entrega_id = ea.id
        WHERE ea.movimiento = 'SALIDA'
            AND ea.fecha BETWEEN ? AND ?
            AND dea.cantidad < 0
            AND UPPER(TRIM(dea.familia)) IN ('BARRAS', 'BROCAS', 'ACOPLES', 'SHANK', 'RIMADORAS')
        GROUP BY ea.equipo, UPPER(TRIM(dea.familia))
        HAVING COALESCE(SUM(ABS(dea.cantidad)), 0) > 0
    """
    
    # Metros por equipo
    query_metros = """
        SELECT 
            g.equipo,
            COALESCE(SUM(d.total_mp), 0) as total_mp
        FROM metros_detalles d
        JOIN metros_general g ON d.registro_id = g.id
        WHERE g.fecha BETWEEN ? AND ?
            AND g.equipo IS NOT NULL 
            AND g.equipo != ''
        GROUP BY g.equipo
        HAVING COALESCE(SUM(d.total_mp), 0) > 0
    """
    
    try:
        consumos = db.execute_query(query_consumo, (desde, hasta))
        metros = db.execute_query(query_metros, (desde, hasta))
        
        # Diccionario de metros por equipo
        metros_por_equipo = {}
        for row in metros:
            equipo = row.get('equipo') or "SIN EQUIPO"
            metros_por_equipo[equipo] = row.get('total_mp', 0)
        
        # Procesar consumos y calcular rendimiento
        rendimiento_por_equipo = defaultdict(dict)
        for row in consumos:
            equipo = row.get('equipo') or "SIN EQUIPO"
            familia = row.get('familia') or "OTROS"
            consumo = row.get('consumo', 0)
            
            metros_equipo = metros_por_equipo.get(equipo, 0)
            rendimiento = metros_equipo / consumo if consumo > 0 else 0
            
            rendimiento_por_equipo[equipo][familia] = {
                'metros': metros_equipo,
                'consumo': consumo,
                'rendimiento': round(rendimiento, 2)
            }
        
        # Calcular rendimiento total por equipo
        for equipo, familias in rendimiento_por_equipo.items():
            total_consumo = sum(f.get('consumo', 0) for f in familias.values())
            total_metros = sum(f.get('metros', 0) for f in familias.values())
            rendimiento_total = total_metros / total_consumo if total_consumo > 0 else 0
            familias['TOTAL'] = {
                'metros': total_metros,
                'consumo': total_consumo,
                'rendimiento': round(rendimiento_total, 2)
            }
        
        return dict(rendimiento_por_equipo)
    except Exception as e:
        print(f"Error en obtener_rendimiento_por_equipo: {e}")
        return {}


def obtener_rendimiento_operadores_brocas(desde, hasta):
    """Obtiene rendimiento de BROCAS por operador, clasificado por tipo y guardia"""
    db = get_db()
    
    query = """
        SELECT 
            UPPER(TRIM(eq.tipo_perforacion)) as tipo,
            ea.operador,
            COALESCE(ea.guardia, 'G') as guardia,
            COALESCE(SUM(ABS(dea.cantidad)), 0) as total_brocas,
            COALESCE((
                SELECT COALESCE(SUM(d.mp_produccion), 0)
                FROM metros_general g
                JOIN metros_detalles d ON g.id = d.registro_id
                WHERE g.operador = ea.operador
                    AND g.guardia = ea.guardia
                    AND g.fecha BETWEEN ? AND ?
            ), 0) as metros_perforados
        FROM movimiento_detalles dea
        JOIN movimiento_general ea ON dea.entrega_id = ea.id
        JOIN equipo eq ON ea.equipo = eq.equipo
        WHERE ea.movimiento = 'SALIDA'
            AND ea.fecha BETWEEN ? AND ?
            AND dea.cantidad < 0
            AND UPPER(TRIM(dea.familia)) = 'BROCAS'
            AND ea.operador IS NOT NULL 
            AND ea.operador != ''
        GROUP BY UPPER(TRIM(eq.tipo_perforacion)), ea.operador, ea.guardia
        HAVING COALESCE(SUM(ABS(dea.cantidad)), 0) > 0
        ORDER BY tipo, guardia
    """
    
    try:
        resultados = db.execute_query(query, (desde, hasta, desde, hasta))
        
        # Agrupar por tipo y guardia
        operadores_por_tipo = defaultdict(lambda: defaultdict(list))
        
        for row in resultados:
            tipo = row.get('tipo') or "SIN TIPO"
            guardia = row.get('guardia') or "G"
            operador = row.get('operador') or "SIN OPERADOR"
            brocas = row.get('total_brocas', 0)
            metros = row.get('metros_perforados', 0)
            rendimiento = metros / brocas if brocas > 0 else 0
            
            operadores_por_tipo[tipo][guardia].append({
                'operador': operador,
                'brocas': brocas,
                'metros': metros,
                'rendimiento': round(rendimiento, 2)
            })
        
        return dict(operadores_por_tipo)
    except Exception as e:
        print(f"Error en obtener_rendimiento_operadores_brocas: {e}")
        return {}


def obtener_stock_critico(umbral=5):
    """Obtiene productos con stock crítico"""
    db = get_db()
    
    query = """
        SELECT 
            codigo,
            MAX(descripcion) as descripcion,
            COALESCE(SUM(cantidad), 0) as stock
        FROM movimiento_detalles
        WHERE cantidad > 0
        GROUP BY codigo
        HAVING COALESCE(SUM(cantidad), 0) <= ?
        ORDER BY stock ASC
    """
    
    try:
        resultados = db.execute_query(query, (umbral,))
        return [dict(row) for row in resultados] if resultados else []
    except Exception as e:
        print(f"Error en obtener_stock_critico: {e}")
        return []