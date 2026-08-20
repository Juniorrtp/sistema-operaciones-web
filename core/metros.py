from core.database import get_db
from datetime import datetime


def obtener_metros(filtros, limit=50, offset=0):
    """Obtiene registros de metros con filtros y paginación"""
    db = get_db()
    
    query = """
        SELECT id, fecha, mes, ano, turno, operador, guardia,
               equipo, compania, tipo_perforacion, total_mp
        FROM metros_general WHERE 1=1
    """
    params = []
    
    if filtros.get('fecha_desde'):
        query += " AND fecha >= ?"
        params.append(filtros['fecha_desde'])
    if filtros.get('fecha_hasta'):
        query += " AND fecha <= ?"
        params.append(filtros['fecha_hasta'])
    
    for campo in ['ano', 'mes', 'operador', 'equipo', 'tipo_perforacion']:
        if filtros.get(campo) and len(filtros[campo]) > 0:
            placeholders = ','.join(['?'] * len(filtros[campo]))
            query += f" AND {campo} IN ({placeholders})"
            params.extend(filtros[campo])
    
    query += " ORDER BY fecha DESC, id DESC"
    query += f" LIMIT {limit} OFFSET {offset}"
    
    try:
        resultados = db.execute_query(query, params)
        return [dict(row) for row in resultados]
    except Exception as e:
        print(f"Error en obtener_metros: {e}")
        return []


def contar_metros(filtros):
    """Cuenta total de registros para paginación"""
    db = get_db()
    
    query = "SELECT COUNT(*) as total FROM metros_general WHERE 1=1"
    params = []
    
    if filtros.get('fecha_desde'):
        query += " AND fecha >= ?"
        params.append(filtros['fecha_desde'])
    if filtros.get('fecha_hasta'):
        query += " AND fecha <= ?"
        params.append(filtros['fecha_hasta'])
    
    for campo in ['ano', 'mes', 'operador', 'equipo', 'tipo_perforacion']:
        if filtros.get(campo) and len(filtros[campo]) > 0:
            placeholders = ','.join(['?'] * len(filtros[campo]))
            query += f" AND {campo} IN ({placeholders})"
            params.extend(filtros[campo])
    
    try:
        resultado = db.execute_query(query, params)
        return resultado[0][0] if resultado else 0
    except Exception as e:
        print(f"Error en contar_metros: {e}")
        return 0


def obtener_metro_por_id(metro_id):
    """Obtiene un registro de metros completo con sus detalles"""
    db = get_db()
    
    query_general = """
        SELECT id, fecha, mes, ano, turno, operador, guardia,
               equipo, compania, tipo_perforacion, ceco_tipo_perf
        FROM metros_general WHERE id = ?
    """
    general = db.execute_query(query_general, (metro_id,))
    
    if not general:
        return None
    
    query_detalles = """
        SELECT id, brazo, cod_ac, actividad, nivel_perf, labor_perf,
               tipo_roca, num_tal, lon_perf, rimados, 
               mp_produccion, mp_rimado, total_mp
        FROM metros_detalles WHERE registro_id = ?
    """
    detalles = db.execute_query(query_detalles, (metro_id,))
    
    return {
        'id': metro_id,
        'generales': dict(general[0]),
        'detalles': [dict(row) for row in detalles]
    }


