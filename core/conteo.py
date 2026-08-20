from core.database import get_db
import pandas as pd
from datetime import datetime


def obtener_ubicaciones():
    """Obtiene todas las ubicaciones activas"""
    db = get_db()
    query = """
        SELECT nombre FROM ubicaciones 
        WHERE activo = 1 
        ORDER BY tipo, nombre
    """
    try:
        resultados = db.execute_query(query)
        return [row['nombre'] for row in resultados]
    except:
        return ["TALLER", "CAMIONETA", "T.AFILADO", "NV_120", "JIMENA", "RP-617", "NV_1370", "RP-616"]


def obtener_productos_con_stock():
    """
    Obtiene todos los productos que tienen stock en el sistema
    (desde movimiento_general y movimiento_detalles)
    """
    db = get_db()
    
    # Obtener productos con stock > 0
    query = """
        SELECT DISTINCT 
            md.codigo,
            MAX(md.descripcion) as descripcion
        FROM movimiento_detalles md
        JOIN movimiento_general mg ON md.entrega_id = mg.id
        WHERE md.codigo IS NOT NULL AND md.codigo != ''
        GROUP BY md.codigo
        HAVING SUM(md.cantidad) > 0
        ORDER BY md.codigo
    """
    
    try:
        resultados = db.execute_query(query)
        if not resultados:
            return pd.DataFrame(columns=['codigo', 'descripcion'])
        return pd.DataFrame([dict(row) for row in resultados])
    except Exception as e:
        print(f"Error en obtener_productos_con_stock: {e}")
        return pd.DataFrame(columns=['codigo', 'descripcion'])


def obtener_ultimo_conteo_fisico(fecha=None, ubicacion_filtro=None):
    """
    Obtiene el último conteo físico guardado para cada producto/ubicación
    Si fecha es None, obtiene el último conteo por producto/ubicación
    """
    db = get_db()
    
    if fecha:
        # Obtener conteo de una fecha específica
        query = """
            SELECT 
                codigo,
                descripcion,
                ubicacion,
                cantidad
            FROM stock_fisico
            WHERE fecha = ?
        """
        params = [fecha]
        
        if ubicacion_filtro and ubicacion_filtro != "TODAS":
            query += " AND ubicacion = ?"
            params.append(ubicacion_filtro)
        
        try:
            resultados = db.execute_query(query, params)
            if not resultados:
                return pd.DataFrame(columns=['codigo', 'descripcion', 'ubicacion', 'cantidad'])
            return pd.DataFrame([dict(row) for row in resultados])
        except:
            return pd.DataFrame(columns=['codigo', 'descripcion', 'ubicacion', 'cantidad'])
    
    else:
        # Obtener último conteo por producto/ubicación
        query = """
            SELECT 
                codigo,
                descripcion,
                ubicacion,
                cantidad,
                MAX(fecha) as ultima_fecha
            FROM stock_fisico
            WHERE 1=1
        """
        params = []
        
        if ubicacion_filtro and ubicacion_filtro != "TODAS":
            query += " AND ubicacion = ?"
            params.append(ubicacion_filtro)
        
        query += " GROUP BY codigo, ubicacion ORDER BY codigo"
        
        try:
            resultados = db.execute_query(query, params)
            if not resultados:
                return pd.DataFrame(columns=['codigo', 'descripcion', 'ubicacion', 'cantidad'])
            return pd.DataFrame([dict(row) for row in resultados])
        except:
            return pd.DataFrame(columns=['codigo', 'descripcion', 'ubicacion', 'cantidad'])


def guardar_conteo_fisico(df, fecha, usuario=None, observacion=None):
    """
    Guarda el conteo físico en la tabla stock_fisico
    df debe tener columnas: codigo, descripcion, ubicacion, cantidad
    """
    db = get_db()
    
    # Primero eliminar registros de la misma fecha y ubicación
    ubicaciones = df['ubicacion'].unique() if 'ubicacion' in df else []
    
    for ubicacion in ubicaciones:
        df_ubicacion = df[df['ubicacion'] == ubicacion]
        codigos = df_ubicacion['codigo'].tolist()
        
        if codigos:
            placeholders = ','.join(['?'] * len(codigos))
            db.execute_update(f"""
                DELETE FROM stock_fisico 
                WHERE fecha = ? AND ubicacion = ? AND codigo IN ({placeholders})
            """, (fecha, ubicacion, *codigos))
    
    # Insertar nuevos registros
    registros_guardados = 0
    for _, row in df.iterrows():
        codigo = row['codigo']
        descripcion = row.get('descripcion', '')
        ubicacion = row['ubicacion']
        cantidad = row.get('cantidad', 0)
        
        if cantidad > 0:  # Solo guardar si hay cantidad > 0
            try:
                db.execute_insert("""
                    INSERT INTO stock_fisico 
                    (codigo, descripcion, ubicacion, cantidad, fecha, usuario, observacion)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(codigo),
                    str(descripcion),
                    str(ubicacion),
                    float(cantidad),
                    fecha.strftime("%Y-%m-%d"),
                    usuario or 'admin',
                    observacion or ''
                ))
                registros_guardados += 1
            except Exception as e:
                print(f"Error guardando: {e}")
    
    return registros_guardados


def obtener_fechas_conteo(ubicacion=None):
    """Obtiene las fechas donde hay conteos guardados"""
    db = get_db()
    
    query = """
        SELECT DISTINCT fecha, COUNT(*) as total_registros
        FROM stock_fisico
        WHERE 1=1
    """
    params = []
    
    if ubicacion and ubicacion != "TODAS":
        query += " AND ubicacion = ?"
        params.append(ubicacion)
    
    query += " GROUP BY fecha ORDER BY fecha DESC"
    
    try:
        resultados = db.execute_query(query, params)
        return [dict(row) for row in resultados]
    except:
        return []


def obtener_conteo_por_fecha(fecha, ubicacion=None):
    """Obtiene todos los registros de un conteo específico"""
    db = get_db()
    
    query = """
        SELECT 
            codigo,
            descripcion,
            ubicacion,
            cantidad
        FROM stock_fisico
        WHERE fecha = ?
    """
    params = [fecha]
    
    if ubicacion and ubicacion != "TODAS":
        query += " AND ubicacion = ?"
        params.append(ubicacion)
    
    try:
        resultados = db.execute_query(query, params)
        return [dict(row) for row in resultados]
    except:
        return []