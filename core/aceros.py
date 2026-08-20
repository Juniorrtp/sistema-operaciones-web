from core.database import get_db
from core.stock import StockCache

def buscar_aceros(texto_busqueda):
    """Busca aceros por código o descripción"""
    db = get_db()
    stock_cache = StockCache.get_instance()
    
    query = """
        SELECT codigo, descripcion, proveedor, marca, familia, subfamilia
        FROM aceros 
        WHERE UPPER(TRIM(codigo)) LIKE ? 
           OR UPPER(TRIM(descripcion)) LIKE ?
        ORDER BY descripcion
        LIMIT 50
    """
    patron = f"%{texto_busqueda.upper().strip()}%"
    resultados = db.execute_query(query, (patron, patron))
    
    aceros = []
    for row in resultados:
        codigo = row[0]
        stock = stock_cache.obtener_stock(codigo)
        aceros.append({
            'codigo': codigo,
            'descripcion': row[1],
            'proveedor': row[2] if row[2] else '',
            'marca': row[3] if row[3] else '',
            'familia': row[4] if row[4] else '',
            'subfamilia': row[5] if row[5] else '',
            'stock': stock
        })
    
    return aceros


def obtener_opciones(campo):
    """Obtiene opciones para filtros"""
    db = get_db()
    
    if campo == 'operador':
        query = "SELECT DISTINCT nombre FROM operador WHERE nombre IS NOT NULL AND nombre != '' ORDER BY nombre"
        resultados = db.execute_query(query)
        return [str(row[0]) for row in resultados if row[0]]
    
    elif campo == 'equipo':
        query = "SELECT DISTINCT equipo FROM equipo WHERE equipo IS NOT NULL AND equipo != '' ORDER BY equipo"
        resultados = db.execute_query(query)
        return [str(row[0]) for row in resultados if row[0]]
    
    elif campo == 'ano':
        query = "SELECT DISTINCT ano FROM movimiento_general WHERE ano IS NOT NULL ORDER BY ano DESC"
        resultados = db.execute_query(query)
        opciones = [str(row[0]) for row in resultados if row[0]]
        if not opciones:
            import datetime
            year = datetime.datetime.now().year
            opciones = [str(year), str(year-1), str(year-2)]
        return opciones
    
    elif campo == 'estado':
        query = "SELECT DISTINCT estado FROM movimiento_general WHERE estado IS NOT NULL AND estado != '' ORDER BY estado"
        resultados = db.execute_query(query)
        opciones = [str(row[0]) for row in resultados if row[0]]
        if "TRASLADO" not in opciones:
            opciones.append("TRASLADO")
            opciones.sort()
        return opciones
    
    else:
        query = f"""
            SELECT DISTINCT {campo} 
            FROM movimiento_general 
            WHERE {campo} IS NOT NULL AND {campo} != '' 
            ORDER BY {campo}
        """
        resultados = db.execute_query(query)
        return [str(row[0]) for row in resultados if row[0]]


def obtener_operadores_con_guardia():
    """Obtiene lista de operadores con su guardia"""
    db = get_db()
    query = "SELECT nombre, guardia FROM operador WHERE nombre IS NOT NULL AND nombre != '' ORDER BY nombre"
    resultados = db.execute_query(query)
    return [{'nombre': row[0], 'guardia': row[1] if row[1] else ''} for row in resultados]


def obtener_equipos_completos():
    """Obtiene lista de equipos con su compañía y tipo"""
    db = get_db()
    query = "SELECT equipo, compania, tipo_perforacion FROM equipo WHERE equipo IS NOT NULL AND equipo != '' ORDER BY equipo"
    resultados = db.execute_query(query)
    return [{'equipo': row[0], 'compania': row[1] if row[1] else '', 'tipo': row[2] if row[2] else ''} for row in resultados]