from core.database import get_db
from collections import defaultdict
from datetime import datetime


def obtener_consumo_equipo(desde, hasta, tipo=None, compania=None):
    """Obtiene consumo por equipo para cada familia"""
    db = get_db()
    
    query = """
        SELECT 
            UPPER(TRIM(md.familia)) as familia,
            mg.equipo,
            SUM(md.cantidad * -1) as total_consumo
        FROM movimiento_general mg
        JOIN movimiento_detalles md ON mg.id = md.entrega_id
        WHERE mg.movimiento = 'SALIDA'
            AND md.cantidad < 0
            AND mg.fecha BETWEEN ? AND ?
    """
    params = [desde, hasta]
    
    if tipo:
        query += " AND mg.tipo_perforacion = ?"
        params.append(tipo)
    if compania:
        query += " AND mg.compania = ?"
        params.append(compania)
    
    query += " GROUP BY md.familia, mg.equipo ORDER BY mg.equipo"
    
    try:
        resultados = db.execute_query(query, params)
        return [dict(row) for row in resultados]
    except Exception as e:
        print(f"Error en obtener_consumo_equipo: {e}")
        return []


def obtener_metros_equipo(desde, hasta, tipo=None, compania=None):
    """Obtiene metros por equipo"""
    db = get_db()
    
    query = """
        SELECT 
            mg.equipo,
            SUM(md.mp_produccion) as mp_produccion,
            SUM(md.mp_rimado) as mp_rimado,
            SUM(md.total_mp) as total_mp
        FROM metros_general mg
        JOIN metros_detalles md ON mg.id = md.registro_id
        WHERE mg.fecha BETWEEN ? AND ?
    """
    params = [desde, hasta]
    
    if tipo:
        query += " AND mg.tipo_perforacion = ?"
        params.append(tipo)
    if compania:
        query += " AND mg.compania = ?"
        params.append(compania)
    
    query += " GROUP BY mg.equipo ORDER BY total_mp DESC"
    
    try:
        resultados = db.execute_query(query, params)
        return [dict(row) for row in resultados]
    except Exception as e:
        print(f"Error en obtener_metros_equipo: {e}")
        return []


def obtener_resumen_compania(desde, hasta, tipo=None):
    """Obtiene resumen de metros por compañía"""
    db = get_db()
    
    query = """
        SELECT 
            mg.compania,
            SUM(md.total_mp) as total_metros
        FROM metros_general mg
        JOIN metros_detalles md ON mg.id = md.registro_id
        WHERE mg.fecha BETWEEN ? AND ?
    """
    params = [desde, hasta]
    
    if tipo:
        query += " AND mg.tipo_perforacion = ?"
        params.append(tipo)
    
    query += " AND mg.compania IS NOT NULL AND mg.compania != ''"
    query += " GROUP BY mg.compania ORDER BY total_metros DESC"
    
    try:
        resultados = db.execute_query(query, params)
        return [dict(row) for row in resultados]
    except Exception as e:
        print(f"Error en obtener_resumen_compania: {e}")
        return []


def obtener_movimientos_mensuales(ano):
    """Obtiene movimientos por mes para un año"""
    db = get_db()
    
    query = """
        SELECT 
            mes,
            COUNT(*) as total,
            SUM(CASE WHEN movimiento = 'INGRESO' THEN 1 ELSE 0 END) as ingresos,
            SUM(CASE WHEN movimiento = 'SALIDA' THEN 1 ELSE 0 END) as salidas
        FROM movimiento_general
        WHERE ano = ?
        GROUP BY mes
        ORDER BY 
            CASE UPPER(mes)
                WHEN 'ENERO' THEN 1 WHEN 'FEBRERO' THEN 2 WHEN 'MARZO' THEN 3
                WHEN 'ABRIL' THEN 4 WHEN 'MAYO' THEN 5 WHEN 'JUNIO' THEN 6
                WHEN 'JULIO' THEN 7 WHEN 'AGOSTO' THEN 8 WHEN 'SEPTIEMBRE' THEN 9
                WHEN 'OCTUBRE' THEN 10 WHEN 'NOVIEMBRE' THEN 11 WHEN 'DICIEMBRE' THEN 12
                ELSE 13
            END
    """
    try:
        resultados = db.execute_query(query, (ano,))
        return [dict(row) for row in resultados]
    except Exception as e:
        print(f"Error en obtener_movimientos_mensuales: {e}")
        return []


def obtener_top_productos(limite=10):
    """Obtiene top productos con más stock"""
    db = get_db()
    
    query = """
        SELECT 
            UPPER(TRIM(codigo)) as codigo,
            UPPER(TRIM(descripcion)) as descripcion,
            SUM(cantidad) as stock
        FROM movimiento_detalles
        WHERE cantidad > 0
        GROUP BY UPPER(TRIM(codigo)), UPPER(TRIM(descripcion))
        ORDER BY stock DESC
        LIMIT ?
    """
    try:
        resultados = db.execute_query(query, (limite,))
        return [dict(row) for row in resultados]
    except Exception as e:
        print(f"Error en obtener_top_productos: {e}")
        return []


