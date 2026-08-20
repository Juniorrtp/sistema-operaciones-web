from core.database import get_db
from core.stock import StockCache

def obtener_movimientos(filtros):
    """Obtiene movimientos con filtros"""
    db = get_db()
    
    # 🔥 Adaptado a tu tabla movimiento_general
    query = """
        SELECT id, fecha, mes, ano, turno, guia, movimiento,
               operador, equipo, compania, estado
        FROM movimiento_general WHERE 1=1
    """
    params = []
    
    # Fechas
    if filtros.get('fecha_desde'):
        query += " AND fecha >= ?"
        params.append(filtros['fecha_desde'])
    if filtros.get('fecha_hasta'):
        query += " AND fecha <= ?"
        params.append(filtros['fecha_hasta'])
    
    # Filtros múltiples
    for campo in ['ano', 'mes', 'movimiento', 'estado', 'operador', 'equipo']:
        if filtros.get(campo) and len(filtros[campo]) > 0:
            placeholders = ','.join(['?'] * len(filtros[campo]))
            query += f" AND {campo} IN ({placeholders})"
            params.extend(filtros[campo])
    
    # Guía
    if filtros.get('guia'):
        query += " AND guia LIKE ?"
        params.append(f"%{filtros['guia']}%")
    
    query += " ORDER BY fecha DESC, id DESC"
    
    try:
        resultados = db.execute_query(query, params)
        return [dict(row) for row in resultados]
    except Exception as e:
        print(f"Error en obtener_movimientos: {e}")
        return []



def obtener_movimiento_por_id(movimiento_id):
    """Obtiene movimiento completo con sus detalles"""
    db = get_db()
    
    # Cabecera
    query_general = """
        SELECT fecha, mes, ano, turno, semana, guia, movimiento, 
               operador, guardia, equipo, tipo_perforacion, compania, 
               observacion, estado
        FROM movimiento_general WHERE id = ?
    """
    general = db.execute_query(query_general, (movimiento_id,))
    
    if not general:
        return None
    
    # Detalles - 🔥 CORREGIDO: Mostrar cantidad en valor absoluto
    query_detalles = """
        SELECT id, brazo, codigo, descripcion, ABS(cantidad) as cantidad, razon
        FROM movimiento_detalles WHERE entrega_id = ?
    """
    detalles = db.execute_query(query_detalles, (movimiento_id,))
    
    return {
        'id': movimiento_id,
        'generales': dict(general[0]),
        'detalles': [dict(row) for row in detalles]
    }

def guardar_movimiento(datos_cabecera, datos_detalles, movimiento_id=None):
    """Guarda movimiento (nuevo o edición)"""
    db = get_db()
    
    # Determinar signo según movimiento
    movimiento = datos_cabecera['movimiento']
    for detalle in datos_detalles:
        cantidad = detalle['cantidad']
        if movimiento == "SALIDA":
            cantidad = -abs(cantidad)
        detalle['cantidad_final'] = cantidad
    
    if movimiento_id:
        # ACTUALIZAR
        db.execute_update("""
            UPDATE movimiento_general SET
                fecha=?, mes=?, ano=?, turno=?, semana=?, guia=?, movimiento=?,
                operador=?, guardia=?, equipo=?, tipo_perforacion=?, compania=?, estado=?
            WHERE id=?
        """, (
            datos_cabecera['fecha'], datos_cabecera['mes'], datos_cabecera['ano'],
            datos_cabecera['turno'], datos_cabecera.get('semana', ''), datos_cabecera['guia'],
            datos_cabecera['movimiento'], datos_cabecera.get('operador', ''),
            datos_cabecera.get('guardia', ''), datos_cabecera.get('equipo', ''),
            datos_cabecera.get('tipo_equipo', ''), datos_cabecera.get('compania', ''),
            datos_cabecera.get('estado', ''), movimiento_id
        ))
        
        # Eliminar detalles viejos
        db.execute_update("DELETE FROM movimiento_detalles WHERE entrega_id = ?", (movimiento_id,))
        
        # Insertar detalles nuevos
        for detalle in datos_detalles:
            db.execute_insert("""
                INSERT INTO movimiento_detalles
                (entrega_id, brazo, codigo, descripcion, cantidad, razon)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                movimiento_id,
                detalle.get('brazo', ''),
                detalle['codigo'],
                detalle['descripcion'],
                detalle['cantidad_final'],
                detalle.get('motivo', '')
            ))
    else:
        # NUEVO
        movimiento_id = db.execute_insert("""
            INSERT INTO movimiento_general
            (fecha, mes, ano, turno, semana, guia, movimiento,
             operador, guardia, equipo, tipo_perforacion, compania, estado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datos_cabecera['fecha'], datos_cabecera['mes'], datos_cabecera['ano'],
            datos_cabecera['turno'], datos_cabecera.get('semana', ''), datos_cabecera['guia'],
            datos_cabecera['movimiento'], datos_cabecera.get('operador', ''),
            datos_cabecera.get('guardia', ''), datos_cabecera.get('equipo', ''),
            datos_cabecera.get('tipo_equipo', ''), datos_cabecera.get('compania', ''),
            datos_cabecera.get('estado', '')
        ))
        
        for detalle in datos_detalles:
            db.execute_insert("""
                INSERT INTO movimiento_detalles
                (entrega_id, brazo, codigo, descripcion, cantidad, razon)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                movimiento_id,
                detalle.get('brazo', ''),
                detalle['codigo'],
                detalle['descripcion'],
                detalle['cantidad_final'],
                detalle.get('motivo', '')
            ))
    
    # Actualizar cache de stock
    StockCache.get_instance().actualizar_cache()
    
    return movimiento_id


def eliminar_movimiento(movimiento_id):
    """Elimina movimiento y sus detalles"""
    db = get_db()
    db.execute_update("DELETE FROM movimiento_detalles WHERE entrega_id = ?", (movimiento_id,))
    db.execute_update("DELETE FROM movimiento_general WHERE id = ?", (movimiento_id,))
    StockCache.get_instance().actualizar_cache()