def guardar_metro(datos_cabecera, datos_detalles, metro_id=None):
    """Guarda registro de metros (nuevo o edición)"""
    db = get_db()
    
    if metro_id:
        db.execute_update("""
            UPDATE metros_general SET
                fecha=?, mes=?, ano=?, turno=?, operador=?, guardia=?,
                equipo=?, compania=?, tipo_perforacion=?, ceco_tipo_perf=?
            WHERE id=?
        """, (
            datos_cabecera['fecha'], datos_cabecera['mes'], datos_cabecera['ano'],
            datos_cabecera['turno'], datos_cabecera['operador'], datos_cabecera['guardia'],
            datos_cabecera['equipo'], datos_cabecera['compania'], datos_cabecera['tipo_perforacion'],
            datos_cabecera.get('ceco_tipo_perf', ''), metro_id
        ))
        
        db.execute_update("DELETE FROM metros_detalles WHERE registro_id = ?", (metro_id,))
    else:
        metro_id = db.execute_insert("""
            INSERT INTO metros_general
            (fecha, mes, ano, turno, operador, guardia, equipo,
             compania, tipo_perforacion, ceco_tipo_perf)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datos_cabecera['fecha'], datos_cabecera['mes'], datos_cabecera['ano'],
            datos_cabecera['turno'], datos_cabecera['operador'], datos_cabecera['guardia'],
            datos_cabecera['equipo'], datos_cabecera['compania'], datos_cabecera['tipo_perforacion'],
            datos_cabecera.get('ceco_tipo_perf', '')
        ))
    
    for detalle in datos_detalles:
        db.execute_insert("""
            INSERT INTO metros_detalles (
                registro_id, brazo, cod_ac, actividad, nivel_perf, labor_perf,
                tipo_roca, num_tal, lon_perf, rimados,
                mp_produccion, mp_rimado, total_mp
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            metro_id,
            detalle.get('brazo', ''),
            detalle.get('cod_ac', ''),
            detalle.get('actividad', ''),
            detalle.get('nivel_perf', ''),
            detalle.get('labor_perf', ''),
            detalle.get('tipo_roca', ''),
            detalle.get('num_tal', 0),
            detalle.get('lon_perf', 0),
            detalle.get('rimados', 0),
            detalle.get('mp_produccion', 0),
            detalle.get('mp_rimado', 0),
            detalle.get('total_mp', 0)
        ))
    
    return metro_id


def eliminar_metro(metro_id):
    """Elimina registro de metros y sus detalles"""
    db = get_db()
    db.execute_update("DELETE FROM metros_detalles WHERE registro_id = ?", (metro_id,))
    db.execute_update("DELETE FROM metros_general WHERE id = ?", (metro_id,))


def obtener_operadores():
    """Obtiene lista de operadores"""
    db = get_db()
    query = "SELECT nombre, guardia FROM operador WHERE nombre IS NOT NULL AND nombre != '' ORDER BY nombre"
    resultados = db.execute_query(query)
    return [{'nombre': row[0], 'guardia': row[1] if row[1] else ''} for row in resultados]


def obtener_equipos_completos():
    """Obtiene lista de equipos con compañía y tipo"""
    db = get_db()
    query = "SELECT equipo, compania, tipo_perforacion, ceco_tipo FROM equipo WHERE equipo IS NOT NULL AND equipo != '' ORDER BY equipo"
    resultados = db.execute_query(query)
    return [{'equipo': row[0], 'compania': row[1] if row[1] else '', 
             'tipo': row[2] if row[2] else '', 'ceco': row[3] if row[3] else ''} for row in resultados]


def obtener_tipos_perforacion():
    """Obtiene tipos de perforación únicos"""
    db = get_db()
    query = "SELECT DISTINCT tipo_perforacion FROM metros_general WHERE tipo_perforacion IS NOT NULL AND tipo_perforacion != '' ORDER BY tipo_perforacion LIMIT 20"
    resultados = db.execute_query(query)
    return [str(row[0]) for row in resultados if row[0]]




def obtener_actividades():
    """Obtiene diccionario de actividades {codigo: descripcion}"""
    db = get_db()
    resultados = {}
    
    try:
        query = "SELECT codigo, descripcion FROM actividad WHERE codigo IS NOT NULL AND descripcion IS NOT NULL ORDER BY codigo"
        datos = db.execute_query(query)
        
        print(f"🔍 DEPURACIÓN: {len(datos) if datos else 0} actividades encontradas")
        
        if datos:
            for row in datos:
                codigo = str(row[0]).strip() if row[0] is not None else ''
                descripcion = str(row[1]).strip() if row[1] is not None else ''
                if codigo and descripcion:
                    resultados[codigo] = descripcion
                    print(f"  ✅ {codigo} -> {descripcion}")
            
            print(f"✅ Actividades cargadas: {len(resultados)}")
            return resultados
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return {}