def obtener_rendimiento_aceros(ano, mes, compania=None):
    """Obtiene rendimiento de aceros por tipo y familia"""
    db = get_db()
    
    # Entregas
    if compania:
        entregas = db.execute_query("""
            SELECT 
                UPPER(TRIM(eq.tipo_perforacion)) as tipo_perforacion,
                UPPER(TRIM(dea.familia)) as familia,
                SUM(dea.cantidad * -1) AS total_entregado
            FROM movimiento_detalles dea
            JOIN movimiento_general ea ON dea.entrega_id = ea.id
            JOIN equipo eq ON ea.equipo = eq.equipo
            WHERE ea.ano = ? AND ea.mes = ? AND ea.compania = ?
            GROUP BY eq.tipo_perforacion, dea.familia
        """, (ano, mes, compania))
    else:
        entregas = db.execute_query("""
            SELECT 
                UPPER(TRIM(eq.tipo_perforacion)) as tipo_perforacion,
                UPPER(TRIM(dea.familia)) as familia,
                SUM(dea.cantidad * -1) AS total_entregado
            FROM movimiento_detalles dea
            JOIN movimiento_general ea ON dea.entrega_id = ea.id
            JOIN equipo eq ON ea.equipo = eq.equipo
            WHERE ea.ano = ? AND ea.mes = ?
            GROUP BY eq.tipo_perforacion, dea.familia
        """, (ano, mes))
    
    # Metros
    if compania:
        metros = db.execute_query("""
            SELECT
                UPPER(TRIM(eq.tipo_perforacion)) as tipo_perforacion,
                SUM(d.total_mp) AS total_mp,
                SUM(d.mp_produccion) AS mp_produccion,
                SUM(d.mp_rimado) AS mp_rimado
            FROM metros_general r
            JOIN metros_detalles d ON r.id = d.registro_id
            JOIN equipo eq ON r.equipo = eq.equipo
            WHERE r.ano = ? AND r.mes = ? AND r.compania = ?
            GROUP BY eq.tipo_perforacion
        """, (ano, mes, compania))
    else:
        metros = db.execute_query("""
            SELECT
                UPPER(TRIM(eq.tipo_perforacion)) as tipo_perforacion,
                SUM(d.total_mp) AS total_mp,
                SUM(d.mp_produccion) AS mp_produccion,
                SUM(d.mp_rimado) AS mp_rimado
            FROM metros_general r
            JOIN metros_detalles d ON r.id = d.registro_id
            JOIN equipo eq ON r.equipo = eq.equipo
            WHERE r.ano = ? AND r.mes = ?
            GROUP BY eq.tipo_perforacion
        """, (ano, mes))
    
    # Objetivos
    objetivos_raw = db.execute_query('SELECT "Tipo Perforacion", "Acero", objetivo FROM objetivos')
    objetivos_dict = {}
    for row in objetivos_raw:
        tp = row[0].strip().upper() if row[0] else None
        ac = row[1].strip().upper() if row[1] else None
        if tp and ac:
            objetivos_dict[(tp, ac)] = row[2] or 0
    
    # Procesar datos
    entregas_dict = {}
    for row in entregas:
        tp = row['tipo_perforacion']
        fam = row['familia']
        if tp and fam:
            key = (tp.upper(), fam.upper())
            entregas_dict[key] = entregas_dict.get(key, 0) + (row['total_entregado'] or 0)
    
    metros_dict = {}
    for row in metros:
        tp = row['tipo_perforacion']
        if tp:
            metros_dict[tp.upper()] = (
                row['total_mp'] or 0,
                row['mp_produccion'] or 0,
                row['mp_rimado'] or 0
            )
    
    resultados = {}
    
    for (tipo_perf, familia), objetivo in objetivos_dict.items():
        if not tipo_perf:
            continue
        
        total_entregado = entregas_dict.get((tipo_perf.upper(), familia.upper()), 0)
        total_mp, mp_prod, mp_rim = metros_dict.get(tipo_perf.upper(), (0, 0, 0))
        
        if familia.upper() == "BROCAS":
            metros_perforados = mp_prod
        elif familia.upper() == "RIMADORAS":
            metros_perforados = mp_rim
        else:
            metros_perforados = total_mp
        
        if total_entregado > 0 or metros_perforados > 0:
            rendimiento = round(metros_perforados / total_entregado, 2) if total_entregado > 0 else 0
            
            if objetivo and objetivo > 0:
                eficiencia = round(rendimiento / objetivo * 100, 2)
            else:
                eficiencia = 0
            
            if tipo_perf not in resultados:
                resultados[tipo_perf] = []
            
            resultados[tipo_perf].append({
                'familia': familia,
                'entregado': int(total_entregado),
                'metros': int(metros_perforados),
                'rendimiento': rendimiento,
                'objetivo': objetivo,
                'eficiencia': eficiencia
            })
    
    return resultados


def obtener_tipos_perforacion_opciones():
    """Obtiene tipos de perforación para filtros"""
    db = get_db()
    query = "SELECT DISTINCT tipo_perforacion FROM equipo WHERE tipo_perforacion IS NOT NULL AND tipo_perforacion != '' ORDER BY tipo_perforacion"
    try:
        resultados = db.execute_query(query)
        return [row[0] for row in resultados]
    except:
        return []


def obtener_companias_opciones():
    """Obtiene compañías para filtros"""
    db = get_db()
    query = "SELECT DISTINCT compania FROM equipo WHERE compania IS NOT NULL AND compania != '' ORDER BY compania"
    try:
        resultados = db.execute_query(query)
        return [row[0] for row in resultados]
    except:
        return []